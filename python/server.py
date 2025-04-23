import socket as sock
from json_proto import Protocol
from gdal_executor import GdalExecutor

HOST = '127.0.0.1'
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

            result = proto.validate(request)
            if result.get('status') != 0:
                proto.send(result)
                continue

            result = executor.execute(request)
            result = proto.match(request, result)
            proto.send(result)

print('Backend finished')
