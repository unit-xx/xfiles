import sys


import jz

from trdTablemodel import trdData, TradeTableModel_dd
from PyQt4.QtCore import *
from PyQt4.QtGui import *

def main(args):
    # make data instances
    stockdata = trdData()
    sindexdata = trdData()
    # start updating thread

    # make uic

if __name__=="__main__":
    main(sys.argv)
