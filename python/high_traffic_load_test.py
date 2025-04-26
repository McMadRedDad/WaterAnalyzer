import socket
import time
from json_proto import Protocol

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 42069))
proto = Protocol(sock, 3.0)
counter = 0

while True:
    times = input('how many requests: ')
    for i in range(int(times)):
        req = {
            "proto_version": proto.get_version(),
            "server_version": "1.0.0",
            "id": counter,
            "operation": "PING",
            "parameters": {}
        }
        proto.send(req)
        counter += 1
    print('Sent', counter, 'times')

    time.sleep(5)
    responses = proto.receive_all()
    print('Responses:')
    for response in responses:
        print(response)

    stop = input('say "stop": ')
    if stop == 'stop':
        proto.send({
            "proto_version": proto.get_version(),
            "server_version": "1.0.0",
            "id": counter,
            "operation": "SHUTDOWN",
            "parameters": {}
        })
        ok = proto.receive_all()
        print(ok[0])
        if ok:
            if ok[0].get('status') == 0:
                for i in range(3):
                    print(3 - i)
                    time.sleep(1)
                print('~done~')
                break

sock.close()