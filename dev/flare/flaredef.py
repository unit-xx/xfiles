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
CHQUOTE = 'CHQUOTE'
CHOREQ = 'CHOREQ'
CHORESP = 'CHORESP'

# order keys and constants, K for order key, V for order value
KOTYPE = 'OTYPE'
VOPEN  = 'OPEN'
VCLOSE = 'CLOSE'

KACTION = 'OACTION'
VINSERT = 'INSERT'
VCANCEL = 'CANCEL'

KDIR = 'DIR'
VLONG = 'LONG'
VSHORT = 'SHORT'

KOID = 'OID'
KSTRAT = 'STRAT'
KPTFID = 'PTFID'

KOSTATE
VORDERREQED
VORDERREJECTED
VORDERACCEPTED
VORDERPTRADE
VORDERFTRADE

KTRADESTATE
VTRADENEW

KCANCELSTATE
VCANCELREQED
VCANCELREJECTED
VCANCELLED

# volume
KTRADEVOL
KUNTRADEVOL

KCODE = 'CODE'
KVOLUME = 'VOLUME'
KPRICE = 'PRICE'
KISIOC = 'isIOC'
KTAG = 'TAG'
KTXCOST = 'TXCOST'

# ptf keys
KACTIVEOID = 'KACTIVEOID'
KINACTIVEOIDS = 'KINACTIVEOIDS'

# position keys
KLONG = 'LONG'
KSHORT = 'SHORT'

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

def localoid():
    return ''

