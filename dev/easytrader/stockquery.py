# -*- coding: utf-8 -*-
import jz
import sys
from stockqueryui import Ui_stockquery
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class StockInfoModel(QAbstractTableModel):
    def __init__(self, header, headermap, data, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.header = header
        self.headermap = headermap
        self.data = data

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.header)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            hname = self.header[section]
            try:
                hname = self.headermap[hname]
            except KeyError:
                pass
            return QVariant(hname)
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(section + 1))
        return QVariant()

    def data(self, index, role):
        # self.data is list of dict
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        try:
            rowindex = index.row()
            columnkey = self.header[index.column()]
            celldata = self.data[rowindex][columnkey]
        except IndexError, KeyError:
            return QVariant()
        return QVariant(celldata)

    @pyqtSlot(int)
    def updaterow(self, rowindex):
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.index(rowindex,0),
                self.index(rowindex,self.columnCount()-1))

class stockquerydlg(QDialog, Ui_stockquery):
    def __init__(self, sessioncfg):
        QDialog.__init__(self)
        self.sessioncfg = sessioncfg

        self.siattr = ["market", "secu_name", "secu_code", "share_bln",
                "share_avl", "share_trd_frz", "share_otd",
                "share_frz", "share_untrade_qty", "current_cost",
                "mkt_val", "cost_price", "share_otd_avl", "curr_price",
                "cost2_price", "mkt_qty"]
        self.siattrmap = {
                "market":u"市场",
                "secu_name":u"名称",
                "secu_code":u"代码",
                "share_bln":u"余额",
                "share_avl":u"可用",
                "share_trd_frz":u"交易冻结",
                "share_otd":u"在途",
                "share_frz":u"异常冻结",
                "share_untrade_qty":u"非流通",
                "current_cost":u"当前成本",
                "mkt_val":u"市值",
                "cost_price":u"持仓成本",
                "share_otd_avl":u"在途可用",
                "curr_price":u"市价",
                "cost2_price":u"买入成本",
                "mkt_qty":u"拥股"
        }
        self.simodel = StockInfoModel(self.siattr, self.siattrmap, [])

    def setup(self):
        self.setupUi(self)

        self.stockinfo.setModel(self.simodel)

        self.session = jz.session(self.sessioncfg)
        if not self.session.setup():
            print "Cannot login"
            return False
        return True

    @pyqtSlot()
    def on_refresh_clicked(self):
        sreq = jz.StockQueryReq(self.session)
        sreq["user_code"] = self.session["user_code"]
        sreq.send()
        sresp = jz.StockQueryResp(self.session)
        sresp.recv()
        if sresp.retcode == "0":
            # update data and UI
            newdata = []
            for r in sresp.records:
                row = {}
                row["market"] = r[2]
                row["secu_name"] = r[4].decode("GBK")
                row["secu_code"] = r[5]
                row["share_bln"] = r[11]
                row["share_avl"] = r[12]
                row["share_trd_frz"] = r[13]
                row["share_otd"] = r[14]
                row["share_frz"] = r[15]
                row["share_untrade_qty"] = r[16]
                row["current_cost"] = r[17]
                row["mkt_val"] = r[24]
                row["cost_price"] = r[19]
                row["share_otd_avl"] = r[20]
                row["curr_price"] = r[21]
                row["cost2_price"] = r[22]
                row["mkt_qty"] = r[23]
                newdata.append(row)

            if len(self.simodel.data) > 0:
                self.simodel.beginRemoveRows(QModelIndex(), 0, len(self.simodel.data) - 1)
                del self.simodel.data[0:]
                self.simodel.endRemoveRows()

            if len(newdata) > 0:
                self.simodel.beginInsertRows(QModelIndex(), 0, len(newdata) - 1)
                self.simodel.data.extend(newdata)
                self.simodel.endInsertRows()

            self.stockinfo.resizeColumnsToContents()

        else:
            QMessageBox.information(None, "", u"刷新错误: " + sresp.retinfo)

    @pyqtSlot()
    def on_quit_clicked(self):
        self.session.close()
        self.done(0)

def main(args):
    # config
    app = QApplication(args)
    session_config = {}
    session_config["tradedbfn"] = "tradeinfo.db"
    session_config["jzserver"] = "172.18.20.52"
    session_config["jzport"] = 9100
    session_config["jzaccount"] = "85804530"
    session_config["jzaccounttype"] = "Z"
    session_config["jzpasswd"] = "123444"

    sqdlg = stockquerydlg(session_config)
    if sqdlg.setup():
        sqdlg.show()
        sqdlg.activateWindow()
        QMetaObject.invokeMethod(sqdlg.refresh, "clicked", Qt.QueuedConnection)
        app.exec_()
    else:
        QMessageBox.information(None, "", u"不能登录")


if __name__=="__main__":
    main(sys.argv)
