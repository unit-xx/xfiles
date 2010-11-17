from cx_Freeze import setup, Executable
import os, sys
import sqlite3 as db

def backenddir():
    pypath = os.path.join(sys.prefix, "lib/python2.6/site-packages/PyQt4/phonon.so")
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
        build_exe = "build/easytrader",
        icon = "ztzq.ico",
        include_files = ["ztzq.ico", "hs300.txt",
            "itrader.cfg", "itrader-gw.cfg", "itrader-jhj.cfg",
            "easytrader.cfg", "easytrader-prod.cfg",
            "openmusic", "closemusic",
            (backenddir(), "phonon.so")],
        compressed = True,
        optimize = 2)

setup(
        name = "easytrader",
        version = "0.1",
        description = "The EasyTrader",
        options = dict(build_exe = buildOptions),
        executables = [Executable("itrader.py"), Executable("easytrader.py"), Executable("genstockindex.py")]
        )

setupdb(buildOptions["build_exe"], "tradeinfo.db")