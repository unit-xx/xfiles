# -*- coding: utf-8 -*-
import jz, jsd
import sys, csv
from stockqueryui import Ui_stockquery
import easytrader_lib
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from util import calsicontracts, incmonth
import datetime

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
    def __init__(self, sessioncfg, jsdcfg):
        QDialog.__init__(self)
        self.sessioncfg = sessioncfg
        self.jsdcfg = jsdcfg

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
            print "Cannot login jz"
            return False

        self.jsdsession = jsd.session(self.jsdcfg)
        if not self.jsdsession.setup():
            print "Cannot login jsd"
            return False

        return True

    def getaccinfo(self):
        # 股票：可用、市值、资产、可以建仓数
        # 期货：保证金、动态权益、持仓、支撑上涨比率

        # username
        self.accinfotext.append(QString("==== %s =====" % datetime.datetime.today().ctime()))
        self.accinfotext.append(QString(''))

        username = ""

        uireq = jz.UserInfoReq(self.session)
        uireq["user_code"] = self.session["user_code"]
        uireq.send()
        uiresp = jz.UserInfoResp(self.session)
        uiresp.recv()
        username = ""
        if uiresp.retcode == "0":
            username = uiresp.records[0]["USER_NAME"]#.decode("GBK")
        self.accinfotext.append(QString(u"用户：%s" % username))
        self.accinfotext.append(QString(u""))

        # current quote of HS300 and futures
        hs300q = 0.0
        ifq0 = 0.0
        ifq1 = 0.0

        sireq = jz.StockQuoteReq(self.session)
        sireq["market"] = jz.SHAMARKET
        sireq["secu_code"] = '000300'
        sireq.send()
        siresp = jz.StockQuoteResp(self.session)
        siresp.recv()
        if siresp.retcode == "0":
            hs300q = float(siresp.records[0]["ZJCJ"])

        sifc = calsicontracts()
        hqreq = jsd.QueryHQReq(self.jsdsession)
        hqreq["exchcode"] = self.jsdsession["cffexcode"]
        hqreq["code"] = sifc[0]
        hqreq.send()
        hqresp = jsd.QueryHQResp(self.jsdsession)
        hqresp.recv()
        if hqresp.anwser == "Y":
            ifq0 = float(hqresp.records[0][9])
        hqreq = jsd.QueryHQReq(self.jsdsession)
        hqreq["exchcode"] = self.jsdsession["cffexcode"]
        hqreq["code"] = sifc[1]
        hqreq.send()
        hqresp = jsd.QueryHQResp(self.jsdsession)
        hqresp.recv()
        if hqresp.anwser == "Y":
            ifq1 = float(hqresp.records[0][9])

        self.accinfotext.append(QString(u"行情："))
        self.accinfotext.append(QString(u"   HS300: %.2f %s: %.2f %s: %.2f" % (hs300q, sifc[0], ifq0, sifc[1], ifq1)))
        self.accinfotext.append(QString(u""))

        # stock capital
        stkcap = 0.0
        stkcash = 0.0
        stkmktval = 0.0
        openable = 0.0

        cqreq = jz.CapitalQueryReq(self.session)
        cqreq["user_code"] = self.session["user_code"]
        cqreq["currency"] = "0"#rmb
        cqreq.send()
        cqresp = jz.CapitalQueryResp(self.session)
        cqresp.recv()
        stkcap = 0.0
        if cqresp.retcode == "0":
            stkcap = float(cqresp.records[0]["ASSERT_VAL"])
            stkcash = float(cqresp.records[0]["AVAILABLE"])
            stkmktval = float(cqresp.records[0]["MKT_VAL"])
            openable = stkcash/300/hs300q

        self.accinfotext.append(QString(u"股票："))
        self.accinfotext.append(QString(u"    资产：%.2f 市值：%.2f 可用资金：%.2f 市值+可用：%.2f 可开手数：%.2f" % (stkcap, stkmktval, stkcash, stkmktval+stkcash, openable)))
        self.accinfotext.append(QString(u""))

        # futures
        tcinforeq = jsd.TradeCapInfoReq(self.jsdsession)
        tcinforeq.send()
        tcinforesp = jsd.TradeCapInfoResp(self.jsdsession)
        tcinforesp.recv()
        margin = 0.0
        fcash = 0.0
        gl = 0.0
        dynequity = 0.0
        uplimit0 = 0.0
        uplimit1 = 0.0
        if tcinforesp.anwser == "Y":
            resp = tcinforesp.records[0]
            margin = float(resp[21])
            fcash = float(resp[9])
            gl = float(resp[14])
            dynequity = float(resp[10])
            uplimit0 = (dynequity*hs300q/(stkcash+stkmktval)/ifq0 - 0.17)/1.17
            uplimit1 = (dynequity*hs300q/(stkcash+stkmktval)/ifq0 - 0.17)/1.17
        self.accinfotext.append(QString(u"期货："))
        self.accinfotext.append(QString(u"    保证金：%.2f 可用资金：%.2f 动态权益：%.2f" % (margin, fcash, dynequity)))
        self.accinfotext.append(QString(u"    支持%s上涨：%.2f%% 支持%s上涨：%.2f%%" % (sifc[0], uplimit0*100, sifc[1], uplimit1*100)))
        self.accinfotext.append(QString(u""))

        posreq = jsd.QueryPosReq(self.jsdsession)
        posreq.send()
        posresp = jsd.QueryPosResp(self.jsdsession)
        posresp.recv()
        pos ={}
        if posresp.anwser == "Y":
            for resp in posresp.records:
                code = resp[2]
                pos.setdefault(code, [0,0])
                if resp[4] != "":#long positions
                    pos[code][0] += int(resp[4])
                if resp[6] != "":#long positions
                    pos[code][1] += int(resp[6])
        self.accinfotext.append(QString(u"期货持仓："))
        for p in pos:
            self.accinfotext.append(QString(u"    代码：%s 买：%d 卖：%d" % (p, pos[p][0], pos[p][1])))
        self.accinfotext.append(QString(u""))


    @pyqtSlot()
    def on_refresh_clicked(self):
        self.getaccinfo()

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
                row["secu_name"] = r[4]
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
    def on_exportsellbtn_clicked(self):
        # export stocks for selling
        sifcode = unicode(self.sifcodeline.text())
        sifshare = unicode(self.sifshareline.text())
        ret = QMessageBox.information(None, "",
                u"对应期货：%s，手数：%s，确认？" % (sifcode, sifshare),
                QMessageBox.Ok|QMessageBox.Cancel)
        if QMessageBox.Ok != ret:
            return

        posfn = QFileDialog.getSaveFileName(self, u"", u"", u"*.pos")
        if posfn == "":
            return
        try:
            f = open(posfn, "wb")
            writer = csv.writer(f)

            if sifcode != "" and sifshare != "":
                sindexinfo = {}
                sindexinfo["code"] = sifcode

                sindexinfo["count"] = sifshare
                sindexinfo["state"] = easytrader_lib.Portfolio.IFOPENSHORTOK
                sindexinfo["pastopen"] = []
                r = easytrader_lib.SIndexRecord()
                r["order_id"] = "deadface"
                r["ordercount"] = sindexinfo["count"]
                r["openclose"] = "0"
                r["longshort"] = "1"
                r["ifhedge"] = "0"
                sindexinfo["pastopen"].append(r)
                sindexinfo["pastclose"] = []
                sindexinfo["deals"] = {}
                sindexinfo["deals"]["deadface"] = [(int(sindexinfo["count"]), 0.0)]

                writer.writerow(["IF", sindexinfo["code"], sindexinfo["count"],
                        sindexinfo["state"].encode("utf-8"),
                        repr(sindexinfo["pastopen"]),
                        repr(sindexinfo["pastclose"]),
                        repr(sindexinfo["deals"])])

            for row in self.simodel.data:
                if row["market"] == "10":
                    mkt = "SH"
                elif row["market"] == "00":
                    mkt = "SZ"
                else:
                    QMessageBox.information(None, "", u"不能识别的市场：%s,%s."
                            % (row["market"], row["secu_code"]))
                    continue

                code = row["secu_code"]
                count = row["share_avl"]
                if int(count) == 0:
                    continue

                pastbuy = []
                pastsell = []
                orec = easytrader_lib.OrderRecord()
                orec["ordercount"] = count
                orec["dealcount"] = count
                orec["order_state"] = easytrader_lib.Portfolio.BUYSUCCESS
                orec["dealprice"] = "0.0"
                orec["dealamount"] = "0.0"
                pastbuy.append(orec)

                writer.writerow([mkt, code, count,
                    repr(pastbuy), repr(pastsell)])
            writer.writerow(["BO",u"买入成功".encode("utf8")])
            f.flush()
            f.close()

        except IOError:
            QMessageBox.information(None, "", u"不能保存卖单.")

    @pyqtSlot()
    def on_quit_clicked(self):
        self.session.close()
        self.jsdsession.close()
        self.done(0)

def main(args):
    # config
    app = QApplication(args)
    session_config = {}
    session_config["tradedbfn"] = "tradeinfo.db"
    session_config["jzserver"] = ""
    session_config["jzport"] = 9100
    session_config["jzaccount"] = ""
    session_config["jzaccounttype"] = "Z"
    session_config["jzpasswd"] = ""

    jsdcfg = {}
    jsdcfg["tradedbfn"] = "tradeinfo.db"
    jsdcfg["jsdserver"] = ""
    jsdcfg["jsdport"] = 17990
    jsdcfg["jsdaccount"] = ""
    jsdcfg["cffexcode"] = "D"
    jsdcfg["branchcode"] = ""
    jsdcfg["ordermethod"] = ""
    jsdcfg["jsdpasswd"] = ""

    sqdlg = stockquerydlg(session_config, jsdcfg)
    if sqdlg.setup():
        sqdlg.show()
        sqdlg.activateWindow()
        QMetaObject.invokeMethod(sqdlg.refresh, "clicked", Qt.QueuedConnection)
        app.exec_()
    else:
        QMessageBox.information(None, "", u"不能登录")


if __name__=="__main__":
    main(sys.argv)
