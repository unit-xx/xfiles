import socket
import pickle, zlib
import datetime
from struct import unpack
from util import recv_n

sifindex = ["1111","1112","1203"]
sifweight = [-3,4,-1]
sifpricebuy = [0.0]*len(sifindex)
sifpricesell = [0.0]*len(sifindex)
siflcbuy = 0.0
siflcsell = 0.0
LOW = 3.0
HIGH = 10.0

HOST, PORT = "172.30.4.93", 22888
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

while 1:
    #print 'get len'
    tmp = recv_n(sock, 4)
    (pktlen,) = unpack("!I", tmp)
    #print 'get data'
    received = recv_n(sock, pktlen)
    assert len(received) == pktlen
    price = pickle.loads(zlib.decompress(received))
    #print "Received: %s" % len(price)
    for qd in price:
        if qd.deliv_date in sifindex:
            pa = float(qd.askPrice1)
            pb = float(qd.bidPrice1)
            i = sifindex.index(qd.deliv_date)
            if sifweight[i] < 0:
                sifpricebuy[i] = pb
                sifpricesell[i] = pa
            else:
                sifpricebuy[i] = pa
                sifpricesell[i] = pb

            siflcbuy = sum([sifweight[i]*sifpricebuy[i] for i in range(len(sifindex))])
            siflcsell = sum([sifweight[i]*sifpricesell[i] for i in range(len(sifindex))])
            print str(datetime.datetime.now()), qd.sys_recv_time, "%.1f"%siflcbuy, "%.1f"%siflcsell, "%.1f"%(siflcbuy-siflcsell)

