import socket as sock

HOST = '127.0.0.1'
PORT = 42069
with sock.socket(sock.AF_INET, sock.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(0)
    print(f'Backend listening on {HOST}:{PORT}')

    conn, addr = s.accept()
    with conn:
        print(f'New connection from {addr[0]}:{addr[1]}')
        while True:
            data = conn.recv(1024)
            if not data: break
            # print('recieved:', data)
            # conn.sendall(data)
            # print('sent:', data)

print('Backend finished')
