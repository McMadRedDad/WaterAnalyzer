import socket as sock
from json_proto import Protocol
from gdal_executor import GdalExecutor

HOST = 'localhost'
PORT = 42069
with sock.socket(sock.AF_INET, sock.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(0)
    print(f'Backend listening on {HOST}:{PORT}')

    conn, addr = s.accept()
    with conn:
        print(f'New connection from {addr[0]}:{addr[1]}')
        proto = Protocol(conn)
        executor = GdalExecutor(proto.get_version())
        if not executor:
            raise GdalExecutor.GdalExecutorError(f'Unsupported protocol version: {proto.get_version()}')

        while True:
            request = proto.receive()
            if not request:
                raise proto.IPCError('Message not recieved')
            print(f'Recieved: {request}')

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
                break
    
    s.close()
            
print('Backend finished')
