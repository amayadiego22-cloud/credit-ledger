// Own build helper. CPython and the Wargaming installation are external dependencies.
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

namespace WotEconomy.Build
{
    public sealed class CompileResult
    {
        public string Source { get; set; }
        public string Output { get; set; }
        public string PythonVersion { get; set; }
        public string MagicHex { get; set; }
        public long Bytes { get; set; }
        public bool MarshalRoundtrip { get; set; }
        public bool ExecutedOwnSelftest { get; set; }
    }

    public sealed class Python27Compiler : IDisposable
    {
        [DllImport("kernel32", CharSet = CharSet.Unicode, SetLastError = true)]
        static extern IntPtr LoadLibraryEx(string path, IntPtr reserved, uint flags);
        [DllImport("kernel32", CharSet = CharSet.Ansi, SetLastError = true)]
        static extern IntPtr GetProcAddress(IntPtr module, string name);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate void VoidFn();
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate void SetPointerFn(IntPtr value);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate void SetIntFn(int value);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate IntPtr StringFn();
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate int IntFn();
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate IntPtr CompileFn(IntPtr source, IntPtr filename, int start, IntPtr flags);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate IntPtr MarshalWriteFn(IntPtr obj, int version);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate IntPtr MarshalReadFn(IntPtr data, IntPtr size);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate int StringBytesFn(IntPtr obj, out IntPtr data, out IntPtr size);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate void DecrefFn(IntPtr obj);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate void FetchFn(out IntPtr type, out IntPtr value, out IntPtr traceback);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate IntPtr ObjectStrFn(IntPtr obj);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate int DictSetFn(IntPtr dict, IntPtr name, IntPtr value);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate IntPtr EvalFn(IntPtr code, IntPtr globals, IntPtr locals);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate IntPtr SizedObjectFn(IntPtr length);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate int SysSetFn(IntPtr name, IntPtr value);
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate int RunSimpleFn(IntPtr source, IntPtr flags);

        readonly IntPtr library;
        readonly List<IntPtr> persistent = new List<IntPtr>();
        readonly DecrefFn decref;
        readonly CompileFn compile;
        readonly MarshalWriteFn marshalWrite;
        readonly MarshalReadFn marshalRead;
        readonly StringBytesFn stringBytes;
        readonly FetchFn errorFetch;
        readonly ObjectStrFn objectStr;
        readonly VoidFn finalize;
        readonly IntFn getMagic;
        readonly string version;
        bool initialized;

        T Bind<T>(string name) where T : class
        {
            IntPtr address = GetProcAddress(library, name);
            if (address == IntPtr.Zero) throw new InvalidOperationException("Missing Python C API export: " + name);
            return Marshal.GetDelegateForFunctionPointer(address, typeof(T)) as T;
        }

        void Flag(string name, int value)
        {
            IntPtr address = GetProcAddress(library, name);
            if (address == IntPtr.Zero) throw new InvalidOperationException("Missing Python flag: " + name);
            Marshal.WriteInt32(address, value);
        }

        static IntPtr BytesZ(byte[] value)
        {
            IntPtr result = Marshal.AllocHGlobal(value.Length + 1);
            Marshal.Copy(value, 0, result, value.Length);
            Marshal.WriteByte(result, value.Length, 0);
            return result;
        }

        static IntPtr Utf8Z(string value) { return BytesZ(Encoding.UTF8.GetBytes(value)); }

        IntPtr Keep(string value)
        {
            IntPtr ptr = Utf8Z(value);
            persistent.Add(ptr);
            return ptr;
        }

