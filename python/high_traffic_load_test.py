import socket
import time
from json_proto import Protocol

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 42069))
proto = Protocol(sock, 3.0)
counter = 0

while True:
    times = int(input('how many requests: '))
    for i in range(times):
        req = {
            "proto_version": proto.get_version(),
            "server_version": "1.0.0",
            "id": counter,
            "operation": "PING",
            "parameters": {}
        }
        proto.send(req)
        counter += 1
        print('request sent')
        response = proto.receive_message()
        if not response:
            print('response not received')
            continue
        print('received:', response)

    stop = input('say "stop": ')
    if stop == 'stop':
        proto.send({
            "proto_version": proto.get_version(),
            "server_version": "1.0.0",
            "id": counter,
            "operation": "SHUTDOWN",
            "parameters": {}
        })
        ok = proto.receive_message()
        if ok.get('status') == 0:
            print('received:', ok)
            print('~done~')
            break
        else:
            print('could not shutdown')
        
sock.close()
