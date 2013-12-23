# define constants for flare library

# namespace prefix, used in config parsing.
NSPREFIX = 'NS'
NSSEP = ':'
POSKEYSEP = '|'

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
KOID = 'OID'
KSTRAT = 'STRAT'
KCODE = 'CODE'
KVOLUME = 'VOLUME'
KTRADEVOL = 'KTRADEVOL'
KUNTRADEVOL = 'KUNTRADEVOL'
KPRICE = 'PRICE'
KISIOC = 'isIOC'
KTAG = 'TAG'
KISRESERVED = 'ISRESERVED'
KTRADE = 'TRADE'

KOTYPE = 'OTYPE'
VOPEN  = 'OPEN'
VCLOSE = 'CLOSE'

KACTION = 'OACTION'
VINSERT = 'INSERT'
VCANCEL = 'CANCEL'

KDIR = 'DIR'
VLONG = 'LONG'
VSHORT = 'SHORT'

KOSTATE
VORDERINIT
VORDERREQED
VORDERREJECTED
VORDERACCEPTED
VORDERPTRADE
VORDERFTRADE

KCANCELSTATE
VCANCELINIT
VCANCELREQED
VCANCELREJECTED
VCANCELLED

# trade
KTRADESTATE
VTRADENEW

KPTFID = 'PTFID'

KTXCOST = 'TXCOST'

# ptf keys
KACTIVEOID = 'KACTIVEOID'
KINACTIVEOIDS = 'KINACTIVEOIDS'

# position keys
KLONG = VLONG
KSHORT = VSHORT
KMAXLIMIT = 'MAXLIMIT'
KPOSITION = 'POSITION'
KRESERVED = 'RESERVED'
# TODO: how to calc margins for order with market price
KAVGPRICE = 'AVGPRICE'

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

def poskey(code, dir):
    return POSKEYSEP.join( (code, dir) )
