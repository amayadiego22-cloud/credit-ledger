using System;
using System.ComponentModel;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

[assembly: AssemblyTitle("Credit Ledger Installer")]
[assembly: AssemblyDescription("Offline installer for Credit Ledger / Contabilidad de créditos")]
[assembly: AssemblyProduct("Credit Ledger")]
[assembly: AssemblyVersion("0.22.14.0")]
[assembly: AssemblyFileVersion("0.22.14.3")]

namespace CreditLedgerSetup
{
    internal sealed class SetupForm : Form
    {
        readonly Color dark = Color.FromArgb(16, 21, 25), card = Color.FromArgb(25, 32, 37), gold = Color.FromArgb(218, 186, 100);
        readonly Color muted = Color.FromArgb(162, 174, 182), green = Color.FromArgb(155, 216, 134);
        readonly ComboBox language = new ComboBox(), games = new ComboBox();
        readonly Label languageLabel = new Label(), subtitle = new Label(), step = new Label(), gameLabel = new Label(), folder = new Label(), destination = new Label(), notes = new Label(), status = new Label(), footer = new Label();
        readonly Label progressTitle = new Label(), progressPercent = new Label();
        readonly Button browse = new Button(), refresh = new Button(), install = new Button(), remove = new Button(), close = new Button();
        readonly ProgressBar progress = new ProgressBar();
        readonly BackgroundWorker worker = new BackgroundWorker();
        internal Func<string, bool, Action<int>, InstallResult> ApplyOperation = (root, removing, report) => new InstallerEngine().Apply(root, removing, report);
        bool english, busy, completed, failed, removingOperation;
        string statusEs, statusEn;

        public SetupForm()
        {
            AutoScaleDimensions = new SizeF(96, 96); AutoScaleMode = AutoScaleMode.Dpi;
            Text = "Credit Ledger · Instalador / Setup";
            ClientSize = new Size(800, 640);
            MinimumSize = new Size(816, 679);
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = dark; ForeColor = Color.White; Font = new Font("Segoe UI", 10);
            MaximizeBox = false; FormBorderStyle = FormBorderStyle.FixedSingle;
            using (var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("CreditLedger.Icon"))
                if (stream != null) Icon = new Icon(stream);

            // All structural spacing is 8pt. Native combo borders and font metrics
            // are optical exceptions; their surrounding rows remain on the grid.
            var main = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 7, Padding = new Padding(32), Margin = Padding.Empty };
            foreach (int size in new[] { 80, 40, 168, 56, 136, 64, 32 }) main.RowStyles.Add(new RowStyle(SizeType.Absolute, size));
            Controls.Add(main);
            var header = new Panel { Dock = DockStyle.Fill, Margin = Padding.Empty };
            var title = new Label { Text = "CREDIT LEDGER", Font = new Font("Segoe UI", 24, FontStyle.Bold), AutoSize = true, ForeColor = gold, Location = new Point(0, 0) };
            subtitle.Location = new Point(0, 48); subtitle.Size = new Size(480, 24); subtitle.ForeColor = muted;
            languageLabel.Location = new Point(560, 0); languageLabel.Size = new Size(176, 24); languageLabel.ForeColor = muted;
            language.SetBounds(560, 32, 176, 32); language.DropDownStyle = ComboBoxStyle.DropDownList;
            language.Items.AddRange(new object[] { "Español", "English" }); language.SelectedIndex = 0;
            language.SelectedIndexChanged += delegate { english = language.SelectedIndex == 1; Translate(); };
            header.Controls.AddRange(new Control[] { title, subtitle, languageLabel, language }); main.Controls.Add(header);
            step.Dock = DockStyle.Fill; step.Margin = Padding.Empty; step.TextAlign = ContentAlignment.MiddleLeft; step.ForeColor = gold; step.Font = new Font(Font, FontStyle.Bold); main.Controls.Add(step);

