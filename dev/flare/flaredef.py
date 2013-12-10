# define constants for flare library

# namespace prefix, used in config parsing.
NSPREFIX = 'NS'
NSSEP = ':'

# namespaces
ORDERNS = 'ORDER'
TRADENS = 'TRADE'
PTFNOMNS = 'PTFNOM'
PTFRENS = 'PTFRE'
ORD2TRDNS = 'ORD2TRD'
QUOTE = 'QUOTE'
ACCOUNT = 'ACCOUNTxxx'

# ptf definition keys
CODE = 'code'
SHARE = 'share'
TAG = 'tag'

# global keys
ALLORDERS = 'ALLORDERS'
ALLTRADES = 'ALLTRADES'
ALLPTFRES = 'ALLPTFRES'
ALLPTFNOM = 'ALLPTFNOM'

# need suffix :<tradingday>
FRONTIDKB = 'ALLFRONT'
SESSIONIDKB = 'ALLSESSION'

def fullname(name, prefix, suffix):
    return NSSEP.join( (prefix, name, suffix) )
