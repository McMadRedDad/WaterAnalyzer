import struct
import json
import socket

class Protocol:
    VERSION = '1.2.0'
    HEADER_SIZE = 4
    SUPPORTED_OPERATIONS = ('PING', 'SHUTDOWN', 'import_gtiff', 'export_gtiff', 'calc_preview', 'calc_index')

    class IPCError(Exception):
        pass

    def __init__(self, connection: socket.socket, timeout: float = 10.0):
        self.conn = connection
        self.conn.settimeout(timeout)
        print(f'Using protocol version {self.VERSION}')

    def send(self, message: dict) -> None:
        """Generate and send a JSON. Does not validate message's content according to this protocol and can send any JSON."""

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

    def _receive_exact(self, num_bytes: int, max_chunk_size: int = 2048) -> bytes:
        """Reads data from socket until num_bytes are received and returns it as bytes. If timeouts, returns an empty bytes object."""

        data = b''
        received = 0
        while len(data) < num_bytes:
            try:
                chunk = self.conn.recv(min(num_bytes - received, max_chunk_size))
                if not chunk:
                    self.conn.close()
                    raise RuntimeError('Peer closed connection')
            except socket.timeout:
                return b''
            data += chunk
            received += len(chunk)

        return data

    def receive_message(self) -> dict:
        """Receive and parse incoming message. Reads exactly one message and returns it as a dictionary. If fails, returns an empty dictionary. Does not validate message's content according to this protocol and can receive any JSON."""

        header = self._receive_exact(self.HEADER_SIZE)
        if not header:
            print('Could not receive message header')
            return {}
        (msg_size, ) = struct.unpack('!I', header)
        if type(msg_size) is not int:
            self.conn.close()
            raise self.IPCError('Invalid message header received')

        message = self._receive_exact(msg_size)
        if not message:
            print('Could not receive message body')
            return {}
        message = json.loads(message.decode('utf-8'))
        if type(message) is not dict:
            self.conn.close()
            raise self.IPCError('Invalid message body received')

        return message

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
