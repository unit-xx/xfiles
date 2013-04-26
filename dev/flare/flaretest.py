import time

import flare_lib
import util
import logging

INSTS = [
         u'IF1305',u'IF1306',
        ]

cfg = util.parse_config()

q = flare_lib.qserver(INSTS, cfg.mduser)
q.setup()

while 1:
    time.sleep(1)
