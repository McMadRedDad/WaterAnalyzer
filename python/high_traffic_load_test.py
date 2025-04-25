import socket
from json_proto import Protocol

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 42069))
proto = Protocol(sock)

counter = 0

for i in range(69):
    req = {
    "proto_version": proto.get_version(),
    "server_version": "1.0.0",
    "id": counter,
    "operation": "PING",
    "parameters": {}
}
    proto.send(req)
    counter += 1

print(counter)
sock.close()