import sys
import time
import datetime
import socket
import zlib, gzip
import pickle
from struct import unpack

HOST, PORT = "172.30.4.93", 22888

logfn = ""
logf = None

starttime = datetime.time(9, 10, 00)
endtime = datetime.time(15, 20, 00)
recstate = 0

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
        now = datetime.datetime.now()
        nowtime = datetime.datetime.now().time()

        if nowtime > starttime and nowtime < endtime:
            # start a new record period.
            if recstate == 0:
                print "gen new log file name."
                logfn = "siq%4d%02d%02d.log" % (now.year, now.month, now.day)
                logfnz = logfn+".gz"
                logf = open(logfn, "w")
                logfz = gzip.open(logfnz, "w")

            recstate = 1 # 1 for open
        else:
            recstate = 0 # 0 for close
            if logf is not None:
                print "close logs."
                logf.close()
                logfz.close()
                logfn = ""
                logfnz = ""

        if recstate:
            (pktlen,) = unpack("!I", sock.recv(4))
            received = recv_n(sock, pktlen)
            assert len(received) == pktlen
            price = pickle.loads(zlib.decompress(received))
            #print "Received: %s" % len(price)
            for qd in price:
                #print qd.exchCode, qd.varity_code, qd.deliv_date, qd.lastPrice, qd.bidPrice1, qd.askPrice1, qd.openPrice, qd.preClosePrice
                count = count + 1
                if count % 100 == 0:
                    #print count
                    logf.flush()
                    logfz.flush()
                if qd.varity_code == "IF":
                    print >>logf, str(datetime.datetime.now()), qd.sys_recv_time, qd.varity_code, qd.deliv_date, qd.lastPrice, qd.doneVolume, qd.openInterest, qd.bidPrice1, qd.bidVolume1, qd.askPrice1, qd.askVolume1
                    print >>logfz, str(datetime.datetime.now()), qd.sys_recv_time, qd.varity_code, qd.deliv_date, qd.lastPrice, qd.doneVolume, qd.openInterest, qd.bidPrice1, qd.bidVolume1, qd.askPrice1, qd.askVolume1
except KeyboardInterrupt:
    print "going to exit"
    if logf is not None:
        logf.close()
        logfz.close()
        logfn = ""
        logfnz = ""

end = time.time()

print  "===================="
print start

print end

print count

print count/(end-start)
print  "===================="
