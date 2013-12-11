# define constants for flare library

# namespace prefix, used in config parsing.
NSPREFIX = 'NS'
NSSEP = ':'

# namespaces
ORDERNS = 'ORDER'
TRADENS = 'TRADE'
PDEFNS = 'PTFDEF'
PINSTNS = 'PTFINST'

# channels
CHQUOTE = 'CH:QUOTE'
CHOREQ = 'CH:OREQ'
CHORESP = 'CH:ORESP'

# order/ptf keys and constants, OK for order key, OV for order value
KTYPE = 'KTYPE'
VOPEN  = 'VOPEN'
VCLOSE = 'VCLOSE'
VCANCEL = 'VCANCEL'

KDIR = 'KDIR'
VLONG = 'VLONG'
VSHORT = 'VSHORT'

KOID = 'KOID'
KSTRAT = 'KSTRAT'
KPTFID = 'KPTFID'

KCODE = 'code'
KSHARE = 'share'
KTAG = 'tag'

# ptf definition keys

# global keys
ALLORDERS = 'ALLORDERS'
ALLTRADES = 'ALLTRADES'
ALLPTFRES = 'ALLPTFRES'
ALLPTFNOM = 'ALLPTFNOM'

# need suffix :<tradingday>
FRONTIDKB = 'ALLFRONT'
SESSIONIDKB = 'ALLSESSION'

def fullname(name, ns)
    return NSSEP.join( (ns, name) )

def splitname(name):
    return name.split(NSSEP)