        public Python27Compiler(string dllPath, string isolatedHome)
        {
            // Absolute DLL path; altered search path lets Windows locate runtime DLL
            // dependencies next to that DLL without changing PATH or registry.
            library = LoadLibraryEx(Path.GetFullPath(dllPath), IntPtr.Zero, 0x00000008);
            if (library == IntPtr.Zero) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            version = Marshal.PtrToStringAnsi(Bind<StringFn>("Py_GetVersion")());
            if (!version.StartsWith("2.7.")) throw new InvalidOperationException("Expected CPython 2.7: " + version);
            if (Bind<IntFn>("Py_IsInitialized")() != 0) throw new InvalidOperationException("Run this tool in a fresh PowerShell process.");
            decref = Bind<DecrefFn>("Py_DecRef");
            compile = Bind<CompileFn>("Py_CompileStringFlags");
            marshalWrite = Bind<MarshalWriteFn>("PyMarshal_WriteObjectToString");
            marshalRead = Bind<MarshalReadFn>("PyMarshal_ReadObjectFromString");
            stringBytes = Bind<StringBytesFn>("PyString_AsStringAndSize");
            errorFetch = Bind<FetchFn>("PyErr_Fetch");
            objectStr = Bind<ObjectStrFn>("PyObject_Str");
            finalize = Bind<VoidFn>("Py_Finalize");
            getMagic = Bind<IntFn>("PyImport_GetMagicNumber");
            Flag("Py_NoSiteFlag", 1);
            Flag("Py_IgnoreEnvironmentFlag", 1);
            Flag("Py_DontWriteBytecodeFlag", 1);
            Flag("Py_OptimizeFlag", 0);
            Flag("Py_NoUserSiteDirectory", 1);
            Bind<SetPointerFn>("Py_SetPythonHome")(Keep(Path.GetFullPath(isolatedHome)));
            Bind<SetPointerFn>("Py_SetProgramName")(Keep("wot-economy-build-helper"));
            Bind<SetIntFn>("Py_InitializeEx")(0);
            initialized = true;
            // Native modules necessary for compilation are built into the DLL.
            // Do not search the game, the current directory, or any third-party libs.
            IntPtr emptyPath = Bind<SizedObjectFn>("PyList_New")(IntPtr.Zero);
            IntPtr pathName = Utf8Z("path");
            try
            {
                if (emptyPath == IntPtr.Zero || Bind<SysSetFn>("PySys_SetObject")(pathName, emptyPath) != 0)
                    throw PythonError("Clearing module search path");
            }
            finally
            {
                if (emptyPath != IntPtr.Zero) decref(emptyPath);
                Marshal.FreeHGlobal(pathName);
            }
            if (getMagic() != 0x0a0df303) throw new InvalidOperationException("Unexpected Python bytecode magic: " + getMagic().ToString("x8"));
            // Python2 normally imports encodings from its external stdlib. Register
            // the required built-in codecs with our own fixed bootstrap instead.
            // This never opens or executes a file from the game or input project.
            string bootstrap =
                "import _codecs\n" +
                "def _wot_build_codec(name):\n" +
                "    name = name.replace('-', '_')\n" +
                "    name = {'utf8': 'utf_8', 'latin1': 'latin_1', 'iso_8859_1': 'latin_1'}.get(name, name)\n" +
                "    encode = getattr(_codecs, name + '_encode', None)\n" +
                "    decode = getattr(_codecs, name + '_decode', None)\n" +
                "    if encode is not None and decode is not None:\n" +
                "        return (encode, decode, None, None)\n" +
                "_codecs.register(_wot_build_codec)\n";
            IntPtr bootstrapBuffer = Utf8Z(bootstrap);
            try
            {
                if (Bind<RunSimpleFn>("PyRun_SimpleStringFlags")(bootstrapBuffer, IntPtr.Zero) != 0)
                    throw new InvalidOperationException("Initializing built-in source codecs failed.");
            }
            finally { Marshal.FreeHGlobal(bootstrapBuffer); }
        }

        byte[] StringBytes(IntPtr obj)
        {
            IntPtr ptr, length;
            if (stringBytes(obj, out ptr, out length) != 0) throw PythonError("Reading Python byte string");
            long n = length.ToInt64();
            if (n < 0 || n > Int32.MaxValue) throw new InvalidOperationException("Byte string too large.");
            byte[] bytes = new byte[(int)n];
            Marshal.Copy(ptr, bytes, 0, bytes.Length);
            return bytes;
        }

        Exception PythonError(string context)
        {
            IntPtr type, value, traceback;
            errorFetch(out type, out value, out traceback);
            string message = "unknown Python error";
            string typeName = "PythonError";
            IntPtr text = IntPtr.Zero;
            try
            {
                if (type != IntPtr.Zero) {
                    text = objectStr(type);
                    if (text != IntPtr.Zero) typeName = Encoding.UTF8.GetString(StringBytes(text));
                    if (text != IntPtr.Zero) { decref(text); text = IntPtr.Zero; }
                }
                if (value != IntPtr.Zero) {
                    text = objectStr(value);
                    if (text != IntPtr.Zero) message = Encoding.UTF8.GetString(StringBytes(text));
                }
            }
            finally
            {
                if (text != IntPtr.Zero) decref(text);
                if (type != IntPtr.Zero) decref(type);
                if (value != IntPtr.Zero) decref(value);
                if (traceback != IntPtr.Zero) decref(traceback);
            }
            return new InvalidOperationException(context + ": " + typeName + ": " + message);
        }

