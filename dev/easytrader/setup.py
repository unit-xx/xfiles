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
        include_files = ["ztzq.ico", "hs300.txt", "easytrader.cfg", "easytrader-prod.cfg", "portfolio", "msvcr_redist", "jsdhqdll", "music", (backenddir(), "phonon_backend")],
        compressed = True,
        optimize = 2)

setup(
        name = "easytrader",
        version = "0.1",
        description = "The EasyTrader",
        options = dict(build_exe = buildOptions),
        executables = [Executable("easytrader.py"), Executable("genstockindex.py")]
        )

setupdb(buildOptions["build_exe"], "tradeinfo.db")
