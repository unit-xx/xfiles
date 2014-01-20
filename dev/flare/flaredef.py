import uuid
# define constants for flare library

# namespace prefix, used in config parsing.
NSPREFIX = 'NS'
NSSEP = ':'
POSKEYSEP = '|'

# namespace definitions.
ACCOUNTNS = 'ACCOUNT'
QUOTENS = 'QUOTE'
ORDERNS = 'ORDER'
TRADENS = 'TRADE'
POSITIONNS = 'POSITION'
PDEFNS = 'PTFDEF'
PINSTNS = 'PTFINST'

ALLORDER = 'ALLORDER'
ALLTRADE = 'ALLTRADE'
ALLPOS = 'ALLPOS'
ALLPTFRE = 'ALLPTFRE'
ALLPTFNOM = 'ALLPTFNOM'

POSMAXNS = 'POSMAX'
TB2STRATMAP = 'TB2STRAT'

# channels
CHQUOTE = 'CHQUOTE'
CHOREQ = 'CHOREQ'
CHORESP = 'CHORESP'
# TBook update notification
CHNTFTBOOK = 'CHNTFTBOOK'
# Heartbeat channel
CHHEARTBEAT = 'HEARTBEAT'

# order keys and constants, K for order key, V for order value
KOID = 'OID'
KSTRAT = 'STRAT'
KORDERDATE = 'ORDERDATE'
KCODE = 'CODE'
KVOLUME = 'VOLUME'
KTRADEVOL = 'TRADEVOL'
KUNTRADEVOL = 'UNTRADEVOL'
KPRICE = 'PRICE'
KISIOC = 'isIOC'
KTAG = 'TAG'
KISRESERVED = 'ISRESERVED'
KTRADE = 'TRADE'

KOTYPE = 'OTYPE'
VOPEN = 'OPEN'
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
KACTIVEOID = 'ACTIVEOID'
KINACTIVEOIDS = 'INACTIVEOIDS'

# position keys
KPOSKEY = 'POSKEY'
KLONG = VLONG
KSHORT = VSHORT
KMAXLIMIT = 'MAXLIMIT'
KPOSITION = 'POSITION'
KRESERVEDOPEN = 'RESERVEDOPEN'
KRESERVEDCLOSE = 'RESERVEDCLOSE'
# TODO: how to calc margins for order with market price
KAVGPRICE = 'AVGPRICE'

# TBookProxy command
CMDNEWORDER = 'CMDNEWORDER'
CMDUPDATEORDER = 'CMDUPDATEORDER'
CMDADDTRADE = 'CMDADDTRADE'
CMDNEWPOSITION = 'CMDNEWPOSITION'
CMDUPDATEPOS = 'CMDUPDATEPOS'

# UI refresh command
CMDUI = 'CMDUI'

# global keys
# need suffix :<tradingday>
FRONTIDKB = 'ALLFRONT'
SESSIONIDKB = 'ALLSESSION'

def fullname(*name):
    return NSSEP.join(name)

def splitname(name):
    return name.split(NSSEP)

def localoid():
    '''
    a UUID
    '''
    return uuid.uuid1().hex

def genposkey(code, direction):
    return POSKEYSEP.join((code, direction))

def splitposkey(poskey):
    return poskey.split(POSKEYSEP)
# $Id$ 
