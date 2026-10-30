using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;

namespace CreditLedgerSetup
{
    // Exercises the real form and BackgroundWorker with a fake operation only.
    // No test writes to an installed game or changes player data.
    internal static class InstallerFlowTests
    {
        static int passed;
        static readonly BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
        static T Field<T>(SetupForm form, string name) { return (T)typeof(SetupForm).GetField(name, Private).GetValue(form); }
        static void Set(SetupForm form, string name, object value) { typeof(SetupForm).GetField(name, Private).SetValue(form, value); }
        static void Call(SetupForm form, string name, params object[] args) { typeof(SetupForm).GetMethod(name, Private).Invoke(form, args); }
        static void Assert(bool condition, string message) { if (!condition) throw new Exception(message); }
        static void Test(string name, Action body) { body(); passed++; Console.WriteLine("PASS " + name); }
        static SetupForm Ready()
        {
            var form = new SetupForm(); form.Show(); Application.DoEvents();
            var games = Field<ComboBox>(form, "games"); games.Items.Clear();
            games.Items.Add(new GameInstall { Root = @"D:\Juegos\World_of_Tanks_NA", Realm = "NA", Version = "2.4.1.1" });
            games.SelectedIndex = 0;
            return form;
        }
        static void Wait(Func<bool> predicate)
        {
            var watch = Stopwatch.StartNew();
            while (!predicate()) { Application.DoEvents(); if (watch.ElapsedMilliseconds > 10000) throw new Exception("form timeout"); Thread.Sleep(5); }
            Application.DoEvents();
        }
        static void Finish(SetupForm form, bool removed)
        {
            Call(form, "Finished", null, new RunWorkerCompletedEventArgs(new object[] { new InstallResult(), removed }, null, false));
        }
        static void Report(SetupForm form, int value) { Call(form, "ProgressChanged", null, new ProgressChangedEventArgs(value, null)); }
        static void Busy(SetupForm form)
        {
            Set(form, "busy", true); Call(form, "UpdateFlow"); Call(form, "UpdateSelection");
        }
        [STAThread]
        static int Main(string[] args)
        {
            Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
            if (args.Length > 0 && args[0] == "--preview-complete")
            {
                using (var preview = Ready())
                {
                    preview.Text += " · Vista de prueba"; Finish(preview, false);
                    Application.Run(preview);
                }
                return 0;
            }
            int exitCode = 1;
            using (var messageHost = new Form { ShowInTaskbar = false, Opacity = 0 })
            {
                messageHost.Shown += delegate { messageHost.BeginInvoke(new Action(delegate { exitCode = RunTests(); messageHost.Close(); })); };
                Application.Run(messageHost);
            }
            return exitCode;
        }
        static int RunTests()
        {
            try
            {
                Control.CheckForIllegalCrossThreadCalls = true;
                Test("ready Spanish, no game disables install", () => {
                    using (var f = Ready()) {
                        Assert(Field<Label>(f,"progressTitle").Text == "Listo para instalar", "Spanish default");
                        Field<ComboBox>(f,"games").Items.Clear(); Call(f,"UpdateSelection");
                        Assert(!Field<Button>(f,"install").Enabled, "requires game selection");
                        Assert(Field<ProgressBar>(f,"progress").Value == 0, "starts at zero");
                    }
                });
                Test("selected game enables install with 20px bar", () => {
                    using (var f = Ready()) {
                        Assert(Field<Button>(f,"install").Enabled, "selected game");
                        Assert(Field<ProgressBar>(f,"progress").Height == 20, "classic bar height");
                    }
                });
                Test("busy blocks controls and window close", () => {
                    using (var f = Ready()) {
                        Busy(f);
                        Assert(!Field<Button>(f,"install").Enabled && !Field<Button>(f,"close").Enabled, "no double operation");
                        Assert(!Field<ComboBox>(f,"games").Enabled && !Field<Button>(f,"browse").Enabled, "selection frozen");
                        f.Close(); Assert(!f.IsDisposed && f.Visible, "cannot close while writing");
                        Set(f,"busy",false);
                    }
                });
                Test("progress advances monotonically, success owns 100 percent", () => {
                    using (var f = Ready()) {
                        Busy(f); Report(f,55); Report(f,20);
                        Assert(Field<ProgressBar>(f,"progress").Value == 55, "no regression");
                        Report(f,100);
                        Assert(Field<ProgressBar>(f,"progress").Value == 99 && Field<Button>(f,"install").Text != "Finalizar", "no premature Finish");
                        Set(f,"busy",false);
                    }
                });
                Test("real worker reports stages and completes", () => {
                    using (var f = Ready()) using (var gate = new ManualResetEvent(false)) {
                        f.ApplyOperation = (root,remove,report) => { report(55); gate.WaitOne(); report(100); return new InstallResult(); };
                        Field<Button>(f,"install").PerformClick();
                        try {
                            Wait(() => Field<ProgressBar>(f,"progress").Value == 55);
                            Assert(Field<Label>(f,"status").Text.Contains("Copiando"), "stage matches copying: " + Field<Label>(f,"status").Text);
                            Assert(Field<bool>(f,"busy"), "asynchronous busy state");
                        } finally { gate.Set(); }
                        Wait(() => !Field<bool>(f,"busy"));
                        Assert(Field<ProgressBar>(f,"progress").Value == 100 && Field<bool>(f,"completed"), "completed worker");
                    }
                });
                Test("success has one Finish action and keeps selection locked", () => {
                    using (var f = Ready()) {
                        Finish(f,false);
                        Assert(Field<Button>(f,"install").Text == "Finalizar" && Field<Button>(f,"install").Enabled, "Finish enabled");
                        Assert(!Field<Button>(f,"close").Visible && !Field<Button>(f,"remove").Visible && !Field<Button>(f,"refresh").Visible, "one action");
                        Assert(!Field<ComboBox>(f,"games").Enabled, "no accidental second installation");
                    }
                });
                Test("Finish actually closes the form", () => {
                    using (var f = Ready()) { Finish(f,false); Field<Button>(f,"install").PerformClick(); Assert(f.IsDisposed, "Finish closes"); }
                });
                Test("late progress cannot overwrite completed state", () => {
                    using (var f = Ready()) {
                        Finish(f,false); Report(f,55);
                        Assert(Field<ProgressBar>(f,"progress").Value == 100 && Field<Label>(f,"status").Text.Contains("listo para usar"), "completion stable");
                    }
                });
                Test("worker failure permits retry and never shows success", () => {
                    using (var f = Ready()) {
                        f.ApplyOperation = (root,remove,report) => { report(90); throw new SetupError("game_running"); };
                        Field<Button>(f,"install").PerformClick(); Wait(() => !Field<bool>(f,"busy"));
                        Assert(Field<bool>(f,"failed") && !Field<bool>(f,"completed"), "error state");
                        Assert(Field<Button>(f,"install").Text == "Reintentar" && Field<Button>(f,"install").Enabled, "retry enabled");
                        Assert(Field<ProgressBar>(f,"progress").Value == 0 && Field<Label>(f,"status").Text.Contains("Cierra WoT"), "no false 100: " + Field<ProgressBar>(f,"progress").Value + " / " + Field<Label>(f,"status").Text);
                        f.ApplyOperation = (root,remove,report) => new InstallResult();
                        Field<Button>(f,"install").PerformClick(); Wait(() => !Field<bool>(f,"busy"));
                        Assert(Field<bool>(f,"completed"), "retry succeeds without reopening");
                    }
                });
                Test("removal retry repeats removal rather than installing", () => {
                    using (var f = Ready()) {
                        Set(f,"removingOperation",true);
                        Call(f,"Finished",null,new RunWorkerCompletedEventArgs(null,new SetupError("changed_files"),false));
                        bool didRemove = false;
                        f.ApplyOperation = (root,remove,report) => { didRemove = remove; report(90); return new InstallResult(); };
                        Field<Button>(f,"install").PerformClick(); Wait(() => !Field<bool>(f,"busy"));
                        Assert(didRemove && Field<Label>(f,"progressTitle").Text.Contains("retirado"), "retry preserves operation");
                        Assert(Field<Button>(f,"install").Text == "Finalizar", "remove Finish");
                    }
                });
                Test("English works during progress, errors and completion", () => {
                    using (var f = Ready()) {
                        Field<ComboBox>(f,"language").SelectedIndex = 1;
                        Assert(Field<Label>(f,"progressTitle").Text == "Ready to install", "English ready");
                        Busy(f); Report(f,55); Assert(Field<Label>(f,"status").Text.Contains("Copying"), "English stage");
                        Call(f,"Finished",null,new RunWorkerCompletedEventArgs(null,new SetupError("game_running"),false));
                        Assert(Field<Button>(f,"install").Text == "Retry" && Field<Label>(f,"status").Text.Contains("Close WoT"), "English error");
                        Finish(f,false); Assert(Field<Button>(f,"install").Text == "Finish", "English Finish");
                        Field<ComboBox>(f,"language").SelectedIndex = 0;
                        Assert(Field<Button>(f,"install").Text == "Finalizar" && Field<ProgressBar>(f,"progress").Value == 100, "language preserves success");
                    }
                });
                Test("changing game clears a previous removal retry", () => {
                    using (var f = Ready()) {
                        Set(f,"removingOperation",true);
                        Call(f,"Finished",null,new RunWorkerCompletedEventArgs(null,new SetupError("changed_files"),false));
                        var games = Field<ComboBox>(f,"games");
                        games.Items.Add(new GameInstall { Root = @"D:\Juegos\World_of_Tanks_EU", Realm = "EU", Version = "2.4.1.1" });
                        games.SelectedIndex = 1;
                        Assert(!Field<bool>(f,"failed") && !Field<bool>(f,"removingOperation"), "no removal inherited by another game");
                        Assert(Field<Button>(f,"install").Text == "Instalar / Actualizar", "new selection is ready to install");
                    }
                });
                Test("cancelled worker is retryable, not successful", () => {
                    using (var f = Ready()) {
                        Busy(f); Call(f,"Finished",null,new RunWorkerCompletedEventArgs(null,null,true));
                        Assert(Field<bool>(f,"failed") && !Field<bool>(f,"completed") && Field<Button>(f,"install").Text == "Reintentar", "cancelled state");
                    }
                });
                Console.WriteLine(passed + " form-flow checks passed"); return 0;
            }
            catch (Exception ex) { Console.Error.WriteLine(ex); return 1; }
        }
    }
}
