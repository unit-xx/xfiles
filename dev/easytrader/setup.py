from cx_Freeze import setup, Executable


buildOptions = dict(
        icon = "ztzq.ico",
        include_files = ["shmap.pkl", "szmap.pkl", "tradeinfo.db", "ztzq.ico", "hs300.txt", "easytrader.cfg", "easytrader-prod.cfg", "portfolio", "msvcr_redist", "jsdhqdll", "music"],
        compressed = True,
        optimize = 2)

setup(
        name = "easytrader",
        version = "0.1",
        description = "The EasyTrader",
        options = dict(build_exe = buildOptions),
        executables = [Executable("easytrader.py"), Executable("genstockindex.py"), Executable("jsdcmd.py")])

