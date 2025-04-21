import socket as sock
from json_proto import Protocol

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
        proto.run()

print('Backend finished')
