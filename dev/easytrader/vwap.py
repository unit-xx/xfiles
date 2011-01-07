import sys
import time
import datetime
import socket
import zlib
import pickle
from struct import unpack

HOST, PORT = "172.30.4.98", 22888
TARGET = "1101"

pv = [] # price, volume, p*v
lastdv = 0

maxqlen = [int(x) for x in sys.argv[1:]]
maxqlen.sort(reverse=True)
volsum = [0 for x in maxqlen]
weightpsum = [0.0 for x in maxqlen]
awp = [0.0 for x in maxqlen]


"""
1. read a quote to setup lastdv
2. accumulate until enough quotes
3. update by minus oldest quote and add latest quote
"""

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server and send data
sock.connect((HOST, PORT))

def recv_n(conn, n):
    left = n
    content = []
    while 1:
        if left <= 0:
            break
        buf = conn.recv(left)
        content.append(buf)
        left = left - len(buf)

    return "".join(content)

oktowhile = True
while oktowhile:
    (pktlen,) = unpack("!I", sock.recv(4))
    received = recv_n(sock, pktlen)
    price = pickle.loads(zlib.decompress(received))
    for qd in price:
        if qd.varity_code == "IF" and qd.deliv_date == TARGET:
            lastdv = qd.doneVolume
            oktowhile = False
            break

oktowhile = True
while oktowhile:
    (pktlen,) = unpack("!I", sock.recv(4))
    received = recv_n(sock, pktlen)
    price = pickle.loads(zlib.decompress(received))
    for qd in price:
        if qd.varity_code == "IF" and qd.deliv_date == TARGET:
            v = qd.doneVolume - lastdv
            p = qd.lastPrice
            pv.append((p, v, p*v))
            lastdv = qd.doneVolume

            if len(pv) == maxqlen[0]:# the largest length
                for i, qlen in enumerate(maxqlen):
                    volsum[i] = sum([x[1] for x in pv[-qlen:]])
                    weightpsum[i] = sum([x[2] for x in pv[-qlen:]])
                oktowhile = False
                break
print pv
print volsum, weightpsum

while 1:
    (pktlen,) = unpack("!I", sock.recv(4))
    received = recv_n(sock, pktlen)
    price = pickle.loads(zlib.decompress(received))
    for qd in price:
        if qd.varity_code == "IF" and qd.deliv_date == TARGET:
            v = qd.doneVolume - lastdv
            p = qd.lastPrice
            lastdv = qd.doneVolume

            for i, qlen in enumerate(maxqlen):
                try:
                    volsum[i] = volsum[i] + v - pv[-qlen][1]
                    #print "vol add %d, minus %d" % (v, pv[-qlen][1])
                    weightpsum[i] = weightpsum[i] + p*v - pv[-qlen][2]
                    #print "weightpsum add %.2f, minus %.2f" % (p*v, pv[-qlen][2])
                    #print volsum, weightpsum

                    awp[i] = weightpsum[i]/volsum[i]

                    if len(pv) > 30*maxqlen:
                        del pv[0:-maxqlen]
                except ZeroDivisionError:
                    awp[i] = qd.lastPrice

            pv.append((p, v, p*v))
            print qd.sys_recv_time, ["%.1f"%x for x in awp], ["%.1f"%(qd.lastPrice-x) for x in awp], "%.1f"%qd.lastPrice#, volsum
