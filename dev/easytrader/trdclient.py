# -*- coding: utf-8 -*-

import socket
import pickle
import time
from struct import pack

import util

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect( ("127.0.0.1", 38888) )

cmd = util.command()
cmd.cmdname = "register"
cmd.args = [u"我", "2003315434.pos", "127.0.0.1", 1234]
msg = pickle.dumps(cmd, -1)
msglen = len(msg)
s.sendall(pack("!I", msglen))
s.sendall(msg)

time.sleep(1)
