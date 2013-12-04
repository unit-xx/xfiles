import os
import ConfigParser
import logging, logging.config

from util import Record

# a global config variable.
gconfig = None

def parse_config(app, name='config.ini', root='base', configpath = '.'):
    '''
    section name has the format CATALOG:NAME, parsed result is accessed
    by config.CATALOG.NAME.property
    '''
    global gconfig

    cfg = ConfigParser.ConfigParser()
    cfgfn = os.path.join(configpath, name)
    cfg.read(cfgfn)
    config = BaseObject(mduser={},trader={},redis={})
    usersec = cfg.get(root,'mduser')
    tradersec = cfg.get(root,'trader')
    redissec = cfg.get(root, 'redis')
    maparamsec = cfg.get(root, 'maparam')
    mmparamsec = cfg.get(root, 'mmparam')

    mduser = BaseObject()
    mduser.port = cfg.get(usersec,'port')
    mduser.broker_id = cfg.get(usersec,'broker_id')
    mduser.investor_id = cfg.get(usersec,'investor_id')
    mduser.passwd = cfg.get(usersec,'passwd')
    config.mduser = mduser

    trader = BaseObject()
    trader.port = cfg.get(tradersec,'port')
    trader.broker_id = cfg.get(tradersec,'broker_id')
    trader.investor_id = cfg.get(tradersec,'investor_id')
    trader.passwd = cfg.get(tradersec,'passwd')
    trader.tpoolcap = cfg.get(tradersec, 'tpoolcap')
    config.trader = trader

    redis = BaseObject()
    redis.host = cfg.get(redissec, 'host')
    redis.port = cfg.getint(redissec, 'port')
    redis.repodb = cfg.getint(redissec, 'repodb')
    redis.accountdb = cfg.getint(redissec, 'accountdb')
    redis.qchannel = cfg.get(redissec, 'qchannel')
    redis.machannel = cfg.get(redissec, 'machannel')
    config.redis = redis

    maparam = BaseObject()
    maparam.step = cfg.getint(maparamsec, 'step')
    maparam.wsize = cfg.getint(maparamsec, 'wsize')
    maparam.bufmax = cfg.getint(maparamsec, 'bufmax')
    config.maparam = maparam

    mmparam = BaseObject()
    mmparam.sigma = cfg.getfloat(mmparamsec, 'sigma')
    mmparam.t = cfg.getfloat(mmparamsec, 't')
    mmparam.qmax = cfg.getint(mmparamsec, 'qmax')
    config.mmparam = mmparam

    logging.config.fileConfig(cfgfn, {"logfn":app+'.log'})
    logger = logging.getLogger()
    msg = "i'm started"
    logger.info("========================")
    logger.info(msg)

    gconfig = config

