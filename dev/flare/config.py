import os
import logging, logging.config
import configparser
from collections import defaultdict

from util import Record

# a global config variable.
gconfig = None

# gconfig is defaultdict of defaultdict
# CATALOG is defaultdict of dict
# NAME is dict

def parseconfig(name='config.ini', configpath = '.'):
    '''
    section name has the format CATALOG:NAME, parsed result is accessed
    by gconfig.CATALOG.NAME.property
    '''

    cfg = configparser.ConfigParser(dict_type=Record,
            interpolation=configparser.ExtendedInterpolation())
    cfgfn = os.path.join(configpath, name)
    cfg.read(cfgfn)

    for sec in cfg.sections():
        # use 'account.mduser1' as key or two-dim dict as ['account']['mduser1']
        pass

    return cfg


def setuplogger(app, name='logger.ini', configpath = '.'):
    cfgfn = os.path.join(configpath, name)
    logging.config.fileConfig(cfgfn, {"logfn":app+'.log'})
    logger = logging.getLogger()
    logger.info("========================")
    logger.info('%s is started!', app)

if gconfig is None:
    gconfig 
