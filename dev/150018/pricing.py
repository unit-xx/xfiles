# pricing the option value for 150018

import sys
import ConfigParser

def value(a, b, m, u, sig, doy):
    a_t = a
    b_t = b
    m_t = m

    dt = 1.0 / doy

    while True:
        rday = mu * dt + sig * (dt**0.5) * random.gauss(0, 1)

def main():
    cfg = ConfigParser.ConfigParser()
    cfg.optionxform = str
    try:
        cfgfn = sys.argv[1]
    except IndexError:
        cfgfn = 'price.ini'

    cfg.read(cfgfn)

    param = dict(cfg.items('main'))

    v = value()

if __name__=='__main__':
    main()

# $Id$
