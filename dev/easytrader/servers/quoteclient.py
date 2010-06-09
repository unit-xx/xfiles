import socket
import sys

HOST, PORT = "127.0.0.1", 20888
data = "sdfasdf"

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server and send data
sock.connect((HOST, PORT))

# Receive data from the server and shut down
while 1:
    received = sock.recv(1024)
    print "Received: %s" % received

