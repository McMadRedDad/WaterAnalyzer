import socket
from json_proto import Protocol
from gdal_executor import GdalExecutor

HOST = 'localhost'
PORT = 42069
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(0)
    listening = True
    print(f'Backend listening on {HOST}:{PORT}')

    conn, addr = s.accept()


    counter = 0


    with conn:
        print(f'New connection from {addr[0]}:{addr[1]}')
        proto = Protocol(conn, 3.0)
        executor = GdalExecutor(proto.get_version())
        if not executor:
            raise GdalExecutor.GdalExecutorError(f'Unsupported protocol version: {proto.get_version()}')

        while True:
            # requests = proto.poll_messages(3.0)
            # for req in requests:
            #     counter += 1
            #     print('Received:', req)

            #     response = proto.validate(req)
            #     if response.get('status') != 0:
            #         proto.send(response)
            #         continue

            #     response = executor.execute(req)
            #     if response.get('status') != 0:
            #         proto.send(response)
            #         continue

            #     response = proto.match(req, response)
            #     proto.send(response)

            #     if (req.get('operation') == 'SHUTDOWN' and
            #         response.get('status') == 0):
            #         conn.close()
            #         break

            # request = proto.receive()
            # if not request:
            #     raise proto.IPCError('Message not recieved')
            # counter += 1
            # print(f'Received: {request}', 'TIME', counter)

            # response = proto.validate(request)
            # if response.get('status') != 0:
            #     proto.send(response)
            #     continue

            # response = executor.execute(request)
            # if response.get('status') != 0:
            #     proto.send(response)
            #     continue

            # response = proto.match(request, response)
            # proto.send(response)

            # if (request.get('operation') == 'SHUTDOWN' and
            #     response.get('status') == 0):
            #     conn.close()
            #     break

            # messages = []
            # while True:
            #     try:
            #         messages.append(proto.receive_message())
            #     except socket.timeout:
            #         print('all data received for now')
            #         break
            
            requests = proto.receive_all()
            for request in requests:
                counter += 1
                print(f'Received: {request}', 'TIME', counter)

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
