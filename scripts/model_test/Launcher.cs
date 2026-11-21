using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

class Launcher {
    [STAThread]
    static int Main(string[] args) {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        try {
            string command = "-I \"" + Path.Combine(root, "launcher.py") + "\"";
            if (args.Length == 2 && args[0] == "--smoke-test")
                command += " --smoke-test \"" + Path.GetFullPath(args[1]) + "\"";
            else if (args.Length != 0)
                return 2;
            var info = new ProcessStartInfo(Path.Combine(root, "python", "pythonw.exe"), command);
            info.WorkingDirectory = root;
            info.UseShellExecute = false;
            info.EnvironmentVariables["TRITON_CACHE_DIR"] = Path.Combine(root, "_temp", "triton");
            info.EnvironmentVariables["FLEX_GEMM_AUTOTUNE_CACHE_PATH"] = Path.Combine(root, "_temp", "flex_gemm.json");
            using (var child = Process.Start(info)) {
                child.WaitForExit();
                return child.ExitCode;
            }
        } catch (Exception error) {
            MessageBox.Show(error.Message, "DepthTricia");
            return 1;
        }
    }
}
