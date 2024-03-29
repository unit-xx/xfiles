# -*- coding: utf-8 -*-

from easytrader_lib import *

PortfolioUpdater = PortfolioUpdater_net
SIFPriceUpdater = SIFPriceUpdater_net

def main(args):
    #import psyco
    #psyco.full()

    # main initialization

    app = QApplication(args)
    # chdir to app's directory
    os.chdir(os.path.dirname(os.path.abspath(args[0])))
    # make log directory
    CONFIGFN = "itrader.cfg"
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
    MYSEC = "itrader"

    session_config = {}
    config = ConfigParser.RawConfigParser()
    config.read(CONFIGFN)
    for k,v in config.items(JZSEC):
        session_config[k] = v
    try:
        session_config["jzport"] = int(session_config["jzport"])
    except KeyError:
        pass

    # show config in dialog
    from ilogindiag import logindlg
    d = logindlg(session_config)
    d.show()
    d.activateWindow()
    d.exec_()
    if d.status == False:
        logger.info("User cancel login")
        sys.exit(1)

    session_config.update(d.config)
    testsession = jz.session(session_config)
    if not testsession.setup():
        logger.warning("Cannot login jz.")
        QMessageBox.warning(None,
                u"",
                u"<H3><FONT COLOR='#FF0000'>金证系统不能登录，勿进行股票操作！</FONT></H3>",
                QMessageBox.Ok)
    testsession.close()

    # save config
    #for k in session_config:
    #    config.set("easytrader", k, session_config[k])
    #config.write(configfn)

    #load portfolio
    portfoliofn = unicode(QFileDialog.getOpenFileName(None, u"选择投资组合", "./portfolio", "*.ptf"))
    if portfoliofn == u"":
        logger.info("No portfolio seleted.")
        sys.exit(1)

    # get jsd session config
    jsd_sessioncfg = {}
    for k,v in config.items(JSDSEC):
        jsd_sessioncfg[k] = v
    try:
        jsd_sessioncfg["jsdport"] = int(jsd_sessioncfg["jsdport"])
    except KeyError:
        pass
    testsession = jsd.session(jsd_sessioncfg)
    if not testsession.setup():
        logger.warning("Cannot login jsd.")
        QMessageBox.warning(None,
                u"",
                u"<H3><FONT COLOR='#FF0000'>金士达系统不能登录，勿进行股指期货操作！</FONT></H3>",
                QMessageBox.Ok)
    testsession.close()

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
    servhost = config.get(MYSEC, "stockhqservhost")
    servport = config.getint(MYSEC, "stockhqservport")
    pupdater = PortfolioUpdater(servhost, servport, p, pmodel)
    pupdater.start()

    # run the order info updater
    orderupdater = OrderUpdater(p, pmodel, session_config, updtlock)
    orderupdater.start()

    # setup and run jzWorker threads
    jzWorkerNum = 10
    workers = []
    for i in range(jzWorkerNum):
        w = jzWorker(session_config, tqueue)
        workers.append(w)

    for i in range(jzWorkerNum):
        workers[i].start()

    # main window
    window = QMainWindow()
    uic = uicontrol(window, session_config, p, pmodel, sindexmodel)
    uic.setup()

    # start stock index price updater
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

    window.show()
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
    logger.info("waiting updater threads to stop.")
    pupdater.join()
    orderupdater.join()
    logger.info("updater threads stopped.")
    logger.info("waiting jzWorkers to finalize jobs")
    # next line ensures all async request will be executed before exit.
    tqueue.join()
    for i in range(jzWorkerNum):
        workers[i].stop()
    for i in range(jzWorkerNum):
        workers[i].join()
    logger.info("jzWorkers stopped")
    logger.info("saving order info.")
    p.savePortfolio()
    p.close()
    logger.info("I will exit.")

if __name__=="__main__":
    main(sys.argv)


