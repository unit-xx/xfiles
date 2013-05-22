import os
import ConfigParser
import logging, logging.config

class BaseObject:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __setattr__(self, attr_name, value):
        self.__dict__[attr_name] = value

    def __repr__(self):
        return str(self.__dict__)

def parse_config(app, name='config.ini', root='base', configpath = '.'):
    cfg = ConfigParser.ConfigParser()
    cfgfn = os.path.join(configpath, name)
    cfg.read(cfgfn)
    config = BaseObject(mduser={},trader={},redis={})
    usersec = cfg.get(root,'mduser')
    tradersec = cfg.get(root,'trader')
    redissec = cfg.get(root, 'redis')

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
    config.redis = redis

    logging.config.fileConfig(cfgfn, {"logfn":app+'.log'})
    logger = logging.getLogger()
    msg = "i'm started"
    logger.info("========================")
    logger.info(msg)

    return config


