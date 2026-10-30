using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Xml;
using Microsoft.Win32;

namespace CreditLedgerSetup
{
    public sealed class SetupError : Exception
    {
        public readonly string Code;
        public SetupError(string code) : base(code) { Code = code; }
    }
    public sealed class GameInstall
    {
        public string Root, Realm, Version;
        public string ModDirectory { get { return Path.Combine(Root, "mods", Version); } }
        public override string ToString() { return "World of Tanks " + Realm + "  ·  " + Version; }
    }
    public sealed class InstallResult
    {
        public string Target, Backup;
        public int PreviousFiles;
    }
    public sealed class InstallerEngine
    {
        public const string ModId = "local.credit_ledger";
        public const string FileName = ModId + ".wotmod";
        public const string Release = "0.22.14";
        public const string PayloadHash = "2a3659b911679edc54aa59336c9761f7a9a5ac825d435464e9f01bd9a2c8bc17";
        internal Func<bool> IsRunning = GameRunning;
        internal Action<string> BeforeCommit = null;
        readonly string backupRoot;

        public InstallerEngine() : this(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CreditLedger", "Installer", "backups")) { }
        internal InstallerEngine(string storage) { backupRoot = Path.GetFullPath(storage); }

        public static bool GameRunning()
        {
            Process[] processes = Process.GetProcessesByName("WorldOfTanks");
            bool running = processes.Length > 0;
            foreach (Process p in processes) p.Dispose();
            return running;
        }
        public static void SafePath(string path)
        {
            string full = Path.GetFullPath(path);
            for (string p = full; !String.IsNullOrEmpty(p); p = Path.GetDirectoryName(p))
                if ((Directory.Exists(p) || File.Exists(p)) && (File.GetAttributes(p) & FileAttributes.ReparsePoint) != 0)
                    throw new SetupError("linked_path");
        }
        static XmlDocument ReadXml(Stream stream)
        {
            var settings = new XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null, MaxCharactersInDocument = 4 * 1024 * 1024 };
            var doc = new XmlDocument { XmlResolver = null };
            using (var reader = XmlReader.Create(stream, settings)) doc.Load(reader);
            return doc;
        }
        static XmlDocument ReadXml(string path) { using (var s = File.OpenRead(path)) return ReadXml(s); }
        static string Value(XmlDocument doc, string xpath)
        {
            XmlNode node = doc.SelectSingleNode(xpath);
            return node == null ? "" : node.InnerText.Trim();
        }
        public static GameInstall Inspect(string folder)
        {
            if (String.IsNullOrWhiteSpace(folder) || !Path.IsPathRooted(folder)) throw new SetupError("not_game");
            string root = Path.GetFullPath(folder).TrimEnd(Path.DirectorySeparatorChar);
            if (String.Equals(root, Path.GetPathRoot(Path.GetFullPath(folder)).TrimEnd(Path.DirectorySeparatorChar), StringComparison.OrdinalIgnoreCase)) throw new SetupError("not_game");
            SafePath(root);
            try
            {
                if (!File.Exists(Path.Combine(root, "win64", "WorldOfTanks.exe")) && !File.Exists(Path.Combine(root, "win32", "WorldOfTanks.exe")))
                    throw new SetupError("not_game");
                SafePath(Path.Combine(root, "version.xml"));
                SafePath(Path.Combine(root, "paths.xml"));
                SafePath(Path.Combine(root, "game_info.xml"));
                var info = ReadXml(Path.Combine(root, "game_info.xml"));
                var version = ReadXml(Path.Combine(root, "version.xml"));
                string realm = Value(version, "/version.xml/meta/realm").ToUpperInvariant();
                if (!new[] { "NA", "EU", "ASIA" }.Contains(realm) || Value(info, "/protocol/game/id") != "WOT." + realm + ".PRODUCTION")
                    throw new SetupError("unsupported_realm");
                Match match = Regex.Match(Value(version, "/version.xml/version"), @"^v\.(\d+\.\d+\.\d+\.\d+)(?:\s|$)");
                if (!match.Success || !new[] { "2.4.1.0", "2.4.1.1" }.Contains(match.Groups[1].Value))
                    throw new SetupError("unsupported_version");
                string client = match.Groups[1].Value;
                var paths = ReadXml(Path.Combine(root, "paths.xml"));
                bool active = false;
                foreach (XmlNode node in paths.SelectNodes("/root/Paths/Path[@mask='*.wotmod']"))
                {
                    string relative = node.InnerText.Trim().Replace('\\', '/');
                    if (relative == "./mods/" + client || relative == "mods/" + client) active = true;
                }
                if (!active) throw new SetupError("paths_mismatch");
                var game = new GameInstall { Root = root, Realm = realm, Version = client };
                SafePath(game.ModDirectory);
                return game;
            }
            catch (SetupError) { throw; }
            catch (IOException) { throw new SetupError("not_game"); }
            catch (XmlException) { throw new SetupError("not_game"); }
            catch (UnauthorizedAccessException) { throw new SetupError("not_game"); }
        }
        public static List<GameInstall> Discover()
        {
            var candidates = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (RegistryHive hive in new[] { RegistryHive.CurrentUser, RegistryHive.LocalMachine })
                foreach (RegistryView view in new[] { RegistryView.Registry32, RegistryView.Registry64 })
                {
                    try
                    {
                        using (var key = RegistryKey.OpenBaseKey(hive, view))
                        using (var uninstall = key.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall"))
                        {
                            if (uninstall == null) continue;
                            foreach (string name in uninstall.GetSubKeyNames())
                                using (var entry = uninstall.OpenSubKey(name))
                                {
                                    if (entry == null || !Convert.ToString(entry.GetValue("DisplayName")).StartsWith("World of Tanks", StringComparison.OrdinalIgnoreCase)) continue;
                                    string location = Convert.ToString(entry.GetValue("InstallLocation"));
                                    if (!String.IsNullOrWhiteSpace(location)) candidates.Add(location.Trim('"'));
                                }
                        }
                    }
                    catch (System.Security.SecurityException) { }
                    catch (UnauthorizedAccessException) { }
                    catch (IOException) { }
                }
            // Bounded conventional paths only: never scan whole drives or player data.
            foreach (DriveInfo drive in DriveInfo.GetDrives())
                if (drive.DriveType == DriveType.Fixed && drive.IsReady)
                    foreach (string name in new[] { "World_of_Tanks", "World_of_Tanks_NA", "World_of_Tanks_EU", "World_of_Tanks_ASIA" })
                        candidates.Add(Path.Combine(drive.RootDirectory.FullName, "Games", name));
            var found = new List<GameInstall>();
            foreach (string candidate in candidates.OrderBy(x => x))
                try { found.Add(Inspect(candidate)); } catch (Exception) { }
            return found.GroupBy(x => x.Root, StringComparer.OrdinalIgnoreCase).Select(x => x.First()).ToList();
        }
        public static string Hash(byte[] data)
        { using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(data)).Replace("-", "").ToLowerInvariant(); }
        static string HashFile(string path) { return Hash(File.ReadAllBytes(path)); }
        public static byte[] Payload()
        {
            using (var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("CreditLedger.Payload"))
            using (var memory = new MemoryStream())
            {
                if (stream == null) throw new SetupError("payload");
                stream.CopyTo(memory);
                byte[] data = memory.ToArray();
                if (Hash(data) != PayloadHash) throw new SetupError("payload");
                return data;
            }
        }
        static string OwnVersion(string path)
        {
            try
            {
                using (var zip = ZipFile.OpenRead(path))
                {
                    var entry = zip.GetEntry("meta.xml");
                    if (entry == null || entry.Length > 65536) return null;
                    using (var stream = entry.Open())
                    {
                        var doc = ReadXml(stream);
                        return Value(doc, "/root/id") == ModId ? Value(doc, "/root/version") : null;
                    }
                }
            }
            catch (InvalidDataException) { return null; }
            catch (XmlException) { return null; }
        }
        static IEnumerable<string> ModFiles(string directory, int depth)
        {
            if (!Directory.Exists(directory)) yield break;
            if (depth > 16) throw new SetupError("deep_folder");
            SafePath(directory);
            // Earlier updaters could leave disabled packages alongside live ones.
            // Extension only selects candidates: OwnVersion must still prove ownership.
            foreach (string file in Directory.GetFiles(directory, "*.wotmod*"))
                if (file.EndsWith(".wotmod", StringComparison.OrdinalIgnoreCase) || file.EndsWith(".wotmod.disabled", StringComparison.OrdinalIgnoreCase))
                { SafePath(file); yield return file; }
            foreach (string sub in Directory.GetDirectories(directory))
                foreach (string file in ModFiles(sub, depth + 1)) yield return file;
        }
        static List<string> OlderClientDirectories(GameInstall game)
        {
            string modRoot = Path.Combine(game.Root, "mods");
            SafePath(modRoot);
            var older = new List<string>();
            if (!Directory.Exists(modRoot)) return older;
            var active = new Version(game.Version);
            foreach (string directory in Directory.GetDirectories(modRoot))
            {
                string name = Path.GetFileName(directory);
                Version candidate;
                if (!Regex.IsMatch(name, @"^\d+\.\d+\.\d+\.\d+$") || !Version.TryParse(name, out candidate) || candidate >= active) continue;
                SafePath(directory);
                older.Add(directory);
            }
            return older;
        }
        static bool Inside(string path, string directory)
        {
            return Path.GetFullPath(path).StartsWith(Path.GetFullPath(directory).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase);
        }
        static void PruneOldDirectories(List<string> older, IEnumerable<string> removedFiles, List<string> removedDirectories)
        {
            var candidates = new HashSet<string>(older, StringComparer.OrdinalIgnoreCase);
            foreach (string root in older)
                foreach (string file in removedFiles.Where(file => Inside(file, root)))
                    for (string parent = Path.GetDirectoryName(file); String.Equals(parent, root, StringComparison.OrdinalIgnoreCase) || Inside(parent, root); parent = Path.GetDirectoryName(parent))
                    {
                        candidates.Add(parent);
                        if (String.Equals(parent, root, StringComparison.OrdinalIgnoreCase)) break;
                    }
            foreach (string directory in candidates.OrderByDescending(path => path.Length))
            {
                if (!older.Any(root => String.Equals(directory, root, StringComparison.OrdinalIgnoreCase) || Inside(directory, root))) throw new SetupError("changed_files");
                SafePath(directory);
                if (!Directory.Exists(directory) || Directory.GetFileSystemEntries(directory).Length != 0) continue;
                try { Directory.Delete(directory, false); removedDirectories.Add(directory); }
                catch (IOException)
                {
                    // A newly arrived unrelated file must keep its folder intact.
                    if (!Directory.Exists(directory) || Directory.GetFileSystemEntries(directory).Length != 0) continue;
                    throw;
                }
            }
        }
        public InstallResult Apply(string folder, bool remove, Action<int> progress)
        {
            using (var mutex = new Mutex(false, @"Local\CreditLedgerInstaller"))
            {
                bool acquired;
                try { acquired = mutex.WaitOne(0); } catch (AbandonedMutexException) { acquired = true; }
                if (!acquired) throw new SetupError("installer_busy");
                try { return ApplyLocked(folder, remove, progress); } finally { mutex.ReleaseMutex(); }
            }
        }
        InstallResult ApplyLocked(string folder, bool remove, Action<int> progress)
        {
            progress(0);
            if (IsRunning()) throw new SetupError("game_running");
            var game = Inspect(folder);
            byte[] payload = Payload();
            string target = Path.Combine(game.ModDirectory, FileName);
            SafePath(target);
            progress(10);
            // Only installation/update also retires this mod from older client
            // folders in the selected game. Future versions and configs stay outside.
            var olderDirectories = remove ? new List<string>() : OlderClientDirectories(game);
            var owned = new List<string>();
            foreach (string file in new[] { game.ModDirectory }.Concat(olderDirectories).SelectMany(directory => ModFiles(directory, 0)))
            {
                string version = OwnVersion(file);
                if (version == null)
                {
                    if (String.Equals(file, target, StringComparison.OrdinalIgnoreCase)) throw new SetupError("foreign_file");
                    continue;
                }
                Version installed;
                if (!remove && (!Version.TryParse(version.Replace("-beta", ""), out installed) || installed > new Version(Release)))
                    throw new SetupError("newer_version");
                owned.Add(file);
            }
            progress(20);
            if (remove && owned.Count == 0) throw new SetupError("not_installed");
            if (olderDirectories.Count == 0 && owned.Count == 1 && String.Equals(owned[0], target, StringComparison.OrdinalIgnoreCase) && !remove && HashFile(target) == PayloadHash)
            {
                progress(100);
                return new InstallResult { Target = target, PreviousFiles = 1 };
            }
            SafePath(backupRoot);
            string backup = Path.Combine(backupRoot, Hash(Encoding.UTF8.GetBytes(game.Root.ToUpperInvariant())).Substring(0, 16), DateTime.UtcNow.ToString("yyyyMMdd-HHmmss") + "-" + Guid.NewGuid().ToString("N"));
            SafePath(backup);
            Directory.CreateDirectory(backup);
            var originals = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (string file in owned)
            {
                string saved = Path.Combine(backup, originals.Count.ToString("D4") + ".wotmod");
                File.Copy(file, saved, false);
                if (HashFile(file) != HashFile(saved)) throw new SetupError("backup_failed");
                originals.Add(file, saved);
            }
            File.WriteAllLines(Path.Combine(backup, "restore-map.txt"), originals.Select(x => x.Value + " -> " + x.Key), Encoding.UTF8);
            progress(35);
            string temp = null;
            var changed = new List<string>();
            var removedDirectories = new List<string>();
            try
            {
                if (!remove)
                {
                    Directory.CreateDirectory(game.ModDirectory);
                    temp = Path.Combine(game.ModDirectory, ".credit-ledger-" + Guid.NewGuid().ToString("N") + ".tmp");
                    using (var stream = new FileStream(temp, FileMode.CreateNew, FileAccess.Write, FileShare.None)) { stream.Write(payload, 0, payload.Length); stream.Flush(true); }
                    if (HashFile(temp) != PayloadHash) throw new SetupError("payload");
                }
                progress(55);
                if (BeforeCommit != null) BeforeCommit("staged");
                if (IsRunning()) throw new SetupError("game_running");
                SafePath(target);
                foreach (var original in originals)
                    if (HashFile(original.Key) != HashFile(original.Value)) throw new SetupError("changed_files");
                if (File.Exists(target) && !originals.ContainsKey(target)) throw new SetupError("changed_files");
                if (!remove)
                {
                    if (File.Exists(target)) File.Replace(temp, target, null); else File.Move(temp, target);
                    changed.Add(target);
                    temp = null;
                    if (HashFile(target) != PayloadHash) throw new SetupError("payload");
                }
                progress(75);
                if (BeforeCommit != null) BeforeCommit("cleanup");
                foreach (string file in owned)
                {
                    if (!remove && String.Equals(file, target, StringComparison.OrdinalIgnoreCase)) continue;
                    SafePath(file);
                    if (HashFile(file) != HashFile(originals[file])) throw new SetupError("changed_files");
                    File.Delete(file);
                    changed.Add(file);
                }
                progress(90);
                // Verify the active client folder after cleanup, including disabled
                // historical copies. Never report success with a duplicate remaining.
                var remaining = ModFiles(game.ModDirectory, 0).Where(file => OwnVersion(file) != null).ToList();
                if (remove ? remaining.Count != 0 : remaining.Count != 1 ||
                    !String.Equals(remaining[0], target, StringComparison.OrdinalIgnoreCase) || HashFile(target) != PayloadHash)
                    throw new SetupError("changed_files");
                if (olderDirectories.Any(directory => ModFiles(directory, 0).Any(file => OwnVersion(file) != null))) throw new SetupError("changed_files");
                PruneOldDirectories(olderDirectories, changed, removedDirectories);
                progress(100);
                return new InstallResult { Target = target, Backup = owned.Count > 0 ? backup : null, PreviousFiles = owned.Count };
            }
            catch (Exception original)
            {
                bool restored = true;
                foreach (string directory in removedDirectories.OrderBy(path => path.Length))
                    try { SafePath(directory); Directory.CreateDirectory(directory); }
                    catch { restored = false; }
                foreach (string file in changed.AsEnumerable().Reverse())
                    try
                    {
                        SafePath(file);
                        if (originals.ContainsKey(file))
                        {
                            Directory.CreateDirectory(Path.GetDirectoryName(file));
                            File.Copy(originals[file], file, true);
                        }
                        else if (File.Exists(file)) File.Delete(file);
                    }
                    catch { restored = false; }
                if (!restored) throw new IOException("rollback_failed: " + backup, original);
                throw;
            }
            finally { if (temp != null && File.Exists(temp)) File.Delete(temp); }
        }
    }
}
