import sys
import time
import datetime
import socket
import zlib
import pickle
from struct import unpack

HOST, PORT = "172.30.4.98", 22888

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

# Receive data from the server and shut down
start = time.time()
print start

count = 0

try:
    while 1:
        (pktlen,) = unpack("!I", sock.recv(4))
        received = recv_n(sock, pktlen)
        assert len(received) == pktlen
        price = pickle.loads(zlib.decompress(received))
        #print "Received: %s" % len(price)
        for qd in price:
            #print qd.exchCode, qd.varity_code, qd.deliv_date, qd.lastPrice, qd.bidPrice1, qd.askPrice1, qd.openPrice, qd.preClosePrice
            count = count + 1
            if count % 100 == 0:
                print count
            if qd.varity_code == "IF":
                print str(datetime.datetime.now()), qd.sys_recv_time, qd.varity_code, qd.deliv_date, qd.lastPrice, qd.doneVolume, qd.openInterest, qd.bidPrice1, qd.bidVolume1, qd.askPrice1, qd.askVolume1
except KeyboardInterrupt:
    pass

end = time.time()

print  "===================="
print start

print end

print count

print count/(end-start)
print  "===================="
