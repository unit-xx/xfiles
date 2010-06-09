from cx_Freeze import setup, Executable

buildOptions = dict(
        include_files = ["quoteserver.cfg", "sindexquoteserver.cfg", "stockquoteserver.cfg"],
        compressed = True,
        optimize = 2)

setup(
        name = "quoteserver",
        version = "0.1",
        description = "quote servers",
        options = dict(build_exe = buildOptions),
        executables = [Executable("quoteserver.py"), Executable("sindexquoteserver.py"), Executable("stockquoteserver.py")])

