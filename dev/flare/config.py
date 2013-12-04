import os
import ConfigParser
import logging, logging.config
from collections import defaultdict

# a global config variable.
gconfig = defaultdict(defaultdict)

# gconfig is defaultdict of defaultdict
# CATALOG is defaultdict of dict
# NAME is dict

def parse_config(app, name='config.ini', configpath = '.'):
    '''
    section name has the format CATALOG:NAME, parsed result is accessed
    by gconfig.CATALOG.NAME.property
    '''

    global gconfig
    if gconfig is not None:
        return False

    cfg = ConfigParser.ConfigParser()
    cfgfn = os.path.join(configpath, name)
    cfg.read(cfgfn)

    for sec in cfg.sections():
        # use 'account.mduser1' as key or two-dim dict as ['account']['mduser1']
        pass

    logging.config.fileConfig(cfgfn, {"logfn":app+'.log'})
    logger = logging.getLogger()
    msg = "i'm started"
    logger.info("========================")
    logger.info(msg)

    gconfig = config

    return True
