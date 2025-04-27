import struct
import json
import socket
import select

class Protocol:
    VERSION = '1.2.0'
    HEADER_SIZE = 4
    SUPPORTED_OPERATIONS = ('PING', 'SHUTDOWN', 'import_gtiff', 'export_gtiff', 'calc_preview', 'calc_index')

    class IPCError(Exception):
        pass

    def __init__(self, connection: socket.socket, timeout: float):
        self.conn = connection
        self.conn.setblocking(False)
        # self.conn.settimeout(timeout)
        self.buffer = b''
        print(f'Using protocol version {self.VERSION}')

    def send(self, message: dict) -> None:
        body = json.dumps(message).encode('utf-8')
        header = struct.pack('!I', len(body))
        msg = header + body

        total_sent = 0
        while total_sent < len(msg):
            sent = self.conn.send(msg[total_sent:])
            if sent == 0:
                self.conn.close()
                raise RuntimeError('Peer closed connection')
            total_sent += sent

    def receive_all_available(self, max_chunk_size: int = 4096) -> [dict]:
        messages = []
        # should be select.select([self.conn], [], [], 5.0), but that does not work on Windows
        while True:
            readable, _, _ = select.select([self.conn], [self.conn], [self.conn], 5.0)
            if not readable:
                # print('No data available to read')
                # return messages
                continue

            try:
                data = self.conn.recv(max_chunk_size)
                if not data:
                    self.conn.close()
                    raise RuntimeError('Peer closed connection')
            except BlockingIOError:
            # except socket.timeout:
                print('no more data for now')
                continue

            self.buffer += data

            while True:
                if len(self.buffer) < self.HEADER_SIZE:
                    break
                (msg_size, ) = struct.unpack('!I', self.buffer[:self.HEADER_SIZE])
                if type(msg_size) is not int:
                    self.conn.close()
                    raise self.IPCError('Invalid message header received')
                
                if len(self.buffer) < self.HEADER_SIZE + msg_size:
                    break
                msg = json.loads(self.buffer[self.HEADER_SIZE : self.HEADER_SIZE + msg_size].decode('utf-8'))
                if type(msg) is not dict:
                    self.conn.close()
                    raise self.IPCError('Invalid message body received')

                messages.append(msg)
                self.buffer = self.buffer[self.HEADER_SIZE + msg_size:]

            break

        return messages

    # def _receive_exact(self, num_bytes: int, max_chunk_size: int = 2048) -> bytes:
    #     data = b''
    #     received = 0
    #     while len(data) < num_bytes:
    #         chunk = self.conn.recv(min(num_bytes - received, max_chunk_size))
    #         if not chunk:
    #             raise RuntimeError('Client closed connection')
    #         data += chunk
    #         received += len(chunk)

    #     return data

    # def _receive_message(self) -> dict:
    #     header = self._receive_exact(self.HEADER_SIZE)
    #     (msg_size, ) = struct.unpack('!I', header)
    #     if type(msg_size) is not int:
    #         self.conn.close()
    #         raise self.IPCError('Invalid message header received')

    #     message = self._receive_exact(msg_size)
    #     message = json.loads(message.decode('utf-8'))
    #     if type(message) is not dict:
    #         self.conn.close()
    #         raise self.IPCError('Invalid message body received')

    #     return message

    # def receive_all(self) -> [dict]:
    #     messages = []
    #     while True:
    #         try:
    #             messages.append(self._receive_message())
    #         except socket.timeout:
    #             print('all data received for now')
    #             break
    #     return messages

    def validate(self, request: dict) -> dict:
        """Checks for all protocol-specific request errors related to message structure, spelling, etc. and returns a dictionary to be used by Protocol.send method. Does not check for data-specific errors (e.g. non-existent image id, server version, etc.) that can only be verified by the backend itself. The dictionary returned is guaranteed to be valid."""

        proto_version = request.get('proto_version')
        server_version = request.get('server_version')
        id_ = request.get('id')
        operation = request.get('operation')
        parameters = request.get('parameters')
        status = 0
        result = {}
        
        def _non_standard_response(request: dict, status: str, result: dict) -> dict:
            response = {}
            for key, val in request.items():
                response[key] = val
            response["status"] = status
            response["result"] = result

            return response

        def _response(status: int, result: dict) -> dict:
            return {
                "proto_version": self.VERSION,
                "server_version": server_version,
                "id": id_,
                "status": status,
                "result": result
            }

        ### Common errors ###
        keys = list(request.keys())
        correct_keys = ['proto_version', 'server_version', 'id', 'operation', 'parameters']
        present_keys = []
        for key in keys:
            if key not in correct_keys:
                return _non_standard_response(request, 10000, {"error": f"key '{key}' is unknown"})
            else:
                present_keys.append(key)
        
        if len(keys) != 5:
            diff = set(correct_keys) - set(present_keys)
            return _non_standard_response(request, 10001, {"error": f"keys '{diff}' are not specified"})
                    
        ok = True
        if type(proto_version) is not str:
            ok = False
        digits = proto_version.split('.')
        if len(digits) == 3:
            for i in range(3):
                try:
                    digits[i] = int(digits[i])
                except ValueError:
                    ok = False
        else:
            ok = False
        if not ok:
            return _response(10002, {"error": f"invalid protocol version string: '{proto_version}'"})

        if type(server_version) is not str:
            ok = False
        digits = server_version.split('.')
        if len(digits) == 3:
            for i in range(3):
                try:
                    digits[i] = int(digits[i])
                except ValueError:
                    ok = False
        else:
            ok = False
        if not ok:
            return _response(10003, {"error": f"invalid server version string: '{server_version}'"})
                    
        if type(id_) is not int:
            return _response(10004, {"error": f"invalid request id: '{id_}'"})
            
        if operation not in self.SUPPORTED_OPERATIONS:
            return _response(10005, {"error": f"unknown operation '{operation}' requested"})
            
        if type(parameters) is not dict:
            return _response(10006, {"error": "invalid 'parameters' key: must be of JSON object type"})
            
        if proto_version != self.VERSION:
            return _response(10008, {"error": f"incorrect protocol version: '{proto_version}'. The current protocol version is {self.VERSION}"})
            
        ### PING ###
        if operation == 'PING':
            if len(parameters) != 0:
                return _response(10100, {"error": "'parameters' must be an empty JSON object for 'PING' request"})
            else:
                return _response(0, {"data": "PONG"})

        ### SHUTDOWN ###
        if operation == 'SHUTDOWN':
            if len(parameters) != 0:
                return _response(10200, {"error": "'parameters' must be an empty JSON object for 'SHUTDOWN' request"})
            else:
                return _response(0, {})
        
        return _response(-1, {"error": "how's this even possible?"})

    def match(self, request: dict, result: dict) -> dict:
        """Checks if 'result' correctly correlates with 'request' and returns a dictionary to be used by Protocol.send method. The dictionary returned is guaranteed to be valid."""

        proto_version = request.get('proto_version')
        server_version = request.get('server_version')
        id_ = request.get('id')

        def _response(status: int, result: dict) -> dict:
            return {
                "proto_version": self.VERSION,
                "server_version": server_version,
                "id": id_,
                "status": status,
                "result": result
            }

        if proto_version != result.get('proto_version'):
            return _response(10009, {"error": "values 'proto_version' do not match in request and response"})
        if server_version != result.get('server_version'):
            return _response(10009, {"error": "values 'server_version' do not match in request and response"})
        if id_ != result.get('id'):
            return _response(10009, {"error": "values 'id' do not match in request and response"})

        return _response(result.get('status'), result.get('result'))

    def get_version(self) -> str:
        return self.VERSION

    def get_supported_operations(self) -> tuple:
        return self.SUPPORTED_OPERATIONS

    def get_header_size(self) -> int:
        return self.HEADER_SIZE