        public CompileResult Compile(string sourcePath, string outputPath, string logicalFilename, bool executeOwnSelftest)
        {
            if (!initialized) throw new ObjectDisposedException("Python27Compiler");
            sourcePath = Path.GetFullPath(sourcePath);
            outputPath = Path.GetFullPath(outputPath);
            if (String.Equals(sourcePath, outputPath, StringComparison.OrdinalIgnoreCase)) throw new ArgumentException("Source and output must differ.");
            byte[] source = File.ReadAllBytes(sourcePath);
            if (Array.IndexOf(source, (byte)0) >= 0) throw new ArgumentException("Source contains a NUL byte.");
            if (!logicalFilename.EndsWith(".py", StringComparison.OrdinalIgnoreCase)) throw new ArgumentException("Logical filename must end in .py.");
            IntPtr sourceBuffer = BytesZ(source), filenameBuffer = Utf8Z(logicalFilename);
            IntPtr code = IntPtr.Zero, packed = IntPtr.Zero, roundtrip = IntPtr.Zero, packedAgain = IntPtr.Zero, payloadBuffer = IntPtr.Zero;
            try
            {
                code = compile(sourceBuffer, filenameBuffer, 257, IntPtr.Zero); // Py_file_input
                if (code == IntPtr.Zero) throw PythonError("Compiling " + logicalFilename);
                packed = marshalWrite(code, 2);
                if (packed == IntPtr.Zero) throw PythonError("Marshaling bytecode");
                byte[] payload = StringBytes(packed);
                payloadBuffer = BytesZ(payload);
                roundtrip = marshalRead(payloadBuffer, new IntPtr(payload.Length));
                if (roundtrip == IntPtr.Zero) throw PythonError("Verifying marshal roundtrip");
                packedAgain = marshalWrite(roundtrip, 2);
                if (packedAgain == IntPtr.Zero) throw PythonError("Remarshaling roundtrip");
                byte[] verified = StringBytes(packedAgain);
                if (payload.Length != verified.Length) throw new InvalidOperationException("Marshal roundtrip length mismatch.");
                for (int i = 0; i < payload.Length; i++) if (payload[i] != verified[i]) throw new InvalidOperationException("Marshal roundtrip content mismatch.");
                if (executeOwnSelftest) ExecuteSelftest(roundtrip);
                long timestamp = (File.GetLastWriteTimeUtc(sourcePath).Ticks - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc).Ticks) / TimeSpan.TicksPerSecond;
                if (timestamp < 0 || timestamp > UInt32.MaxValue) throw new InvalidOperationException("Source timestamp outside Python2 pyc range.");
                Directory.CreateDirectory(Path.GetDirectoryName(outputPath));
                using (FileStream stream = new FileStream(outputPath, FileMode.Create, FileAccess.Write, FileShare.None))
                using (BinaryWriter writer = new BinaryWriter(stream))
                {
                    writer.Write(getMagic());
                    writer.Write((UInt32)timestamp);
                    writer.Write(payload);
                }
                byte[] saved = File.ReadAllBytes(outputPath);
                if (saved.Length != payload.Length + 8 || saved[0] != 0x03 || saved[1] != 0xf3 || saved[2] != 0x0d || saved[3] != 0x0a)
                    throw new InvalidOperationException("Written pyc header verification failed.");
                return new CompileResult { Source = sourcePath, Output = outputPath, PythonVersion = version, MagicHex = "03f30d0a", Bytes = saved.Length, MarshalRoundtrip = true, ExecutedOwnSelftest = executeOwnSelftest };
            }
            finally
            {
                if (packedAgain != IntPtr.Zero) decref(packedAgain);
                if (roundtrip != IntPtr.Zero) decref(roundtrip);
                if (packed != IntPtr.Zero) decref(packed);
                if (code != IntPtr.Zero) decref(code);
                if (payloadBuffer != IntPtr.Zero) Marshal.FreeHGlobal(payloadBuffer);
                Marshal.FreeHGlobal(filenameBuffer);
                Marshal.FreeHGlobal(sourceBuffer);
            }
        }

        void ExecuteSelftest(IntPtr code)
        {
            IntPtr globals = Bind<StringFn>("PyDict_New")();
            IntPtr name = Utf8Z("__builtins__");
            IntPtr result = IntPtr.Zero;
            try
            {
                if (globals == IntPtr.Zero) throw PythonError("Creating selftest globals");
                IntPtr builtins = Bind<StringFn>("PyEval_GetBuiltins")();
                if (Bind<DictSetFn>("PyDict_SetItemString")(globals, name, builtins) != 0) throw PythonError("Setting selftest builtins");
                result = Bind<EvalFn>("PyEval_EvalCode")(code, globals, globals);
                if (result == IntPtr.Zero) throw PythonError("Executing own Python2 selftest");
            }
            finally
            {
                if (result != IntPtr.Zero) decref(result);
                if (globals != IntPtr.Zero) decref(globals);
                Marshal.FreeHGlobal(name);
            }
        }

        public void Dispose()
        {
            if (initialized) { finalize(); initialized = false; }
            foreach (IntPtr ptr in persistent) Marshal.FreeHGlobal(ptr);
            persistent.Clear();
            // The OS releases this process's native module on child-process exit.
            // Do not unload the DLL while .NET still owns native delegates.
        }
    }
}
