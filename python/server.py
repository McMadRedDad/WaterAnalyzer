import socket
from json_proto import Protocol
from gdal_executor import GdalExecutor

HOST = 'localhost'
PORT = 42069
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    listening = True
    print(f'Backend listening on {HOST}:{PORT}')

    conn, addr = s.accept()
    with conn:
        print(f'New connection from {addr[0]}:{addr[1]}')
        proto = Protocol(conn, 3.0)
        executor = GdalExecutor(proto.get_version())
        if not executor:
            raise GdalExecutor.GdalExecutorError(f'Unsupported protocol version: {proto.get_version()}')

        while True:
            requests = proto.receive_all_available()
            for request in requests:
                print(f'Received: {request}')

                response = proto.validate(request)
                if response.get('status') != 0:
                    proto.send(response)
                    continue

                response = executor.execute(request)
                if response.get('status') != 0:
                    proto.send(response)
                    continue

                response = proto.match(request, response)
                proto.send(response)

                if (request.get('operation') == 'SHUTDOWN' and
                    response.get('status') == 0):
                    conn.close()
                    listening = False
                    break

            if not listening:
                print('Shutting down')
                break
    
    s.close()

print('Backend finished')
