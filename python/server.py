import json
from typing import Union
from flask import Flask, request, make_response
from json_proto import Protocol
from gdal_executor import GdalExecutor

# proto = Protocol()
# executor = GdalExecutor()
server = Flask(__name__)

def check_http_headers(request: request, request_type: str) -> Union['Response', None]:
    """Checks if all mandatory HTTP headers are included in the request. Then checks if headers' values are valid. In case of errors, generates a response and returns a Response object, otherwise returns None. Must be called first to validate an HTTP request. request_type is either 'command' for command execution requests, or 'resource' for resource requests."""

    headers = request.headers
    def _http400(reason: str) -> 'Response':
        response = make_response('', 400)
        response.headers['Request-ID'] = headers['Request-ID']
        response.headers['Reason'] = reason
        return response
    
    if request_type == 'command':
        mandatory_headers = ['Content-Type', 'Content-Length', 'Accept', 'Protocol-Version', 'Request-ID']
        present_headers = []
        for header in mandatory_headers:
            if header in headers:
                present_headers.append(header)
        if len(present_headers) != len(mandatory_headers):
            diff = set(mandatory_headers) - set(present_headers)
            response = make_response('', 400)
            if 'Request-ID' in present_headers:
                response.headers['Request-ID'] = headers['Request-ID']
            if diff == {'Content-Length'}:
                response.headers['Reason'] = 'Invalid HTTP request. "Content-Length" header must be provided.'
            else:
                response.headers['Reason'] = f'Invalid HTTP Request. Headers "{diff}" are missing in the request.'
            return response
    elif request_type == 'resource':
        pass
    else:
        raise ValueError(f'Invalid "request_type" argument passed to "check_http_headers" function: {request_type}')

    content_type = headers['Content-Type']
    if (
        content_type != 'application/json; charset=utf-8' and
        content_type != 'application/json;charset=utf-8'
    ):
        return _http400(f'Invalid value "{content_type}" of "Content-Type" header: must be "application/json; charset=utf-8" or "application/json;charset=utf-8".')
    
    accept = headers['Accept']
    if (
        accept != 'application/json; charset=utf-8' and
        accept != 'application/json;charset=utf-8'
    ):
        return _http400(f'Invalid value "{accept}" of "Accept" header: must be "application/json; charset=utf-8" or "application/json;charset=utf-8".')

    content_length = headers['Content-Length']
    try:
        content_length = int(content_length)
    except ValueError:
        return _http400('Invalid type for "Content-Length" header: must be of integer type.')
    if content_length != len(request.get_data()):
        return _http400(f'Invalid value {content_length} for "Content-Length" header: does not equal to message body\'s length in bytes (actual length is {len(request.get_data())}).')

    # proto version

    try:
        int(headers['Request-ID'])
    except ValueError:
        return _http400('Invalid type for "Request-ID" header: must be of integer type.')

    return None

def check_http_body(request: request, request_type: str) -> Union['Response', None]:
    """Checks validity of the request's body and returns None if the body is valid. Otherwise, generates a response and returns a Response object. Must be called after the 'check_http_headers' function. request_type is either 'command' for command execution requests, or 'resource' for resource requests."""

    if request_type == 'command':
        try:
            json.loads(request.get_data())
        except ValueError:
            response = make_response('', 400)
            response.headers['Request-ID'] = request.headers['Request-ID']
            response.headers['Reason'] = 'The request\'s body is not a valid JSON.'
            return response
    elif request_type == 'resource':
        pass
    else:
        raise ValueError(f'Invalid "request_type" argument passed to "check_http_body" function: {request_type}')
    
    return None

# def 

def generate_http_response(json_response: dict) -> 'Response':
    pass

@server.post('/api/<command>')
def respond(command):
    response = check_http_headers(request, 'command')
    if response is not None:
        return response

    response = check_http_body(request, 'command')
    if response is not None:
        return response

    return make_response('temp ok', 200)

# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     s.bind((HOST, PORT))
#     s.listen(1)
#     print(f'Backend listening on {HOST}:{PORT}')

#     conn, addr = s.accept()
#     with conn:
#         print(f'New connection from {addr[0]}:{addr[1]}')
#         proto = Protocol(conn)
#         executor = GdalExecutor(proto.get_version())
#         if not executor:
#             raise GdalExecutor.GdalExecutorError(f'Unsupported protocol version: {proto.get_version()}')

#         while True:
#             request = proto.receive_message()
#             if not request:
#                 # print('Could not receive request')
#                 continue
#             print(f'Received: {request}')

#             response = proto.validate(request)
#             if response.get('status') != 0:
#                 proto.send(response)
#                 continue

#             response = executor.execute(request)
#             if response.get('status') != 0:
#                 proto.send(response)
#                 continue

#             response = proto.match(request, response)
#             proto.send(response)

#             if (request.get('operation') == 'SHUTDOWN' and
#                 response.get('status') == 0):
#                 conn.close()
#                 break
    
#     s.close()

# print('Backend finished')
