import os, time, threading
import json
from typing import Union
from flask import Flask, request, make_response
from json_proto import Protocol
from gdal_executor import GdalExecutor

proto = Protocol()
executor = GdalExecutor(proto)
if not executor:
    raise ValueError(f'Unsupproted protocol version passed to {GdalExecutor} constructor.')
_max_content_length = 1024
server = Flask(__name__)

def _http_response(request: request, body: str, status: int, **headers: str) -> 'Response':
    """In 'headers' arguments underscore '_' is replaced with hyphen '-'."""

    hdrs = { 'Protocol-Version': proto.get_version() }
    if 'Request-ID' in request.headers:
        hdrs['Request-ID'] = request.headers['Request-ID']
    for k, v in headers.items():
        hdrs[k.replace('_', '-')] = v
    return make_response(body, status, hdrs)

def check_http_headers(request: request, request_type: str) -> Union['Response', None]:
    """Checks if all mandatory HTTP headers are included in the request. Then checks if headers' values are valid. In case of errors, generates a response and returns a Response object, otherwise returns None.
    Must be called first to validate an HTTP request.
    'request_type' is either 'command' for command execution requests, or 'resource' for resource requests."""

    headers = request.headers
    if request_type == 'command':
        mandatory_headers = ['Content-Type', 'Content-Length', 'Accept', 'Protocol-Version', 'Request-ID']
        present_headers = []
        for header in mandatory_headers:
            if header in headers:
                present_headers.append(header)
        if len(present_headers) != len(mandatory_headers):
            diff = set(mandatory_headers) - set(present_headers)
            if diff == {'Content-Length'}:
                return _http_response(request, '', 411, Reason='Invalid HTTP request. "Content-Length" header must be provided.')
            else:
                return _http_response(request, '', 400, Reason=f'Invalid HTTP Request. Headers "{diff}" are missing in the request.')
    elif request_type == 'resource':
        pass
    else:
        raise ValueError(f'Invalid "request_type" argument passed to "check_http_headers" function: {request_type}')

    if headers['Protocol-Version'] != proto.get_version():
        return _http_response(request, '', 400, Reason=f'Invalid protocol version "{headers["Protocol-Version"]}" in "Protocol-Version" header: used protocol version is "{proto.get_version()}".')

    try:
        id_ = int(headers['Request-ID'])
    except ValueError:
        return _http_response(request, '', 400, Reason='Invalid type for "Request-ID" header: must be of integer type.')
    if id_ < 0:
        return _http_response(request, '', 400, Reason=f'Invalid value "{id_}" of "Request-ID" header: must be >= 0.')

    if request_type == 'command':
        content_type = headers['Content-Type']
        if (
            content_type != 'application/json; charset=utf-8' and
            content_type != 'application/json;charset=utf-8'
        ):
            return _http_response(request, '', 400, Reason=f'Invalid value "{content_type}" of "Content-Type" header: must be "application/json; charset=utf-8" or "application/json;charset=utf-8".')
        
        accept = headers['Accept']
        if (
            accept != 'application/json; charset=utf-8' and
            accept != 'application/json;charset=utf-8'
        ):
            return _http_response(request, '', 400, Reason=f'Invalid value "{accept}" of "Accept" header: must be "application/json; charset=utf-8" or "application/json;charset=utf-8".')

        try:
            content_length = int(headers['Content-Length'])
        except ValueError:
            return _http_response(request, '', 400, Reason='Invalid type for "Content-Length" header: must be of integer type.')
        if content_length < 2:
            return _http_response(request, '', 400, Reason=f'Invalid value "{content_length}" for "Content-Length" header: must be in [2, {_max_content_length}] for {request.url} request.')
        if content_length > _max_content_length:
            return _http_response(request, '', 413, Reason=f'Invalid value "{content_length}" for "Content-Length" header: must be in [2, {_max_content_length}] for {request.url} request.')
    elif request_type == 'resource':
        pass
    else:
        raise ValueError(f'Invalid "request_type" argument passed to "check_http_headers" function: {request_type}')

    return None

