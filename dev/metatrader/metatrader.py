# -*- coding: utf-8 -*-

from metatrader_lib import *
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
    CONFIGFN = "metatrader.cfg"
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

    # read config
    JZSEC = "jz"
    JSDSEC = "jsd"
    HSSEC = 'hs'
    MYSEC = "metatrader"

    config = ConfigParser.RawConfigParser()
    config.read(CONFIGFN)

    hscfg = {}
    for k,v in config.items(HSSEC):
        hscfg[k] = v
    hscfg["hsport"] = int(hscfg["hsport"])
    hscfg["protocol"] = int(hscfg["protocol"])
    hscfg["keyciper"] = int(hscfg["keyciper"])

    try:
        hscfg["usebatch"] = int(hscfg["usebatch"])
    except KeyError:
        hscfg["usebatch"] = 0
    try:
        hscfg["useboundprice"] = int(hscfg["useboundprice"])
    except KeyError:
        hscfg["useboundprice"] = 0

    testsession = hs.session(hscfg)
    loginok = True
    username = 'anonymous'
    if not testsession.setup():
        loginok = False
        QMessageBox.warning(None,
                u"",
                u"<H3><FONT COLOR='#FF0000'>恒生系统不能登录！</FONT></H3>",
                QMessageBox.Ok)
    else:
        username = testsession['client_name']
    testsession.close()
    if not loginok:
        sys.exit(1)

    # verify stock mapping
    shdbfn = hscfg["shdbfn"]
    szdbfn = hscfg["szdbfn"]
    shmapfn = "shmap.pkl"
    szmapfn = "szmap.pkl"
    if not verifymap(shdbfn, shmapfn, "S1"):
        #logger.warning("SH stock map file error.")
        sys.exit(1)
    if not verifymap(szdbfn, szmapfn, "HQZQDM"):
        #logger.warning("SZ stock map file error.")
        sys.exit(1)

    # save config
    #for k in hscfg:
    #    config.set("easytrader", k, hscfg[k])
    #config.write(configfn)

    #load portfolio
    #portfoliofn = unicode(QFileDialog.getOpenFileName(None, u"选择投资组合", "./portfolio", "*.ptf"))

    ptfdlg = openptfdlg.openptfdlg("portfolio", username)
    if ptfdlg.setup():
        ptfdlg.show()
        ptfdlg.activateWindow()
        app.exec_()

    portfoliofn = ptfdlg.selectedfn
    portfoliobasefn = os.path.basename(portfoliofn)[0:-4]
    opennew = ptfdlg.opennew

    if portfoliofn == u"":
        #logger.info("No portfolio seleted.")
        sys.exit(1)

    # TODO: lock portfolio file to be used by one instance of easytrader
    updtlock = Lock()
    # setup portfolio
    tqueue = Queue.Queue()
    p = Portfolio(portfoliofn, hscfg, tqueue, updtlock, jsd_sessioncfg)
    p.loadPortfolio()

    # setup portfolio model for showing in table
    pmodel = PortfolioModel(p)
    sindexmodel = StockIndexModel(p)

    pstat = PortfolioStat()
    pstat.ptfname = portfoliobasefn
    pstat.username = username

    # main window
    uic = uicontrol(hscfg, jsd_sessioncfg, p, pmodel, sindexmodel, opennew)
    uic.setup()

    # setup logging
    logfn = u"log/metatrader-%s-%s.log" % (username, portfoliobasefn)
    p.logfn = logfn
    logging.config.fileConfig(CONFIGFN, {"logfn":logfn.encode("gbk")})
    logger = logging.getLogger()
    msg = "i'm started"
    logger.info("========================")
    logger.info(msg)

    # run the portfolio updater
    pupdater = PortfolioUpdater(shdbfn, shmapfn, szdbfn, szmapfn, p, pmodel)
    #pupdater = PortfolioUpdater("172.30.4.165", 21888, p, pmodel)
    pupdater.start()

    # run SecuInfoUpdater
    siupdter = SecuInfoUpdater(p, pmodel, hscfg)
    siupdter.start()

    # run the order info updater
    orderupdater = OrderUpdater(p, pmodel, hscfg, updtlock)
    orderupdater.start()

    coupdater = CancelOrderUpdater(p, pmodel, hscfg)
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
        w = jzWorker(hscfg, tqueue, dbqueue)
        workers.append(w)

    for i in range(jzWorkerNum):
        workers[i].start()

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
    bdiffupdter = basediffUpdater(pupdater, jsd_sessioncfg, uic, pstat)
    bdiffupdter.start()

    # stock stats collector
    ssu = StockStatUpdater(uic, p, pstat)
    ssu.start()

    # connect to controller
    caddr = config.get(MYSEC, "controlleraddr")
    cport = config.getint(MYSEC, "controllerport")
    client = trdClient(caddr, cport, pstat, uic)
    client.start()

    # sif updater for quick submit
    sifuq = SIFOrderUpdaterQ(p, jsd_sessioncfg, uic)
    sifuq.start()

    uic.show()
    app.exec_()

    # exit process
    sifuq.stop()

    client.stop()
    client.join()

    ssu.stop()
    ssu.join()

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


