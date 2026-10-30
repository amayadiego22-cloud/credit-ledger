using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using CreditLedgerSetup;

internal static class InstallerTests
{
    static string suite;
    static int passed;
    static string Fixture(string realm, string version, string name)
    {
        string root = Path.Combine(suite, name + "-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path.Combine(root, "win64"));
        File.WriteAllBytes(Path.Combine(root, "win64", "WorldOfTanks.exe"), new byte[] { 0 });
        File.WriteAllText(Path.Combine(root, "version.xml"), "<version.xml><version> v." + version + " #1 </version><meta><realm>" + realm + "</realm></meta></version.xml>");
        File.WriteAllText(Path.Combine(root, "game_info.xml"), "<protocol><game><id>WOT." + realm + ".PRODUCTION</id></game></protocol>");
        File.WriteAllText(Path.Combine(root, "paths.xml"), "<root><Paths><Path mask='*.wotmod'>./mods/" + version + "</Path></Paths></root>");
        Directory.CreateDirectory(Path.Combine(root, "mods", version));
        return root;
    }
    static string Target(string root) { return Path.Combine(InstallerEngine.Inspect(root).ModDirectory, InstallerEngine.FileName); }
    static void Package(string path, string id, string version)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        using (var zip = ZipFile.Open(path, ZipArchiveMode.Create))
        using (var writer = new StreamWriter(zip.CreateEntry("meta.xml").Open()))
            writer.Write("<root><id>" + id + "</id><version>" + version + "</version></root>");
    }
    static void Assert(bool condition, string label) { if (!condition) throw new Exception(label); }
    static void Reject(Action operation, string code)
    {
        try { operation(); } catch (SetupError e) { Assert(e.Code == code, "expected " + code + ", got " + e.Code); return; }
        throw new Exception("did not reject " + code);
    }
    static void Test(string name, Action test) { test(); passed++; Console.WriteLine("PASS " + name); }
    static InstallerEngine Engine() { return new InstallerEngine(Path.Combine(suite, "backups")) { IsRunning = () => false }; }
    static void AssertProgress(List<int> values, bool complete)
    {
        Assert(values.Count > 0 && values[0] == 0, "progress begins at zero");
        Assert(values.All(p => p >= 0 && p <= 100), "progress stays within bounds");
        for (int i = 1; i < values.Count; i++) Assert(values[i] > values[i - 1], "progress advances monotonically");
        Assert(complete ? values.Last() == 100 : !values.Contains(100), "completion matches operation result");
    }
    static void Main(string[] args)
    {
        suite = Path.GetFullPath(args[0]); Directory.CreateDirectory(suite);
        Test("embedded payload SHA-256", () => Assert(InstallerEngine.Hash(InstallerEngine.Payload()) == InstallerEngine.PayloadHash, "hash"));
        foreach (string realmValue in new[] { "NA", "EU", "ASIA" })
            foreach (string versionValue in new[] { "2.4.1.0", "2.4.1.1" })
            {
                string realm = realmValue, version = versionValue;
                Test("install " + realm + " " + version + " Unicode path", () =>
                {
                    string root = Fixture(realm, version, "Prueba créditos 日本語");
                    Engine().Apply(root, false, p => { });
                    Assert(InstallerEngine.Hash(File.ReadAllBytes(Target(root))) == InstallerEngine.PayloadHash, "installed");
                    Assert(Directory.GetDirectories(Path.Combine(root, "mods")).Length == 1, "only active version");
                });
            }
        Test("reject arbitrary folder", () => Reject(() => InstallerEngine.Inspect(suite), "not_game"));
        Test("reject relative folder", () => Reject(() => InstallerEngine.Inspect("relative"), "not_game"));
        Test("reject Lesta", () => Reject(() => InstallerEngine.Inspect(Fixture("RU", "2.4.1.1", "lesta")), "unsupported_realm"));
        Test("reject Common Test", () => Reject(() => InstallerEngine.Inspect(Fixture("CT", "2.4.1.1", "test")), "unsupported_realm"));
        Test("reject mismatching production ID", () =>
        {
            string root = Fixture("EU", "2.4.1.1", "id"); File.WriteAllText(Path.Combine(root, "game_info.xml"), "<protocol><game><id>WOT.NA.PRODUCTION</id></game></protocol>");
            Reject(() => InstallerEngine.Inspect(root), "unsupported_realm");
        });
        Test("reject future client version", () => Reject(() => InstallerEngine.Inspect(Fixture("NA", "2.5.0.0", "future")), "unsupported_version"));
        Test("reject active paths mismatch", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "paths"); File.WriteAllText(Path.Combine(root, "paths.xml"), "<root><Paths><Path mask='*.wotmod'>../outside</Path></Paths></root>");
            Reject(() => InstallerEngine.Inspect(root), "paths_mismatch");
        });
        Test("reject XML external entities", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "xxe"); File.WriteAllText(Path.Combine(root, "version.xml"), "<!DOCTYPE root [<!ENTITY x SYSTEM 'file:///C:/nonexistent'>]><version.xml>&x;</version.xml>");
            Reject(() => InstallerEngine.Inspect(root), "not_game");
        });
        Test("game running blocks all writes", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "running"); var engine = Engine(); engine.IsRunning = () => true;
            Reject(() => engine.Apply(root, false, p => { }), "game_running"); Assert(!File.Exists(Target(root)), "no write");
        });
        Test("game starts after staging preserves original", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "starts"); Package(Target(root), InstallerEngine.ModId, "0.22.6"); byte[] before = File.ReadAllBytes(Target(root));
            var engine = Engine(); engine.BeforeCommit = stage => { if (stage == "staged") engine.IsRunning = () => true; };
            Reject(() => engine.Apply(root, false, p => { }), "game_running"); Assert(before.SequenceEqual(File.ReadAllBytes(Target(root))), "preserved");
            Assert(!Directory.GetFiles(Path.GetDirectoryName(Target(root)), "*.tmp").Any(), "temp cleaned");
        });
        Test("foreign file at target is never replaced", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "foreign"); File.WriteAllText(Target(root), "unrelated");
            Reject(() => Engine().Apply(root, false, p => { }), "foreign_file"); Assert(File.ReadAllText(Target(root)) == "unrelated", "foreign preserved");
        });
        Test("newer mod blocks downgrade", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "newer"); Package(Target(root), InstallerEngine.ModId, "0.23.0");
            Reject(() => Engine().Apply(root, false, p => { }), "newer_version");
        });
        Test("update removes only identified duplicates and backs them up", () =>
        {
            string root = Fixture("EU", "2.4.1.1", "duplicates"); string dir = Path.GetDirectoryName(Target(root));
            string old = Path.Combine(dir, "old", "credit_ledger.0.20.wotmod"), other = Path.Combine(dir, "someone_else.wotmod");
            Package(Target(root), InstallerEngine.ModId, "0.22.6"); Package(old, InstallerEngine.ModId, "0.20.0"); Package(other, "another.mod", "1.0");
            byte[] otherBefore = File.ReadAllBytes(other); var result = Engine().Apply(root, false, p => { });
            Assert(!File.Exists(old) && otherBefore.SequenceEqual(File.ReadAllBytes(other)), "duplicates only");
            Assert(result.PreviousFiles == 2 && Directory.GetFiles(result.Backup, "*.wotmod").Length == 2, "backups");
        });
        Test("repeat install is idempotent", () =>
        {
            string root = Fixture("ASIA", "2.4.1.1", "twice"); var engine = Engine(); engine.Apply(root, false, p => { });
            DateTime before = File.GetLastWriteTimeUtc(Target(root)); var result = engine.Apply(root, false, p => { });
            Assert(File.GetLastWriteTimeUtc(Target(root)) == before && result.Backup == null, "idempotent");
        });
        foreach (string activeValue in new[] { "2.4.1.0", "2.4.1.1" })
        {
            string active = activeValue;
            Test("one current copy, older clients cleaned, future clients kept for " + active, () =>
            {
                string root = Fixture("EU", active, "active cleanup " + active);
                string dir = Path.GetDirectoryName(Target(root));
                File.WriteAllBytes(Target(root), InstallerEngine.Payload());
                string old = Path.Combine(dir, "previous", "renamed old package.wotmod");
                string same = Path.Combine(dir, "copy of current.wotmod");
                string disabled = Path.Combine(dir, "local.credit_ledger.0.3.0-beta.wotmod.disabled");
                Package(old, InstallerEngine.ModId, "0.17.0");
                File.WriteAllBytes(same, InstallerEngine.Payload());
                Package(disabled, InstallerEngine.ModId, "0.3.0");
                string foreign = Path.Combine(dir, "credit_ledger_unrelated.wotmod.disabled");
                Package(foreign, "another.mod", "1.0");
                string inactiveVersion = active == "2.4.1.0" ? "2.4.1.1" : "2.4.1.0";
                string inactive = Path.Combine(root, "mods", inactiveVersion, "old credit ledger.wotmod");
                string inactiveDisabled = inactive + ".disabled";
                Package(inactive, InstallerEngine.ModId, "0.22.6");
                Package(inactiveDisabled, InstallerEngine.ModId, "0.3.0");
                bool isOlder = new Version(inactiveVersion) < new Version(active);
                var protectedFiles = (isOlder ? new[] { foreign } : new[] { foreign, inactive, inactiveDisabled }).ToDictionary(path => path, path => File.ReadAllBytes(path));
                var values = new List<int>();
                var result = Engine().Apply(root, false, p => values.Add(p));
                Assert(!File.Exists(old) && !File.Exists(same) && !File.Exists(disabled), "old, identical and disabled copies removed");
                Assert(InstallerEngine.Hash(File.ReadAllBytes(Target(root))) == InstallerEngine.PayloadHash, "current payload is the remaining copy");
                int expectedBackups = isOlder ? 6 : 4;
                Assert(result.PreviousFiles == expectedBackups && Directory.GetFiles(result.Backup, "*.wotmod").Length == expectedBackups, "all previous copies backed up outside game");
                foreach (var preserved in protectedFiles) Assert(preserved.Value.SequenceEqual(File.ReadAllBytes(preserved.Key)), "future client and foreign package preserved");
                if (isOlder) Assert(!Directory.Exists(Path.GetDirectoryName(inactive)), "empty older version folder removed");
                Assert(Directory.GetFiles(dir, "*.wotmod*", SearchOption.AllDirectories).Length == 2, "one owned copy plus preserved foreign package");
                AssertProgress(values, true);
            });
        }
        Test("unexpected duplicate during cleanup prevents success and restores originals", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "new duplicate");
            Package(Target(root), InstallerEngine.ModId, "0.22.6");
            byte[] before = File.ReadAllBytes(Target(root));
            string external = Path.Combine(Path.GetDirectoryName(Target(root)), "external copy.wotmod.disabled");
            var engine = Engine(); var values = new List<int>();
            engine.BeforeCommit = stage => { if (stage == "cleanup") Package(external, InstallerEngine.ModId, "0.22.5"); };
            Reject(() => engine.Apply(root, false, p => values.Add(p)), "changed_files");
            Assert(!values.Contains(100), "duplicate cannot report success");
            Assert(before.SequenceEqual(File.ReadAllBytes(Target(root))), "original restored");
            Assert(File.Exists(external), "concurrent file not removed without prior backup");
        });
        Test("already current installation still removes an empty older client folder", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "empty old client");
            File.WriteAllBytes(Target(root), InstallerEngine.Payload());
            string oldDirectory = Path.Combine(root, "mods", "2.4.1.0"); Directory.CreateDirectory(oldDirectory);
            Engine().Apply(root, false, p => { });
            Assert(!Directory.Exists(oldDirectory), "old empty folder removed despite current payload");
            Assert(Directory.Exists(Path.GetDirectoryName(Target(root))) && InstallerEngine.Hash(File.ReadAllBytes(Target(root))) == InstallerEngine.PayloadHash, "active client retained");
        });
        Test("old nested copies removed while foreign files, configs and future clients stay", () =>
        {
            string root = Fixture("ASIA", "2.4.1.1", "mixed older clients");
            string mixedRoot = Path.Combine(root, "mods", "2.4.1.0");
            string mixedOwn = Path.Combine(mixedRoot, "nested", "old.wotmod.disabled");
            string foreign = Path.Combine(mixedRoot, "other.wotmod");
            string readme = Path.Combine(mixedRoot, "notes.txt");
            Package(mixedOwn, InstallerEngine.ModId, "0.20.0");
            Package(foreign, "another.mod", "1.0"); File.WriteAllText(readme, "keep this file");
            string oldRoot = Path.Combine(root, "mods", "1.9.0.0");
            string oldOwn = Path.Combine(oldRoot, "deep", "nested", "renamed.wotmod");
            Package(oldOwn, InstallerEngine.ModId, "0.17.0");
            string future = Path.Combine(root, "mods", "2.4.1.2", "next.wotmod");
            string config = Path.Combine(root, "mods", "configs", "credit_ledger", "saved.wotmod");
            string nonVersion = Path.Combine(root, "mods", "2.4.1.0-backup", "saved.wotmod");
            foreach (string path in new[] { future, config, nonVersion }) Package(path, InstallerEngine.ModId, "0.22.6");
            var preserved = new[] { foreign, readme, future, config, nonVersion }.ToDictionary(path => path, path => File.ReadAllBytes(path));
            var result = Engine().Apply(root, false, p => { });
            Assert(!File.Exists(mixedOwn) && !Directory.Exists(Path.GetDirectoryName(mixedOwn)), "empty owned subfolder removed");
            Assert(Directory.Exists(mixedRoot) && !Directory.Exists(oldRoot), "mixed old root retained, fully empty old tree removed");
            foreach (var item in preserved) Assert(item.Value.SequenceEqual(File.ReadAllBytes(item.Key)), "unrelated content preserved");
            string map = File.ReadAllText(Path.Combine(result.Backup, "restore-map.txt"));
            Assert(result.PreviousFiles == 2 && map.Contains(mixedOwn) && map.Contains(oldOwn), "old client files included in backup map");
        });
        Test("failure after removing old folders restores their tree and files", () =>
        {
            string root = Fixture("EU", "2.4.1.1", "old folder rollback");
            string oldRoot = Path.Combine(root, "mods", "2.4.1.0");
            string oldOwn = Path.Combine(oldRoot, "deep", "previous.wotmod");
            string disabled = Path.Combine(oldRoot, "previous.wotmod.disabled");
            string emptyRoot = Path.Combine(root, "mods", "2.3.0.0"); Directory.CreateDirectory(emptyRoot);
            Package(Target(root), InstallerEngine.ModId, "0.22.6");
            Package(oldOwn, InstallerEngine.ModId, "0.20.0"); Package(disabled, InstallerEngine.ModId, "0.17.0");
            var originals = new[] { Target(root), oldOwn, disabled }.ToDictionary(path => path, path => File.ReadAllBytes(path));
            bool rejected = false;
            try { Engine().Apply(root, false, p => { if (p == 100) { Assert(!Directory.Exists(oldRoot) && !Directory.Exists(emptyRoot), "folders removed before completion"); throw new IOException("synthetic final failure"); } }); }
            catch (IOException) { rejected = true; }
            Assert(rejected && Directory.Exists(emptyRoot), "failure restores even an originally empty folder");
            foreach (var item in originals) Assert(item.Value.SequenceEqual(File.ReadAllBytes(item.Key)), "all files restored with their parent folders");
        });
        Test("concurrent change in old client file is preserved", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "old client concurrent");
            string old = Path.Combine(root, "mods", "2.4.1.0", "old.wotmod");
            Package(Target(root), InstallerEngine.ModId, "0.22.6"); Package(old, InstallerEngine.ModId, "0.20.0");
            byte[] currentBefore = File.ReadAllBytes(Target(root));
            var engine = Engine(); engine.BeforeCommit = stage => { if (stage == "cleanup") File.WriteAllText(old, "external change"); };
            Reject(() => engine.Apply(root, false, p => { }), "changed_files");
            Assert(File.ReadAllText(old) == "external change", "unbacked external change not deleted");
            Assert(currentBefore.SequenceEqual(File.ReadAllBytes(Target(root))), "active original restored");
        });
        foreach (string scenarioValue in new[] { "fresh", "update", "remove", "repeat" })
        {
            string scenario = scenarioValue;
            Test("verified progress for " + scenario, () =>
            {
                string root = Fixture("NA", "2.4.1.1", "progress " + scenario);
                if (scenario == "update") Package(Target(root), InstallerEngine.ModId, "0.22.6");
                if (scenario == "remove" || scenario == "repeat") Engine().Apply(root, false, p => { });
                var values = new List<int>();
                Engine().Apply(root, scenario == "remove", p =>
                {
                    values.Add(p);
                    if (p == 100)
                    {
                        Assert(scenario == "remove" ? !File.Exists(Target(root)) :
                            InstallerEngine.Hash(File.ReadAllBytes(Target(root))) == InstallerEngine.PayloadHash,
                            "100 follows verified final files");
                    }
                });
                AssertProgress(values, true);
                Assert(values.SequenceEqual(scenario == "repeat" ? new[] { 0, 10, 20, 100 } :
                    new[] { 0, 10, 20, 35, 55, 75, 90, 100 }), "real operation milestones");
            });
        }
        Test("failed operations never report completion", () =>
        {
            foreach (string failure in new[] { "validation", "staged", "cleanup" })
            {
                string root = Fixture("NA", "2.4.1.1", "progress failure " + failure);
                Package(Target(root), InstallerEngine.ModId, "0.22.6");
                byte[] before = File.ReadAllBytes(Target(root));
                var engine = Engine(); var values = new List<int>();
                engine.IsRunning = () => failure == "validation";
                engine.BeforeCommit = stage => { if (stage == failure) throw new IOException("synthetic progress failure"); };
                bool rejected = false;
                try { engine.Apply(root, false, p => values.Add(p)); }
                catch (SetupError) { rejected = true; }
                catch (IOException) { rejected = true; }
                Assert(rejected, "failure rejected");
                AssertProgress(values, false);
                Assert(before.SequenceEqual(File.ReadAllBytes(Target(root))), "failure preserves original files");
            }
        });
        Test("preserves wallet, goals, history and future version folders", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "data"); string data = Path.Combine(root, "mods", "configs", "credit_ledger"); Directory.CreateDirectory(data);
            foreach (string f in new[] { "wallet.json", "ledger.json", "config.json" }) File.WriteAllText(Path.Combine(data, f), "USER DATA " + f);
            string inactive = Path.Combine(root, "mods", "2.4.2.0", InstallerEngine.FileName); Package(inactive, InstallerEngine.ModId, "0.22.6"); byte[] before = File.ReadAllBytes(inactive);
            Engine().Apply(root, false, p => { }); Engine().Apply(root, true, p => { });
            foreach (string f in Directory.GetFiles(data)) Assert(File.ReadAllText(f) == "USER DATA " + Path.GetFileName(f), "data preserved");
            Assert(before.SequenceEqual(File.ReadAllBytes(inactive)), "inactive preserved");
        });
        Test("rollback existing mod after post-replace failure", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "rollback"); Package(Target(root), InstallerEngine.ModId, "0.22.6"); byte[] before = File.ReadAllBytes(Target(root));
            var engine = Engine(); engine.BeforeCommit = stage => { if (stage == "cleanup") throw new IOException("test failure"); };
            try { engine.Apply(root, false, p => { }); throw new Exception("not failed"); } catch (IOException) { }
            Assert(before.SequenceEqual(File.ReadAllBytes(Target(root))), "restored");
        });
        Test("rollback fresh install after post-replace failure", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "new rollback"); var engine = Engine(); engine.BeforeCommit = stage => { if (stage == "cleanup") throw new IOException("test failure"); };
            try { engine.Apply(root, false, p => { }); throw new Exception("not failed"); } catch (IOException) { }
            Assert(!File.Exists(Target(root)), "fresh rolled back");
        });
        Test("uninstall backs up owned files and keeps others", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "remove"); Engine().Apply(root, false, p => { });
            string other = Path.Combine(Path.GetDirectoryName(Target(root)), "other.wotmod"); File.WriteAllText(other, "keep");
            var result = Engine().Apply(root, true, p => { }); Assert(!File.Exists(Target(root)) && File.ReadAllText(other) == "keep" && result.Backup != null, "removed safely");
        });
        Test("uninstall absent mod has no target writes", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "absent"); Reject(() => Engine().Apply(root, true, p => { }), "not_installed");
        });
        Test("locked old package aborts without replacement", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "locked"); Package(Target(root), InstallerEngine.ModId, "0.22.6"); byte[] before = File.ReadAllBytes(Target(root));
            using (var handle = File.Open(Target(root), FileMode.Open, FileAccess.Read, FileShare.None))
                try { Engine().Apply(root, false, p => { }); throw new Exception("not failed"); } catch (IOException) { }
            Assert(before.SequenceEqual(File.ReadAllBytes(Target(root))), "locked preserved");
        });
        Test("rollback restores all duplicates after cleanup failure", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "cleanup rollback"); string first = Target(root), second = Path.Combine(Path.GetDirectoryName(first), "previous.wotmod");
            Package(first, InstallerEngine.ModId, "0.22.6"); Package(second, InstallerEngine.ModId, "0.22.5");
            byte[] a = File.ReadAllBytes(first), b = File.ReadAllBytes(second);
            try { Engine().Apply(root, false, p => { if (p == 100) throw new IOException("test cleanup failure"); }); throw new Exception("not failed"); } catch (IOException) { }
            Assert(a.SequenceEqual(File.ReadAllBytes(first)) && b.SequenceEqual(File.ReadAllBytes(second)), "all restored");
        });
        Test("concurrent external target creation is not overwritten", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "concurrent"); var engine = Engine();
            engine.BeforeCommit = stage => { if (stage == "staged") File.WriteAllText(Target(root), "external file"); };
            Reject(() => engine.Apply(root, false, p => { }), "changed_files");
            Assert(File.ReadAllText(Target(root)) == "external file", "external preserved");
        });
        Test("concurrent old file change is preserved", () =>
        {
            string root = Fixture("NA", "2.4.1.1", "old concurrent"); Package(Target(root), InstallerEngine.ModId, "0.22.6"); var engine = Engine();
            engine.BeforeCommit = stage => { if (stage == "staged") File.WriteAllText(Target(root), "external update"); };
            Reject(() => engine.Apply(root, false, p => { }), "changed_files");
            Assert(File.ReadAllText(Target(root)) == "external update", "external update preserved");
        });
        Test("junction and child paths rejected", () =>
        {
            Reject(() => InstallerEngine.SafePath(Path.Combine(suite, "linked-game")), "linked_path");
            Reject(() => InstallerEngine.SafePath(Path.Combine(suite, "linked-game", "mods", "2.4.1.1", "new.wotmod")), "linked_path");
        });
        Test("real discovery validates all candidates without writing", () =>
        {
            foreach (var game in InstallerEngine.Discover()) Assert(new[] { "NA", "EU", "ASIA" }.Contains(game.Realm), "only supported");
        });
        Console.WriteLine("TOTAL " + passed + " passed; fixtures: " + suite);
    }
}
