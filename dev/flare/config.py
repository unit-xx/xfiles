import os
import logging, logging.config
import ConfigParser

from util import Record
import flaredef as fdef

# a global config variable.
# gconfig[NS:SECTION][KEY] = VALUE
gconfig = None

# gconfig is defaultdict of defaultdict
# CATALOG is defaultdict of dict
# NAME is dict

# namespace prefix: NS:xxx
# setting in a namespace: NS:xxx:yyy

def parseconfig(name='config.ini', configpath = '.'):
    '''
    section name has the format CATALOG:NAME, parsed result is accessed
    by gconfig.CATALOG.NAME.property
    '''

    cfg = ConfigParser.ConfigParser()
    cfgfn = os.path.join(configpath, name)
    cfg.read(cfgfn)

    config = dict()

    for sec in cfg.sections():
        if cfg.has_option(sec, fdef.NSPREFIX):
            namespace = getattr(fdef, cfg.get(sec, fdef.NSPREFIX))
            cfg.set(sec, fdef.NSPREFIX, namespace)
            csec = fdef.NSSEP.join((namespace, sec))
        else:
            csec = sec

        config[csec] = dict(cfg.items(sec))

    return config

def setuplogger(app, name='logger.ini', configpath = '.'):
    cfgfn = os.path.join(configpath, name)
    logging.config.fileConfig(cfgfn, {"logfn":app+'.log'})
    logger = logging.getLogger()
    logger.info("========================")
    logger.info('%s is started!', app)

def init_gconfig(config):
    global gconfig
    if gconfig is None:
        gconfig = config
        return True
    else:
        return False
