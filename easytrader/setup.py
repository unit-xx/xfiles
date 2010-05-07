from cx_Freeze import setup, Executable


buildOptions = dict(
        #icon = "ztzq.ico",
        include_files = ["shmap.pkl", "szmap.pkl", "tradeinfo.db", "ztzq.ico", "hs300.txt", "portfolio", "msvcr_redist"],
        compressed = True)

setup(
        name = "hello",
        version = "0.1",
        description = "The EasyTrader",
        options = dict(build_exe = buildOptions),
        executables = [Executable("easytrader.py"), Executable("genstockindex.py")])

