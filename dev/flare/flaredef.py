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
KTYPE = 'KTYPE'
VOPEN  = 'VOPEN'
VCLOSE = 'VCLOSE'

KACTION
VINSERT
VCANCEL = 'VCANCEL'

KDIR = 'KDIR'
VLONG = 'VLONG'
VSHORT = 'VSHORT'

KOID = 'KOID'
KSTRAT = 'KSTRAT'
KPTFID = 'KPTFID'

KOSTATE
VORDERREQED
VORDERREJECTED
VORDERACCEPTED
VORDERPTRADE
VORDERFTRADE

KCANCELSTATE
VCANCELREQED
VCANCELREJECTED
VCANCELLED

# ptf keys
KCODE = 'code'
KSHARE = 'share'
KTAG = 'tag'
KACTIVEOID
KINACTIVEOIDS

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
