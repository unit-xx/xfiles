import os
import logging, logging.config
import ConfigParser

import flaredef as fdef

# a global config variable accessed by:
# GCONFIG[NS:SECTION][KEY] = VALUE
GCONFIG = None

def parseconfig(name='config.ini', configpath='.'):
    global GCONFIG
    cfg = ConfigParser.ConfigParser()
    cfgfn = os.path.join(configpath, name)
    cfg.read(cfgfn)

    config = {}

    for sec in cfg.sections():
        if cfg.has_option(sec, fdef.NSPREFIX):
            namespace = getattr(fdef, cfg.get(sec, fdef.NSPREFIX))
            cfg.set(sec, fdef.NSPREFIX, namespace)
            csec = fdef.fullname(namespace, sec)
        else:
            csec = sec

        config[csec] = dict(cfg.items(sec))

    try:
        GCONFIG = config['GLOBAL']
    except KeyError:
        pass

    return config

def setuplogger(app, name='logger.ini', configpath='.'):
    cfgfn = os.path.join(configpath, name)
    logging.config.fileConfig(cfgfn, {"logfn":app+'.log'})
    logger = logging.getLogger()
    logger.info("========================")
    logger.info('%s is started!', app)

#def init_gconfig(config):
#    global GCONFIG
#    if GCONFIG is None:
#        GCONFIG = config
#        return True
#    else:
#        return False
# $Id$ 
