from cx_Freeze import setup, Executable
import os, sys
import sqlite3 as db

def backenddir():
    pypath = os.path.join(sys.prefix, "Lib\site-packages\PyQt4\plugins\phonon_backend")
    return pypath

def setupdb(dbpath, dbname, force=False):
    cwd = os.getcwd()
    os.chdir(dbpath)
    if os.path.exists(dbname):
        if force:
            os.remove(dbname)
        else:
            print "%s exists, will not be changed" % dbname
    else:
        print "making fresh trading database..."
        conn = db.connect(dbname)
        conn.execute("""
            CREATE TABLE [rawtradeinfo] 
            (
                [time] TEXT,
                [req] TEXT,
                [resp] TEXT,
                [respstatus] TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE [rawsindextradeinfo] 
            (
                [time] TEXT,
                [req] TEXT,
                [resp] TEXT
            )
        """)
        print "done!"

    os.chdir(cwd)

buildOptions = dict(
        build_exe = "build\\easytrader",
        icon = "ztzq.ico",
        include_files = ["ztzq.ico", "hs300.txt", "itrader.cfg", "itrader-gw.cfg", "itrader-jhj.cfg", "easytrader.cfg", "easytrader-prod.cfg", "easytrader-jhj.cfg", "msvcr_redist", "jsdhqdll", "openmusic", "closemusic", (backenddir(), "phonon_backend")],
        compressed = True,
        optimize = 0)

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
        name = "easytrader",
        version = "0.1",
        description = "The EasyTrader",
        options = dict(build_exe = buildOptions),
        executables = [Executable("itrader.py", base = base), 
            Executable("easytrader.py", base = base), 
            Executable("genstockindex.py")]
        )

setupdb(buildOptions["build_exe"], "tradeinfo.db")
