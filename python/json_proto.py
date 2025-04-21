import struct

class Protocol:
    VERSION = '1.1.1'
    HEADER_SIZE = 4

    def __init__(self, connection):
        self.conn = connection

    def _receive_exact(self, num_bytes: int) -> bytes:
        data = b''
        while len(data) < num_bytes:
            chunk = self.conn.recv(num_bytes - len(data))
            if not chunk:
                raise ConnectionError('Could not recieve a message part')
                return None
            data += chunk
        return data

    def receive(self) -> dict:
        header = self._receive_exact(self.HEADER_SIZE)
        if not header:
            raise ConnectionError('Could not recieve header')
            return None
        (size, ) = struct.unpack('!I', header)
        
        data = self._receive_exact(size)
        if not data:
            raise ConnectionError('Could not recieve message body')
            return None
        message = data.decode('utf-8')

        return message

    def send(self, data: str) -> None:
        data_bytes = data.encode('utf-8')
        header = struct.pack('!I', len(data_bytes))

        self.conn.sendall(header + data_bytes)


    def run(self):
        while True:
            data = self.receive()
            if not data:
                raise ConnectionError('Message not recieved')
                break

            print('Recieved:', data)
            self.send('падаль, くそ')
            # self.conn.sendall(data)
            # print('sent:', data)