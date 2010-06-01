import socket
import sys

HOST, PORT = "localhost", 20888
data = "sdfasdf"

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server and send data
sock.connect((HOST, PORT))

# Receive data from the server and shut down
while 1:
    pktlen = unpack("!I", sock.recv(4))
    received = sock.recv(pktlen)
    assert len(received) == pktlen
    print "Received: %s" % received

