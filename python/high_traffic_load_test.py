import socket
import time
from json_proto import Protocol

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 42069))
proto = Protocol(sock, 3.0)
counter = 0
# sending_iteration = True

while True:
    # if sending_iteration:
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
    print('Sent', counter, 'times')

        # sending_iteration = False
        # continue

    responses = proto.receive_all_available()
    # if len(responses) < times:
    #     continue
    print(f'Responses (got {len(responses)}):')
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
        ok = proto.receive_all_available()
        if ok:
            print(ok[0])
            if ok[0].get('id') == counter and ok[0].get('status') == 0:
                for i in range(3):
                    print(3 - i)
                    time.sleep(1)
                print('~done~')
                break
            else:
                print('shutdown response not received')
                break    
        else:
            print('shutdown response not received')
            break

    # sending_iteration = True

sock.close()