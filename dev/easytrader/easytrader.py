# -*- coding: utf-8 -*-

from easytrader_lib import *
import openptfdlg

PortfolioUpdater = PortfolioUpdater_dbf
#SIFPriceUpdater = SIFPriceUpdater_pushee
SIFPriceUpdater = SIFPriceUpdater_net

def main(args):
    #import psyco
    #psyco.full()

    # main initialization

    app = QApplication(args)
    # chdir to app's directory
    os.chdir(os.path.dirname(os.path.abspath(args[0])))
    # make log directory
    CONFIGFN = "easytrader.cfg"
    try:
        CONFIGFN = sys.argv[1]
    except IndexError:
        pass
    LOGDIR = "log"
    if not os.path.isdir(LOGDIR):
        try:
            os.mkdir(LOGDIR)
        except OSError as e:
            print "cannot make log directory: %d, %s." % (e.errno, e.strerror)
            QMessageBox.information(None, "", u"不能创建log目录: %d, %s" % (e.errno, e.strerror))
            sys.exit(1)

    logging.config.fileConfig(CONFIGFN)
    logger = logging.getLogger()
    msg = "i'm started"
    logger.info("========================")
    logger.info(msg)

    # read config
    JZSEC = "jz"
    JSDSEC = "jsd"
    MYSEC = "easytrader"

    config = ConfigParser.RawConfigParser()
    config.read(CONFIGFN)

    session_config = {}
    for k,v in config.items(JZSEC):
        session_config[k] = v
    try:
        session_config["jzport"] = int(session_config["jzport"])
    except KeyError:
        pass

    # get jsd session config
    jsd_sessioncfg = {}
    for k,v in config.items(JSDSEC):
        jsd_sessioncfg[k] = v
    try:
        jsd_sessioncfg["jsdport"] = int(jsd_sessioncfg["jsdport"])
    except KeyError:
        pass

    # show config in dialog
    from logindiag import logindlg
    d = logindlg(session_config, jsd_sessioncfg)
    d.show()
    d.activateWindow()
    d.exec_()
    if d.status == False:
        logger.info("User cancel login")
        sys.exit(1)

    session_config.update(d.jzconfig)
    jsd_sessioncfg.update(d.jsdconfig)

    testsession = jz.session(session_config)
    loginok = True
    if not testsession.setup():
        loginok = False
        logger.warning("Cannot login jz.")
        QMessageBox.warning(None,
                u"",
                u"<H3><FONT COLOR='#FF0000'>金证系统不能登录！</FONT></H3>",
                QMessageBox.Ok)
    testsession.close()
    if not loginok:
        sys.exit(1)

    testsession = jsd.session(jsd_sessioncfg)
    loginok = True
    if not testsession.setup():
        loginok = False
        logger.warning("Cannot login jsd.")
        QMessageBox.warning(None,
                u"",
                u"<H3><FONT COLOR='#FF0000'>金士达系统不能登录！</FONT></H3>",
                QMessageBox.Ok)
    testsession.close()
    if not loginok:
        sys.exit(1)

    # verify stock mapping
    shdbfn = session_config["shdbfn"]
    szdbfn = session_config["szdbfn"]
    shmapfn = "shmap.pkl"
    szmapfn = "szmap.pkl"
    if not verifymap(shdbfn, shmapfn, "S1"):
        logger.warning("SH stock map file error.")
        sys.exit(1)
    if not verifymap(szdbfn, szmapfn, "HQZQDM"):
        logger.warning("SZ stock map file error.")
        sys.exit(1)

    # save config
    #for k in session_config:
    #    config.set("easytrader", k, session_config[k])
    #config.write(configfn)

    #load portfolio
    #portfoliofn = unicode(QFileDialog.getOpenFileName(None, u"选择投资组合", "./portfolio", "*.ptf"))
    username = ""
    testsession = jz.session(session_config)
    if testsession.setup():
        uireq = jz.UserInfoReq(testsession)
        uireq["user_code"] = testsession["user_code"]
        uireq.send()
        uiresp = jz.UserInfoResp(testsession)
        uiresp.recv()
        if uiresp.retcode == "0":
            username = uiresp.records[0][0].decode("GBK")
        testsession.close()
    if username == "":
        QMessageBox.warning(None,
                u"",
                u"<H3><FONT COLOR='#FF0000'>不能取得用户资料！</FONT></H3>",
                QMessageBox.Ok)
        logger.warning("cannot get user name")
        sys.exit(1)

    ptfdlg = openptfdlg.openptfdlg("portfolio", username)
    if ptfdlg.setup():
        ptfdlg.show()
        ptfdlg.activateWindow()
        app.exec_()

    portfoliofn = ptfdlg.selectedfn

    if portfoliofn == u"":
        logger.info("No portfolio seleted.")
        sys.exit(1)

    # TODO: lock portfolio file to be used by one instance of easytrader
    updtlock = Lock()
    # setup portfolio
    tqueue = Queue.Queue()
    p = Portfolio(portfoliofn, session_config, tqueue, updtlock, jsd_sessioncfg)
    p.loadPortfolio()

    # setup portfolio model for showing in table
    pmodel = PortfolioModel(p)
    sindexmodel = StockIndexModel(p)

    # run the portfolio updater
    pupdater = PortfolioUpdater(shdbfn, shmapfn, szdbfn, szmapfn, p, pmodel)
    #pupdater = PortfolioUpdater("172.30.4.165", 21888, p, pmodel)
    pupdater.start()

    # run SecuInfoUpdater
    siupdter = SecuInfoUpdater(p, pmodel, session_config)
    siupdter.start()

    # run the order info updater
    orderupdater = OrderUpdater(p, pmodel, session_config, updtlock)
    orderupdater.start()

    coupdater = CancelOrderUpdater(p, pmodel, session_config)
    coupdater.start()

    # setup dbqueue and dbserver
    dbqueue = Queue.Queue()
    dbname = config.get(MYSEC, "tradedb")
    dbs = dbserver(dbname, dbqueue)
    dbs.start()

    # setup and run jzWorker threads
    jzWorkerNum = 10
    try:
        jzWorkerNum = config.getint(MYSEC, "jzworkernum")
    except Exception:
        pass

    workers = []
    for i in range(jzWorkerNum):
        w = jzWorker(session_config, tqueue, dbqueue)
        workers.append(w)

    for i in range(jzWorkerNum):
        workers[i].start()

    # main window
    uic = uicontrol(session_config, p, pmodel, sindexmodel)
    uic.setup()

    # start stock index price updater
    #sifupdter = SIFPriceUpdater(p, sindexmodel, jsd_sessioncfg, uic)
    #sifupdter.start()
    servhost = config.get(MYSEC, "sindexhqservhost")
    servport = config.getint(MYSEC, "sindexhqservport")
    sifupdter = SIFPriceUpdater(servhost, servport, p, sindexmodel, uic)
    sifupdter.start()


    # start SIFOrderPushee
    sifop = SIFOrderPushee(p, sindexmodel, jsd_sessioncfg)
    sifop.start()

    # start base diff updater
    bdiffupdter = basediffUpdater(pupdater, jsd_sessioncfg, uic)
    bdiffupdter.start()

    uic.show()
    app.exec_()

    # exit process
    logger.info("waiting basediffUpdater to stop")
    bdiffupdter.stop()
    bdiffupdter.join()

    logger.info("waiting SIFPriceUpdater to stop")
    sifupdter.stop()
    sifupdter.join()

    logger.info("waiting SIFOrderPushee to stop")
    sifop.stop()
    sifop.join()

    logger.info("notify updater threads to stop.")
    pupdater.stop()
    orderupdater.stop()
    coupdater.stop()
    logger.info("waiting updater threads to stop.")
    pupdater.join()
    orderupdater.join()
    coupdater.join()
    logger.info("updater threads stopped.")

    logger.info("waiting SecuInfoUpdater to stop")
    siupdter.stop()
    siupdter.join()

    logger.info("waiting jzWorkers to finalize jobs")
    # next line ensures all async request will be executed before exit.
    tqueue.join()
    for i in range(jzWorkerNum):
        workers[i].stop()
    for i in range(jzWorkerNum):
        workers[i].join()
    logger.info("jzWorkers stopped")

    logger.info("waiting dbserver to stop")
    dbqueue.join()
    dbs.stop()
    dbs.join()

    logger.info("saving order info.")
    p.savePortfolio()
    p.close()
    logger.info("I will exit.")

if __name__=="__main__":
    main(sys.argv)


