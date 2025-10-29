from typing import Union
import os, time, threading
from flask import Flask, request, make_response
import tempfile
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import numpy as np
import json
from json_proto import Protocol
from gdal_executor import GdalExecutor
import index_calculator as indcal

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

    def _check_header_list(correct_headers, headers_to_check):
        present_headers = []
        for header in correct_headers:
            if header in headers_to_check:
                present_headers.append(header)
        if len(present_headers) != len(correct_headers):
            diff = set(correct_headers) - set(present_headers)
            if diff == {'Content-Length'}:
                return _http_response(request, '', 411, Reason='Invalid HTTP request. "Content-Length" header must be provided.')
            else:
                return _http_response(request, '', 400, Reason=f'Invalid HTTP Request. Headers "{diff}" are missing in the request.')
        return None

    headers = request.headers
    if request_type == 'command':
        mandatory_headers = ['Content-Type', 'Content-Length', 'Accept', 'Protocol-Version', 'Request-ID']
        hdr_list = _check_header_list(mandatory_headers, headers)
        if hdr_list is not None:
            return hdr_list
    elif request_type == 'resource':
        if request.base_url.rpartition('/')[2] not in ('preview', 'index'):
            raise ValueError('Resource request with invalid resource type "{}" passed to "check_http_headers" function'.format(request.base_url.rpartition('/')[2]))
        mandatory_headers = ['Accept', 'Protocol-Version', 'Request-ID']
        hdr_list = _check_header_list(mandatory_headers, headers)
        if hdr_list is not None:
            return hdr_list
    else:
        raise ValueError(f'Invalid "request_type" argument passed to "check_http_headers" function: "{request_type}"')

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
        if not (
            content_type == 'application/json; charset=utf-8' or
            content_type == 'application/json;charset=utf-8'
        ):
            return _http_response(request, '', 400, Reason=f'Invalid value "{content_type}" of "Content-Type" header: must be "application/json; charset=utf-8" or "application/json;charset=utf-8" for "{request.path}" request.')
        
        accept = headers['Accept']
        if not (
            accept == 'application/json; charset=utf-8' or
            accept == 'application/json;charset=utf-8'
        ):
            return _http_response(request, '', 400, Reason=f'Invalid value "{accept}" of "Accept" header: must be "application/json; charset=utf-8" or "application/json;charset=utf-8" for "{request.path}" request.')

        try:
            content_length = int(headers['Content-Length'])
        except ValueError:
            return _http_response(request, '', 400, Reason='Invalid type for "Content-Length" header: must be of integer type.')
        if content_length < 2:
            return _http_response(request, '', 400, Reason=f'Invalid value "{content_length}" for "Content-Length" header: must be in [2, {_max_content_length}] for {request.path} request.')
        if content_length > _max_content_length:
            return _http_response(request, '', 413, Reason=f'Invalid value "{content_length}" for "Content-Length" header: must be in [2, {_max_content_length}] for {request.path} request.')
    if request_type == 'resource':
        accept = headers['Accept']
        if request.base_url.rpartition('/')[2] == 'preview':
            if accept != 'image/png':
                return _http_response(request, '', 400, Reason=f'Invalid value "{accept}" of "Accept" header: must be "image/png" for /resource/preview request.')            
        elif request.base_url.rpartition('/')[2] == 'index':
            if accept != 'image/tiff':
                return _http_response(request, '', 400, Reason=f'Invalid value "{accept}" of "Accept" header: must be "image/tiff" for /resource/index request.')

    return None

def check_http_body(request: request, request_type: str) -> Union['Response', None]:
    """Checks validity of the request's body and returns None if the body is valid. Otherwise, generates a response and returns a Response object.
    Must be called after the 'check_http_headers' function.
    'request_type' is either 'command' for command execution requests, or 'resource' for resource requests."""

    if request_type == 'command':
        try:
            request_json = json.loads(request.get_data())
        except ValueError:
            return _http_response(request, '', 400, Reason='The request\'s body is not a valid JSON document.')
        if not request_json:
            return _http_response(request, '', 400, Reason='The request\'s body must not be an empty JSON document for command execution requests.')
    elif request_type == 'resource':
        if request.get_data() != b'':
            return _http_response(request, '', 400, Reason='The request\'s body must be empty for resource requests.')
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
        code == 10300 or
        code in range(10400, 10402+1) or code == 20400 or
        code == 10500 or code == 20500 or
        code in range(10600, 10601+1) or code == 20601 or
        code == 10700
    ):
        http_status = 400
    elif (
        code in range(20000, 20002+1) or code == 20004 or
        code == 20201 or
        code in range(20300, 20301+1) or
        code in range(20401, 20402+1) or
        code in range(20501, 20503+1) or
        code == 20600 or
        code in range (20800, 20801+1)
    ):
        http_status = 500
    elif code == 20003:
        http_status = 429
    elif code == 20200:
        http_status = 503
    elif code == 20700:
        http_status = 409
    else:
        raise ValueError(f'Unknown status code in JSON response: {code}')

    return _http_response(request, response_json, http_status, Content_Type='application/json; charset=utf-8')

def shutdown():
    # to be changed for chosen wsgi server and gracefulness
    time.sleep(3)
    os._exit(0)

