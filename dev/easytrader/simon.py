import sys

import jz

from trdTablemodel import trdData, TradeTableModel_dd
from trdUpdater.py import 
from PyQt4.QtCore import *
from PyQt4.QtGui import *

def hs300Updater(
def main(args):
    # make data instances
    stockdata = trdData()
    stockdata.colname = [
            "name",
            "latest",
            "close",
            "open",
            "volumn"
            ]
    stockdata.rowname = ["SH000300"]

    sindexdata = trdData()
    # start updating thread

    # make uic

if __name__=="__main__":
    main(sys.argv)