def check_http_body(request: request, request_type: str) -> Union['Response', None]:
    """Checks validity of the request's body and returns None if the body is valid. Otherwise, generates a response and returns a Response object.
    Must be called after the 'check_http_headers' function.
    'request_type' is either 'command' for command execution requests, or 'resource' for resource requests."""

    if request_type == 'command':
        try:
            request_json = json.loads(request.get_data())
        except ValueError:
            return _http_response(request, '', 400, Reason='The request\'s body is not a valid JSON.')
        if not request_json:
            return _http_response(request, '', 400, Reason='The request\'s body must not be an empty JSON document for command execution requests.')
    elif request_type == 'resource':
        pass
    else:
        raise ValueError(f'Invalid "request_type" argument passed to "check_http_body" function: {request_type}')
    
    return None

def generate_http_response(request: request, response_json: dict) -> 'Response':
    """Constructs an HTTP response based on the JSON response generated by the protocol and returns a Response object.
    Assumes 'request' and 'response_json' are valid according to the protocol."""
    
    http_status = -1
    code = response_json['status']
    if code == 0:
        http_status = 200
    elif (
        code in range(10000, 10010+1) or
        code == 10100 or
        code == 10200 or
        code == 10400 or
        code in range(10500, 10502+1) or code == 20501 or
        code in range(10600, 10601+1) or code in range(20601, 20602+1)
    ):
        http_status = 400
    elif (
        code == 20400 or
        code == 20500 or
        code == 20600
    ):
        http_status = 404
    elif (
        code in range(20000, 20002+1) or
        code == 20201 or
        code in range(20300, 20301+1) or
        code == 20401 or
        code == 20502 or
        code == 20603
    ):
        http_status = 500
    elif code == 20003:
        http_status = 429
    elif code == 20200:
        http_status = 503
    else:
        raise ValueError(f'Incorrect status code in JSON response: {code}')

    return _http_response(request, response_json, http_status, Content_Type='application/json; charset=utf-8')

def shutdown():
    # to be changed for chosen wsgi server
    time.sleep(3)
    os._exit(0)

@server.get('/resource/<type>')
def handle_resource(type):
    print(request.args)
    print(request.headers)
    return make_response('', 200)

@server.post('/api/<command>')
def handle_command(command):
    if command not in executor.get_supported_operations():
        return _http_response(request, '', 400, Reason=f'Unknown/unsupported command "{command}" requested.')

    response = check_http_headers(request, 'command')
    if response is not None:
        return response

    response = check_http_body(request, 'command')
    if response is not None:
        return response

    request_json = request.get_json()
    
    response_json = proto.validate(request_json)
    if response_json['status'] != 0:
        return generate_http_response(request, response_json)

    if command != request_json['operation']:
        return _http_response(request, request_json, 400, Reason=f'Requested operation "{request_json["operation"]}" does not match to the endpoint "/api/{command}"')
    if request.headers['Protocol-Version'] != request_json['proto_version']:
        return _http_response(request, request_json,  400, Reason=f'Protocol versions do not match in HTTP header and JSON payload: {request.headers["Protocol-Version"]} and {request_json["proto_version"]}.')
    if int(request.headers['Request-ID']) != request_json['id']:
        return _http_response(request, request_json,  400, Reason=f'Request ids do not match in HTTP header and JSON payload: {request.headers["Request-ID"]} and {request_json["id"]}.')
    
    response_json = executor.execute(request_json)
    if response_json['status'] != 0:
        return generate_http_response(request, response_json)

    response_json = proto.match(request_json, response_json)
    if response_json['status'] != 0:
        return generate_http_response(request, response_json)

    if command == 'SHUTDOWN':
        threading.Thread(target=shutdown).start()
    if command == 'calc_preview':
        response_json['result']['url'] = f'/resource/preview?id={response_json['result']['url']}'

    return generate_http_response(request, response_json)
