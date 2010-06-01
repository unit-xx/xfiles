import sys
import socket
import zlib
import pickle
from struct import unpack

HOST, PORT = "localhost", 21888
data = "sdfasdf"

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
while 1:
    (pktlen,) = unpack("!I", sock.recv(4))
    received = recv_n(sock, pktlen)
    assert len(received) == pktlen
    price = pickle.loads(zlib.decompress(received))
    print "Received: %s" % len(price)
    print type(price[1])
    print price[1]
    print price[-1]

