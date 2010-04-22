import socket
import time

jsdserver = "172.18.20.71"
jsdport = 17990

conn = socket.socket()
conn.connect((jsdserver, jsdport))
conn.setblocking(0)

loginreq = "R|||6011|||9201|123|"
queryreq = "R|||6017|||9201|123||IF1006|"
getnextrowreq = "R|||0|||9201|123|"
conn.sendall(loginreq)
time.sleep(1)
resp = conn.recv(4096)
print len(resp)
k = 1
for i in resp.split("|")[3:]:
    print k, i
    k = k + 1

orderreq = "R|||6021|||9201|123|G|IF1006|0|0|1|1|3678|||"
