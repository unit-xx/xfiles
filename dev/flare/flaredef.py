# define constants for flare library

# namespace prefix, used in config parsing.
NSPREFIX = 'NS'
NSSEP = ':'
POSKEYSEP = '|'

# namespace definitions.
ORDERNS = 'ORDER'
TRADENS = 'TRADE'
POSITIONNS = 'POSITION'
PDEFNS = 'PTFDEF'
PINSTNS = 'PTFINST'

ALLORDER = 'ALLORDER'
ALLTRADE = 'ALLTRADE'
ALLPTFRE = 'ALLPTFRE'
ALLPTFNOM = 'ALLPTFNOM'

POSMAXNS = 'POSMAX'
STRATTBMAP = 'STRATTBMAP'

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

KOSTATE = 'OSTATE'
VORDERINIT = 'ORDERINIT'
VORDERREQED = 'ORDERREQED'
VORDERREJECTED = 'ORDERREJECTED'
VORDERACCEPTED = 'ORDERACCEPTED'
VORDERPTRADE = 'ORDERPTRADE'
VORDERFTRADE = 'ORDERFTRADE'

KCANCELSTATE = 'CANCELSTATE'
VCANCELINIT = 'CANCELINIT'
VCANCELREQED = 'CANCELREQED'
VCANCELREJECTED = 'CANCELREJECTED'
VCANCELLED = 'CANCELLED'

# trade
KTRADESTATE = 'TRADESTATE'
VTRADENEW = 'TRADENEW'

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
# need suffix :<tradingday>
FRONTIDKB = 'ALLFRONT'
SESSIONIDKB = 'ALLSESSION'

def fullname(*name)
    return NSSEP.join(name)

def splitname(name):
    return name.split(NSSEP)

def localoid():
    '''
    a UUID
    '''
    return ''

def poskey(code, dir):
    return POSKEYSEP.join( (code, dir) )

def splitposkey(poskey):
    return poskey.split(POSKEYSEP)
