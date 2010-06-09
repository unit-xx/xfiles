from cx_Freeze import setup, Executable
import os, sys

def backenddir():
    pypath = os.path.join(sys.prefix, "Lib\site-packages\PyQt4\plugins\phonon_backend")
    return pypath

buildOptions = dict(
        build_exe = "build\\easytrader",
        icon = "ztzq.ico",
        include_files = ["shmap.pkl", "szmap.pkl", "tradeinfo.db", "ztzq.ico", "hs300.txt", "easytrader.cfg", "easytrader-prod.cfg", "portfolio", "msvcr_redist", "jsdhqdll", "music", (backenddir(), "phonon_backend")],
        compressed = True,
        optimize = 2)

setup(
        name = "easytrader",
        version = "0.1",
        description = "The EasyTrader",
        options = dict(build_exe = buildOptions),
        executables = [Executable("easytrader.py"), Executable("genstockindex.py"), Executable("jsdcmd.py")])