def normalize_brightness(img: Image) -> Image:
    """Tweaks 'img's brightness based on its mean brightness and returns a new Image. Assumes 'img' is 8 bit and of 'RGB' or 'RGBA' format."""

    rgb = np.asarray(img)[..., :3].astype(np.float32)
    mean = rgb.mean(axis=(0, 1)).mean()

    if mean < 80:
        return ImageEnhance.Brightness(img).enhance(128 / mean * 0.4)
    elif mean > 170:
        return ImageEnhance.Brightness(img).enhance(mean / 128 * 0.6)
    else:
        return img

def image_with_scalebar(src_image: Image, gap: int, values: np.ndarray) -> Image:
    """Generates a scalebar (bar diagram flled with gradient) with min and max values from 'values' array and returns a new PIL.Image with 'src_image', the scalebar and a 'gap' in between."""

    scalebar_w, scalebar_h = max(25, src_image.width // 20), src_image.height
    total_w, total_h = src_image.width + gap + scalebar_w, src_image.height
    min_, mid, max_ = round(float(values.min()), 3), round(values.max() / 2, 3), round(float(values.max()), 3)
    
    gradient = Image.new('L', (1, scalebar_h))
    line = np.linspace(255, 0, scalebar_h, dtype=np.uint8)
    gradient.putdata(line)
    gradient = gradient.resize((scalebar_w, scalebar_h))

    draw = ImageDraw.Draw(Image.new('1', (0, 0)))
    font = ImageFont.load_default(14)
    str_max = draw.textlength(str(max_), font)
    str_mid = draw.textlength(str(mid), font)
    str_min = draw.textlength(str(min_), font)

    ret = Image.new('RGBA', (total_w + int(max(str_min, str_mid, str_max)) + 2, total_h), (0, 0, 0, 0))
    ret.paste(src_image)
    ret.paste(gradient, (src_image.width + gap - 1, 0))
    draw = ImageDraw.Draw(ret)

    draw.rectangle([(src_image.width + gap - 1, 0), (total_w - 2, total_h - 1)], outline=(128, 128, 128, 255), width=2)
    draw.text((total_w + 2, 0), str(max_), fill=(0, 0, 0, 255), font=font, anchor='lt')
    draw.text((total_w + 2, scalebar_h // 2), str(mid), fill=(0, 0, 0, 255), font=font, anchor='lm')
    draw.text((total_w + 2, scalebar_h), str(min_), fill=(0, 0, 0, 255), font=font, anchor='lb')

    return ret

@server.get('/resource/<res_type>')
def handle_resource(res_type):
    if len(request.query_string) == 0:
        return _http_response(request, '', 400, Reason='Query string must be provided for resource requests.')

    id_, scalebar = request.args.get('id'), request.args.get('sb')
    if id_ is None:
        return _http_response(request, '', 400, Reason='Query string must include "id" parameter for resource requests.')
    try:
        id_ = int(id_)
    except ValueError:
        return _http_response(request, '', 400, Reason='"id" parameter of the query string must be of integer type.')
    if id_ < 0:
        return _http_response(request, '', 400, Reason=f'Invalid value "{id_}" for "id" parameter of the query string: must be >= 0.')

    if res_type not in ('preview', 'index'):
        return _http_response(request, '', 400, Reason=f'The requested resource type "{res_type}" is not supported.')

    if res_type == 'preview':
        if scalebar is None:
            return _http_response(request, '', 400, Reason='Query string must include "sb" parameter for preview requests.')
        if len(request.args) != 2:
            return _http_response(request, '', 400, Reason='Query string must only include "id" and "sb" parameters for preview requests.')
        if not (scalebar == '0' or scalebar == '1'):
            return _http_response(request, '', 400, Reason='"sb" parameter of the query string must be either 0 or 1.')

    if res_type == 'index':
        if len(request.args) != 1:
            return _http_response(request, '', 400, Reason='Query string must only include "id" parameter for index requests.')

    response = check_http_headers(request, 'resource')
    if response is not None:
        return response

    response = check_http_body(request, 'resource')
    if response is not None:
        return response

    if res_type == 'preview':
        try:
            rgba = executor.pv_man.get(id_)
        except KeyError:
            return _http_response(request, '', 404, Reason=f'Requested preview "{id_}" does not exist.')
        
        if scalebar == '1':
            if rgba.index == 'nat_col':
                    return _http_response(request, '', 400, Reason='Unable to generate a scalebar for non-grayscale preview.')

        buf = BytesIO()
        img = Image.fromarray(rgba.array)
        if scalebar == '1':
            id__ = executor.ds_man.find(rgba.index)
            img = image_with_scalebar(img, 10, executor.ds_man.get_as_array(id__))
        else:
            img = normalize_brightness(img)
        img.save(buf, format='PNG')
        buf.seek(0)
        
        return _http_response(request, buf, 200, Content_Type='image/png', Width=img.width, Height=img.height)
        
    if res_type == 'index':
        try:
            dataset = executor.ds_man.get(id_).dataset
        except KeyError:
            return _http_response(request, '', 404, Reason=f'Requested index "{id_}" does not exist.')

        with tempfile.NamedTemporaryFile(mode='w+b', delete=True, delete_on_close=True) as tmp:
            executor.geotiff.CreateCopy(tmp.name, dataset, strict=False)
            tmp.seek(0)
            data = tmp.read()
            
            return _http_response(request, data, 200, Content_Type='image/tiff')

@server.post('/api/<command>')
def handle_command(command):
    if len(request.query_string) != 0:
        return _http_response(request, '', 400, Reason='No query strings allowed for command execution requests.')

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
    if command == 'calc_index':
        response_json['result']['url'] = f'/resource/index?id={response_json['result']['url']}'

    return generate_http_response(request, response_json)