            var selection = new TableLayoutPanel { Dock = DockStyle.Fill, BackColor = card, ColumnCount = 2, RowCount = 4, Padding = new Padding(16), Margin = Padding.Empty };
            selection.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100)); selection.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 184));
            selection.RowStyles.Add(new RowStyle(SizeType.Absolute, 24)); selection.RowStyles.Add(new RowStyle(SizeType.Absolute, 48)); selection.RowStyles.Add(new RowStyle(SizeType.Absolute, 32)); selection.RowStyles.Add(new RowStyle(SizeType.Absolute, 32));
            gameLabel.Dock = DockStyle.Fill; gameLabel.Margin = Padding.Empty; selection.Controls.Add(gameLabel, 0, 0); selection.SetColumnSpan(gameLabel, 2);
            games.Dock = DockStyle.Fill; games.DropDownStyle = ComboBoxStyle.DropDownList; games.Margin = new Padding(0, 8, 16, 8);
            games.SelectedIndexChanged += delegate {
                if (failed) {
                    failed = false; removingOperation = false; UpdateFlow();
                    ShowStatus("Revisa la carpeta y pulsa Instalar / Actualizar.", "Check the folder and click Install / Update.", false, false);
                }
                UpdateSelection();
            }; selection.Controls.Add(games, 0, 1);
            Style(browse, false); browse.Dock = DockStyle.Fill; browse.Margin = new Padding(0, 8, 0, 8); browse.Click += Browse; selection.Controls.Add(browse, 1, 1);
            folder.Dock = DockStyle.Fill; folder.Margin = Padding.Empty; folder.TextAlign = ContentAlignment.MiddleLeft; folder.ForeColor = muted; folder.AutoEllipsis = true; selection.Controls.Add(folder, 0, 2); selection.SetColumnSpan(folder, 2);
            destination.Dock = DockStyle.Fill; destination.Margin = Padding.Empty; destination.TextAlign = ContentAlignment.MiddleLeft; destination.ForeColor = gold; destination.AutoEllipsis = true; selection.Controls.Add(destination, 0, 3); selection.SetColumnSpan(destination, 2);
            main.Controls.Add(selection);
            notes.Dock = DockStyle.Fill; notes.Margin = Padding.Empty; notes.ForeColor = muted; notes.Padding = new Padding(0, 16, 0, 0); main.Controls.Add(notes);
            var feedback = new TableLayoutPanel { Dock = DockStyle.Fill, BackColor = card, Padding = new Padding(16), Margin = Padding.Empty, ColumnCount = 1, RowCount = 3 };
            feedback.RowStyles.Add(new RowStyle(SizeType.Absolute, 32)); feedback.RowStyles.Add(new RowStyle(SizeType.Absolute, 32)); feedback.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            var progressHeading = new Panel { Dock = DockStyle.Fill, Margin = Padding.Empty };
            progressTitle.Name = "progressTitle"; progressTitle.Dock = DockStyle.Fill; progressTitle.TextAlign = ContentAlignment.MiddleLeft; progressTitle.Font = new Font("Segoe UI", 12, FontStyle.Bold);
            progressPercent.Name = "progressPercent"; progressPercent.Dock = DockStyle.Right; progressPercent.Width = 88; progressPercent.TextAlign = ContentAlignment.MiddleRight; progressPercent.Font = new Font("Segoe UI", 14, FontStyle.Bold); progressPercent.ForeColor = green;
            progressHeading.Controls.Add(progressTitle); progressHeading.Controls.Add(progressPercent); feedback.Controls.Add(progressHeading);
            progress.Name = "installProgress"; progress.Dock = DockStyle.Fill; progress.Margin = new Padding(0, 6, 0, 6); progress.Style = ProgressBarStyle.Continuous; progress.ForeColor = green; feedback.Controls.Add(progress);
            status.Name = "operationStatus"; status.Dock = DockStyle.Fill; status.Margin = Padding.Empty; status.Padding = Padding.Empty; status.Font = new Font("Segoe UI", 9); status.AutoEllipsis = true;
            feedback.Controls.Add(status); main.Controls.Add(feedback);
            var buttons = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.RightToLeft, Padding = new Padding(0, 16, 0, 0), Margin = Padding.Empty, WrapContents = false };
            Style(install, true); install.Name = "installAction"; install.Width = 192; install.Margin = Padding.Empty; install.Click += delegate { if (completed) Close(); else Begin(failed && removingOperation); };
            Style(close, false); close.Width = 96; close.Click += delegate { Close(); };
            Style(remove, false); remove.Width = 152; remove.Click += delegate { Begin(true); };
            Style(refresh, false); refresh.Width = 160; refresh.Click += delegate { FindGames(); };
            buttons.Controls.AddRange(new Control[] { install, close, remove, refresh }); main.Controls.Add(buttons);
            footer.Dock = DockStyle.Fill; footer.Margin = Padding.Empty; footer.ForeColor = muted; footer.Font = new Font("Segoe UI", 8); footer.Padding = new Padding(0, 8, 0, 0); main.Controls.Add(footer);
            AcceptButton = install; CancelButton = close;
            worker.WorkerReportsProgress = true;
            worker.ProgressChanged += ProgressChanged;
            worker.RunWorkerCompleted += Finished;
            FormClosing += delegate(object sender, FormClosingEventArgs e) { if (busy) e.Cancel = true; };
            Translate(); Shown += delegate { FindGames(); };
        }
        string T(string es, string en) { return english ? en : es; }
        void Style(Button button, bool primary)
        {
            button.Height = 40; button.Margin = new Padding(0, 0, 8, 0); button.FlatStyle = FlatStyle.Flat; button.FlatAppearance.BorderColor = primary ? gold : Color.FromArgb(67, 78, 85);
            button.BackColor = primary ? gold : card; button.ForeColor = primary ? dark : Color.White; button.Cursor = Cursors.Hand; button.UseVisualStyleBackColor = false;
        }
        void Translate()
        {
            subtitle.Text = T("Contabilidad de créditos · Instalador 0.22.14", "Credit tracking · Installer 0.22.14");
            languageLabel.Text = T("Idioma", "Language");
            gameLabel.Text = T("Instalación del juego", "Game installation"); browse.Text = T("Elegir carpeta…", "Choose folder…");
            refresh.Text = T("Buscar de nuevo", "Search again"); remove.Text = T("Quitar el mod…", "Remove mod…");
            footer.Text = T("NA · EU · ASIA   |   WoT 2.4.1.0 / 2.4.1.1   |   Sin descargas adicionales ni consola", "NA · EU · ASIA   |   WoT 2.4.1.0 / 2.4.1.1   |   No extra downloads or console");
            UpdateFlow(); UpdateSelection(); status.Text = T(statusEs ?? "", statusEn ?? "");
        }
        void UpdateFlow()
        {
            step.Text = completed ? T("03 / 03   TODO LISTO", "03 / 03   ALL DONE") : busy ? T("02 / 03   INSTALACIÓN", "02 / 03   INSTALLATION") : T("01 / 03   ELIGE TU WORLD OF TANKS", "01 / 03   CHOOSE YOUR WORLD OF TANKS");
            progressTitle.Text = completed ? (removingOperation ? T("Mod retirado correctamente", "Mod removed successfully") : T("¡Instalación completada!", "Installation complete!")) : busy ? (removingOperation ? T("Retirando Credit Ledger…", "Removing Credit Ledger…") : T("Instalando Credit Ledger…", "Installing Credit Ledger…")) : failed ? T("No se completó la operación", "The operation could not be completed") : T("Listo para instalar", "Ready to install");
            progressTitle.ForeColor = completed ? green : failed ? Color.FromArgb(243, 143, 143) : ForeColor;
            progressPercent.Text = progress.Value + " %"; progressPercent.AccessibleName = T("Progreso: ", "Progress: ") + progressPercent.Text;
            install.Text = completed ? T("Finalizar", "Finish") : busy ? (removingOperation ? T("Retirando…", "Removing…") : T("Instalando…", "Installing…")) : failed ? T("Reintentar", "Retry") : T("Instalar / Actualizar", "Install / Update");
            close.Text = busy ? T("Cancelar", "Cancel") : T("Cerrar", "Close");
            close.Visible = !completed; remove.Visible = refresh.Visible = !busy && !completed;
            games.Enabled = browse.Enabled = !busy && !completed; refresh.Enabled = language.Enabled = close.Enabled = !busy;
            notes.Text = completed ? (removingOperation ? T("Tus metas, preferencias e historial se conservaron.", "Your goals, preferences and history were kept.") : T("Ya puedes abrir World of Tanks y entrar al garaje. Tus metas e historial se conservaron.", "You can now open World of Tanks and enter the garage. Your goals and history were kept.")) : T("Cierra World of Tanks antes de instalar. Tus metas, preferencias e historial se conservan.", "Close World of Tanks before installing. Your goals, preferences and history are kept.");
        }
        void ShowStatus(string es, string en, bool error, bool success)
        { statusEs = es; statusEn = en; status.Text = T(es, en); status.ForeColor = error ? Color.FromArgb(243, 143, 143) : success ? green : ForeColor; }
        void UpdateSelection()
        {
            var game = games.SelectedItem as GameInstall;
            folder.Text = game == null ? T("¿No aparece tu juego? Pulsa Elegir carpeta.", "Game not listed? Click Choose folder.") : game.Root;
            destination.Text = game == null ? "" : T("Destino: ", "Destination: ") + @"mods\" + game.Version + @"\" + InstallerEngine.FileName;
            install.Enabled = !busy && (completed || game != null); remove.Enabled = game != null && !busy && !completed;
        }
        void FindGames()
        {
            if (busy || completed) return;
            games.Items.Clear();
            try { foreach (var game in InstallerEngine.Discover()) games.Items.Add(game); }
            catch { }
            if (games.Items.Count > 0) games.SelectedIndex = 0;
            failed = false; progress.Value = 0; UpdateFlow(); UpdateSelection();
            ShowStatus(games.Items.Count > 0 ? "Todo listo. Revisa la carpeta y pulsa Instalar / Actualizar." : "Selecciona la carpeta principal del juego, donde está version.xml.",
                games.Items.Count > 0 ? "Ready. Check the folder and click Install / Update." : "Choose the main game folder, the one containing version.xml.", false, false);
        }
        void Browse(object sender, EventArgs e)
        {
            if (busy || completed) return;
            using (var picker = new FolderBrowserDialog { Description = T("Elige la carpeta principal de World of Tanks (contiene version.xml).", "Choose the main World of Tanks folder (contains version.xml)."), ShowNewFolderButton = false })
            {
                var current = games.SelectedItem as GameInstall; if (current != null) picker.SelectedPath = current.Root;
                if (picker.ShowDialog(this) != DialogResult.OK) return;
                try
                {
                    var game = InstallerEngine.Inspect(picker.SelectedPath);
                    for (int i = 0; i < games.Items.Count; i++) if (String.Equals(((GameInstall)games.Items[i]).Root, game.Root, StringComparison.OrdinalIgnoreCase)) { games.SelectedIndex = i; return; }
                    games.Items.Add(game); games.SelectedItem = game;
                    failed = false; UpdateFlow(); ShowStatus("Carpeta válida. Ya puedes instalar.", "Valid folder. You can install now.", false, false);
                }
                catch (Exception ex) { Error(ex); }
            }
        }
        void Begin(bool removing)
        {
            var game = games.SelectedItem as GameInstall; if (game == null || busy || completed) return;
            if (removing && !failed && MessageBox.Show(this, T("¿Quitar Credit Ledger de esta instalación? Tus datos se conservarán.\n\n", "Remove Credit Ledger from this installation? Your data will be kept.\n\n") + game.Root,
                T("Quitar el mod", "Remove mod"), MessageBoxButtons.YesNo, MessageBoxIcon.Question, MessageBoxDefaultButton.Button2) != DialogResult.Yes) return;
            busy = true; failed = false; completed = false; removingOperation = removing; progress.Value = 0; UpdateFlow(); UpdateSelection();
            ShowStatus("Verificando los archivos…", "Verifying files…", false, false);
            worker.DoWork += RunOperation;
            worker.RunWorkerAsync(new object[] { game.Root, removing });
        }
        void RunOperation(object sender, DoWorkEventArgs e)
        {
            object[] args = (object[])e.Argument;
            e.Result = new object[] { ApplyOperation((string)args[0], (bool)args[1], p => worker.ReportProgress(p)), (bool)args[1] };
        }
        void ProgressChanged(object sender, ProgressChangedEventArgs e)
        {
            if (!busy) return;
            // Native completion can still fail after a progress callback.
            // Reserve the visible 100% and Finish state for worker success.
            progress.Value = Math.Max(progress.Value, Math.Min(99, Math.Max(0, e.ProgressPercentage)));
            int value = e.ProgressPercentage;
            if (value < 10) ShowStatus("Verificando los archivos…", "Verifying files…", false, false);
            else if (value < 20) ShowStatus("Revisando versiones anteriores…", "Checking existing versions…", false, false);
            else if (value < 35) ShowStatus("Creando la copia de seguridad…", "Creating the backup…", false, false);
            else if (value < 55) ShowStatus("Preparando los archivos del mod…", "Preparing the mod files…", false, false);
            else if (value < 75) ShowStatus(removingOperation ? "Retirando el mod…" : "Copiando el mod en tu juego…", removingOperation ? "Removing the mod…" : "Copying the mod into your game…", false, false);
            else if (value < 90) ShowStatus("Organizando los archivos finales…", "Finishing the file changes…", false, false);
            else ShowStatus(removingOperation ? "Comprobando los cambios…" : "Comprobando la instalación…", removingOperation ? "Checking the changes…" : "Checking the installation…", false, false);
            UpdateFlow();
        }
        void Finished(object sender, RunWorkerCompletedEventArgs e)
        {
            worker.DoWork -= RunOperation; busy = false;
            if (e.Error != null || e.Cancelled) { completed = false; failed = true; progress.Value = 0; UpdateFlow(); UpdateSelection(); Error(e.Error ?? new OperationCanceledException()); return; }
            var args = (object[])e.Result; var result = (InstallResult)args[0]; bool removed = (bool)args[1]; progress.Value = 100;
            completed = true; failed = false; removingOperation = removed; UpdateFlow(); UpdateSelection();
            string backupEs = result.Backup == null ? "" : "\nCopia de seguridad: " + result.Backup;
            string backupEn = result.Backup == null ? "" : "\nBackup: " + result.Backup;
            ShowStatus(removed ? "Credit Ledger se retiró correctamente." + backupEs : "Credit Ledger ya está listo para usar." + backupEs,
                removed ? "Credit Ledger was removed successfully." + backupEn : "Credit Ledger is ready to use." + backupEn, false, true);
            install.Focus();
        }
        void Error(Exception ex)
        {
            var known = ex as SetupError;
            string code = known == null ? "other" : known.Code;
            string es, en;
            switch (code)
            {
                case "game_running": es = "Cierra WoT por completo y vuelve a pulsar el botón. No se ha cerrado tu juego."; en = "Close WoT completely and try again. Your game has not been closed for you."; break;
                case "not_game": es = "Esta no es la carpeta principal de WoT. En Game Center usa Ajustes del juego → Mostrar en carpeta."; en = "This is not the main WoT folder. In Game Center use Game settings → Show in folder."; break;
                case "unsupported_realm": es = "Elige WoT de Wargaming: NA, EU o ASIA. Esta edición no admite Blitz, Lesta ni el servidor de prueba."; en = "Choose Wargaming WoT: NA, EU or ASIA. This release does not support Blitz, Lesta or Common Test."; break;
                case "unsupported_version": es = "Esta edición del mod es para WoT 2.4.1.0 / 2.4.1.1. Descarga una edición compatible con tu juego."; en = "This mod release supports WoT 2.4.1.0 / 2.4.1.1. Download a release matching your game."; break;
                case "paths_mismatch": es = "El juego no usa la carpeta de mods esperada. Actualiza o repara el cliente en Game Center y vuelve a intentar."; en = "The game does not use the expected mod folder. Update or repair it in Game Center and try again."; break;
                case "linked_path": es = "Esta ruta contiene un enlace de carpetas. Elige una instalación sin enlaces para evitar cambiar otra ubicación."; en = "This path contains a folder link. Choose an installation without links to avoid changing another location."; break;
                case "newer_version": es = "Ya tienes una edición más reciente del mod. Usa su instalador para evitar reemplazarla por una anterior."; en = "A newer mod release is installed. Use its installer to avoid replacing it with an older release."; break;
                case "foreign_file": es = "Otro archivo usa el nombre del mod. No se ha reemplazado; revisa esa carpeta antes de continuar."; en = "Another file uses the mod filename. It has not been replaced; check that folder before continuing."; break;
                case "not_installed": es = "No se encontró Credit Ledger en la carpeta activa de esta instalación."; en = "Credit Ledger was not found in this installation's active mod folder."; break;
                case "payload": es = "No se pudo verificar el mod incluido. Descarga de nuevo el instalador desde su ficha oficial."; en = "The included mod could not be verified. Download the installer again from its official listing."; break;
                case "installer_busy": es = "Otro instalador de Credit Ledger está trabajando. Espera a que termine."; en = "Another Credit Ledger installer is working. Wait for it to finish."; break;
                case "changed_files": es = "Los archivos cambiaron durante la preparación. Cierra otros instaladores y vuelve a intentar."; en = "Files changed while preparing. Close other installers and try again."; break;
                default:
                    if (ex is UnauthorizedAccessException) { es = "Windows no permite escribir en esa carpeta. Cierra el instalador y ábrelo como administrador si la instalación lo requiere."; en = "Windows denied access to that folder. Close the installer and run it as administrator if that installation requires it."; }
                    else { es = "No se pudo completar la operación. Detalle: " + ex.Message; en = "The operation could not be completed. Details: " + ex.Message; }
                    break;
            }
            ShowStatus(es, en, true, false);
        }
    }
    internal static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new SetupForm());
        }
    }
}
