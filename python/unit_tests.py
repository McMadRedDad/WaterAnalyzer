# 1. Test HTTP part only, without JSON
# 2. Test JSON part only, without HTTP
# 3. Test both together

import unittest
from copy import deepcopy
from werkzeug.test import EnvironBuilder
from server import server, proto, executor, generate_http_response

server.testing = True
client = server.test_client()
proto_version = proto.get_version()
server_version = executor.get_version()

# Substrings of the Reason HTTP header that contains HTTP-level error description. Most HTTP-level errors return 400 response, so checking only the status code is not enough.
http_reason = {
    'unknown_endpoint': 'Unknown/unsupported command ',
    'unsupported_resource_type': 'The requested resource type ',
    'no_query_string': 'No query strings allowed ',
    'query_string_necessary': 'Query string must be provided ',
    'query_string_id': 'Query string must include "id" ',
    'inv_id_type_in_query_string': '"id" parameter of the query string ',
    'inv_id_in_query_string': ' for "id" parameter of the query string: must be >= 0.',
    'missing_content_type': ' Headers "{\'Content-Type\'}" are missing ',
    'missing_accept': ' Headers "{\'Accept\'}" are missing ',
    'missing_proto_v': ' Headers "{\'Protocol-Version\'}" are missing ',
    'missing_request_id': ' Headers "{\'Request-ID\'}" are missing ',
    'missing_many1': ' Headers "{\'Content-Length\', \'Accept\'}" are missing ',
    'missing_many2': ' Headers "{\'Accept\', \'Content-Length\'}" are missing ',
    'missing_content_length': ' "Content-Length" header must be provided.',
    'inv_content_type': ' of "Content-Type" header: must be ',
    'inv_accept': ' of "Accept" header: must be ',
    'inv_content_length_type': 'Invalid type for "Content-Length" header: must be ',
    'inv_content_length': ' must be in [2, 1024] ',
    'inv_proto_v': 'Invalid protocol version ',
    'inv_request_id_type': 'Invalid type for "Request-ID" header: must be ',
    'inv_request_id': ' of "Request-ID" header: must be ',
    'inv_json': ' is not a valid JSON document.',
    'empty_json': ' must not be an empty JSON document ',
    'get_body_not_empty': ' body must be empty ',
    'endpoint_mismatch': ' does not match to the endpoint ',
    'proto_v_mismatch': 'Protocol versions do not match ',
    'request_id_mismatch': 'Request ids do not match ',
    'get_preview_no_sb': ' must include "sb" parameter ',
    'get_preview_odd_params': ' must only include "id" and "sb" parameters ',
    'get_preview_inv_sb': ' must be either 0 or 1.',
    'get_preview_not_grayscale': 'Unable to generate a scalebar ',
    'get_preview_404': 'Requested preview ',
    'get_index_odd_params': ' must only include "id" parameter ',
    'get_index_404': 'Requested index '
}

# Content-Length = string -> assuming invalid type
# Content-Length != 0 -> assuming invalid value
# Content-Length = 0 -> the value needs to be recalculated by HTTP client
http_headers = {
    "ok": {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': 0,
        'Accept': 'application/json; charset=utf-8',
        'Protocol-Version': proto_version,
        'Request-ID': 0
    },
    'get_preview_ok': {
        'Accept': 'image/png',
        'Protocol-Version': proto_version,
        'Request-ID': 0
    },
    'get_index_ok': {
        'Accept': 'image/tiff',
        'Protocol-Version': proto_version,
        'Request-ID': 0
    },
    'missing_content_type': {
        'Content-Length': 0,
        'Accept': 'application/json; charset=utf-8',
        'Protocol-Version': proto_version,
        'Request-ID': 0
    },
    'missing_accept': {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': 0,
        'Protocol-Version': proto_version,
        'Request-ID': 0
    },
    'missing_proto_v': {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': 0,
        'Accept': 'application/json; charset=utf-8',
        'Request-ID': 0
    },
    'missing_request_id': {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': 0,
        'Accept': 'application/json; charset=utf-8',
        'Protocol-Version': proto_version
    },
    'missing_many': {
        'Content-Type': 'application/json; charset=utf-8',
        'Protocol-Version': proto_version,
        'Request-ID': 0
    },
    'missing_content_length': {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json; charset=utf-8',
        'Protocol-Version': proto_version,
        'Request-ID': 0
    },
    "inv_content_type": {
        'Content-Type': 'none',
        'Content-Length': 0,
        'Accept': 'application/json; charset=utf-8',
        'Protocol-Version': proto_version,
        'Request-ID': 0
    },
    "inv_accept": {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': 0,
        'Accept': 'any',
        'Protocol-Version': proto_version,
        'Request-ID': 0
    },
    "inv_content_length_type": {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': "zero",
        'Accept': 'application/json; charset=utf-8',
        'Protocol-Version': proto_version,
        'Request-ID': 0
    },
    "inv_content_length_val1": {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': -1,
        'Accept': 'application/json; charset=utf-8',
        'Protocol-Version': proto_version,
        'Request-ID': 0
    },
    "inv_content_length_val2": {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': 42069,
        'Accept': 'application/json; charset=utf-8',
        'Protocol-Version': proto_version,
        'Request-ID': 0
    },
    "inv_proto_v": {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': 0,
        'Accept': 'application/json; charset=utf-8',
        'Protocol-Version': "-1",
        'Request-ID': 0
    },
    "inv_request_id_type": {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': 0,
        'Accept': 'application/json; charset=utf-8',
        'Protocol-Version': proto_version,
        'Request-ID': "zero"
    },
    "inv_request_id": {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': 0,
        'Accept': 'application/json; charset=utf-8',
        'Protocol-Version': proto_version,
        'Request-ID': -1
    }
}

test_files = {
    'gtiff_ok1': '/home/tim/Учёба/Test data/LC09_L1TP_188012_20230710_20230710_02_T1/LC09_L1TP_188012_20230710_20230710_02_T1_B5.TIF',
    'gtiff_ok2': '/home/tim/Учёба/Test data/dacha.tif',
    'gtiff_ok3': '/home/tim/Учёба/Test data/dacha_10px.tif',
    'gtiff_ok4': '/home/tim/Учёба/Test data/dacha_dist.tif',
    'gtiff_ok5': '/home/tim/Учёба/Test data/dacha_dist_10px.tif',
    'gtiff_ok6': '/home/tim/Учёба/Test data/dacha_dist_copy.tif',
    'only_nodata': '/home/tim/Учёба/Test data/empty.tif',
    'regular_tif': '/home/tim/Учёба/Test data/japanese-stone-lantern.tif',
    'saga_grid': '/home/tim/Учёба/Test data/dacha.sg-grd-z',
    'shape': '/home/tim/Учёба/Test data/dacha.shp',
    'non_existent': '/home/tim/42069.34'
}

requests_json = {
    'unknown_key1': {
        "version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'unknown_key2': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {},
        "val": 420.69
    },
    'missing_key1': {
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'missing_key2': {
        "proto_version": proto_version,        
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'missing_key3': {
        "proto_version": proto_version,
        "server_version": server_version,
        "operation": "PING",
        "parameters": {}
    },
    'missing_key4': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "parameters": {}
    },
    'missing_key5': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
    },
    'inv_proto_ver1': {
        "proto_version": "abc",
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'inv_proto_ver2': {
        "proto_version": "120",
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'inv_proto_ver3': {
        "proto_version": "12.0",
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'inv_proto_ver4': {
        "proto_version": "12.0",
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'inv_proto_ver5': {
        "proto_version": "a.2.0",
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'inv_proto_ver6': {
        "proto_version": "1.2.0-1",
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'inv_serv_ver1': {
        "proto_version": proto_version,
        "server_version": "abc",
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'inv_serv_ver2': {
        "proto_version": proto_version,
        "server_version": "120",
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'inv_serv_ver3': {
        "proto_version": proto_version,
        "server_version": "12.0",
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'inv_serv_ver4': {
        "proto_version": proto_version,
        "server_version": "12.0",
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'inv_serv_ver5': {
        "proto_version": proto_version,
        "server_version": "a.2.0",
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'inv_serv_ver6': {
        "proto_version": proto_version,
        "server_version": "1.2.0-1",
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'inv_id1': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": "abc",
        "operation": "PING",
        "parameters": {}
    },
    'inv_id2': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0.3,
        "operation": "PING",
        "parameters": {}
    },
    'unknown_operation': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "abc",
        "parameters": {}
    },
    'inv_params': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": "abc"
    },
    'params_missing_key': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {}
    },
    'params_unknown_key': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['gtiff_ok1'],
            "arg": "val"
        }
    },
    'incorrect_proto_ver': {
        "proto_version": "420.69.42069",
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'incorrect_serv_ver': {
        "proto_version": proto_version,
        "server_version": "420.69.42069",
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'unsupported_proto_ver': {
        "proto_version": "1.0.0",
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'unsupported_operation': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "new_operation",
        "parameters": {}
    },
    'ping_ok': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {}
    },
    'ping_non_empty_params': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "PING",
        "parameters": {"arg1": "val1"}
    },
    'shutdown_ok': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "SHUTDOWN",
        "parameters": {}
    },
    'shutdown_non_empty_params': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "SHUTDOWN",
        "parameters": {"arg1": "val1"}
    },
    # shutdown 20200, 20201
    'import_gtiff_ok_big': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['gtiff_ok1'],
            "band": 1
        }
    },
    'import_gtiff_ok_mid': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['gtiff_ok2'],
            "band": 2
        }
    },
    'import_gtiff_ok_smol': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['gtiff_ok3'],
            "band": 11
        }
    },
    'import_gtiff_ok_mid2': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['gtiff_ok4'],
            "band": 3
        }
    },
    'import_gtiff_ok_mid3': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['gtiff_ok6'],
            "band": 4
        }
    },
    'import_gtiff_ok_smol2': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['gtiff_ok5'],
            "band": 5
        }
    },
    'import_gtiff_ok_nodata': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['only_nodata'],
            "band": 6
        }
    },
    'import_gtiff_no_file': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "band": 1
        }
    },
    'import_gtiff_no_band': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['gtiff_ok1']
        }
    },
    'import_gtiff_non_existent': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['non_existent'],
            "band": 1
        }
    },
    'import_gtiff_not_geotiff1': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['saga_grid'],
            "band": 1
        }
    },
    'import_gtiff_not_geotiff2': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['shape'],
            "band": 1
        }
    },
    'import_gtiff_not_geotiff3': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['regular_tif'],
            "band": 1
        }
    },
    'import_gtiff_inv_band_type': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['gtiff_ok1'],
            "band": "rule34"
        }
    },
    'calc_preview_ok': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_preview",
        "parameters": {
            "index": "test",
            "width": 100,
            "height": 100
        }
    },
    'calc_preview_no_index': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_preview",
        "parameters": {
            "width": 100,
            "height": 100
        }
    },
    'calc_preview_no_width': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_preview",
        "parameters": {
            "index": "test",
            "height": 100
        }
    },
    'calc_preview_no_height': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_preview",
        "parameters": {
            "index": "test",
            "width": 100
        }
    },
    'calc_preview_inv_index_type': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_preview",
        "parameters": {
            "index": 69,
            "width": 100,
            "height": 100
        }
    },
    'calc_preview_inv_width_type': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_preview",
        "parameters": {
            "index": "test",
            "width": 'abc',
            "height": 100
        }
    },
    'calc_preview_inv_height_type': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_preview",
        "parameters": {
            "index": "test",
            "width": 100,
            "height": 'abc'
        }
    },
    'calc_preview_unsupported_index': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_preview",
        "parameters": {
            "index": "rule34",
            "width": 100,
            "height": 100
        }
    },
    'calc_preview_index_not_created': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_preview",
        "parameters": {
            "index": "oc3",
            "width": 100,
            "height": 100
        }
    },
    'calc_preview_inv_width': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_preview",
        "parameters": {
            "index": "test",
            "width": -10,
            "height": 100
        }
    },
    'calc_preview_inv_height': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_preview",
        "parameters": {
            "index": "test",
            "width": 100,
            "height": -10
        }
    },
    # calc_preview 20402
    'calc_index_ok1': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_index",
        "parameters": {
            "index": "test"
        }
    },
    'calc_index_no_index': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_index",
        "parameters": {}
    },
    'calc_index_inv_index_type': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_index",
        "parameters": {
            "index": 69
        }
    },
    'calc_index_unsupported_index': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_index",
        "parameters": {
            "index": "unsupported"
        }
    },
    'calc_index_not_enough_bands': {    # depends on import_gtiff's band nums as wi2015 uses band 7
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "calc_index",
        "parameters": {
            "index": "wi2015"
        }
    },
    # calc_index 20502
    'set_satellite_ok': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "set_satellite",
        "parameters": {
            "satellite": "Landsat 8/9"
        }
    },
    'set_satellite_inv_satellite_type': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "set_satellite",
        "parameters": {
            "satellite": 69
        }
    },
    'set_satellite_unsupported_satellite': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "set_satellite",
        "parameters": {
            "satellite": "NEW sAtEllItE 6/9"
        }
    },
    'end_session_ok': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "end_session",
        "parameters": {}
    },
    'end_session_non_empty_params': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "end_session",
        "parameters": {
            "rule34": 42069
        }
    },
}

# Able to override the Content-Type and Content-Length headers.
def POST(endpoint, headers, body):
    builder = EnvironBuilder(
        method='POST',
        path=endpoint,
        headers=headers,
        json=body
    )
    builder.content_type = headers.get('Content-Type')
    env = builder.get_environ()
    if 'Content-Length' not in headers:
        env.pop('CONTENT_LENGTH')
    elif type(headers['Content-Length']) is not int or headers['Content-Length'] != 0:
        env['CONTENT_LENGTH'] = str(headers['Content-Length'])
    return client.open(environ_overrides=env)

def GET(url, headers, body, **extra_headers):
    builder = EnvironBuilder(
        method='GET',
        path=url,
        headers=headers,
        data=body
    )
    for k, v in extra_headers.items():
        builder.headers[k.replace('-', '_').upper()] = str(v)
    return client.open(environ_overrides=builder.get_environ())

def check_json(request_json):
    response = proto.validate(request_json)
    if response['status'] != 0:
        return response['status']
    response = executor.execute(request_json)
    if response['status'] != 0:
        return response['status']
    response = proto.match(request_json, response)
    return response['status']

def check_all(endpoint, headers, body):
    res = POST(endpoint, headers, body)
    return res.status_code, \
           res.headers.get('Reason'), \
           res.get_json().get('status') if res.get_json() else None

class Test(unittest.TestCase):
    def prepare(self):
        executor.execute(requests_json['set_satellite_ok'])
        executor.execute(requests_json['import_gtiff_ok_big'])
        executor.execute(requests_json['import_gtiff_ok_mid'])
        executor.execute(requests_json['import_gtiff_ok_smol'])
        executor.execute(requests_json['import_gtiff_ok_mid2'])
        executor.execute(requests_json['import_gtiff_ok_mid3'])
        executor.execute(requests_json['import_gtiff_ok_smol2'])
        executor.execute(requests_json['import_gtiff_ok_nodata'])
        executor.execute(requests_json['calc_preview_ok'])
        executor.execute(requests_json['calc_index_ok1'])
    
    def test_000(self):
        def _codes(response: 'Response'):
            return response.status_code, \
                   response.get_json().get('status') if response.get_json() else None

        print('RUNNING INITIAL TEST "test_000" that acts as a setup. If this test fails, others will too. Check this test first.')

        print('Checking error 20004...')
        self.assertEqual((500, 20004) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_mid'])))
        self.assertEqual((500, 20004) , _codes(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_ok'])))
        self.assertEqual((500, 20004) , _codes(POST('/api/calc_index', http_headers['ok'], requests_json['calc_index_ok1'])))
        print('Done!')

        self.prepare()

        print('Imported GTiffs, created a preview, created an index.')
        print('Initialization successful!')

    ### HTTP ONLY ###

    def test_http_ok(self):
        self.assertEqual(200, POST('/api/PING', http_headers['ok'], requests_json['ping_ok']).status_code)
        # self.assertEqual(200, POST('/api/SHUTDOWN', http_headers['ok'], requests_json['shutdown_ok']).status_code)
        self.assertEqual(200, POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_big']).status_code)
        self.assertEqual(200, POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_mid']).status_code)
        self.assertEqual(200, POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_smol']).status_code)
        self.assertEqual(200, POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_mid2']).status_code)
        self.assertEqual(200, POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_mid3']).status_code)
        self.assertEqual(200, POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_smol2']).status_code)
        self.assertEqual(200, POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_nodata']).status_code)
        prev = POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_ok'])
        self.assertEqual(200, prev.status_code)
        url_pr = prev.get_json()['result']['url'] + '&sb=0'
        index = POST('/api/calc_index', http_headers['ok'], requests_json['calc_index_ok1'])
        self.assertEqual(200, index.status_code)
        url_ind = index.get_json()['result']['url']
        self.assertEqual(200, GET(url_pr, http_headers['get_preview_ok'], '').status_code)
        self.assertEqual(200, GET(url_ind, http_headers['get_index_ok'], '').status_code)
        self.assertEqual(200, POST('/api/set_satellite', http_headers['ok'], requests_json['set_satellite_ok']).status_code)
        self.assertEqual(200, POST('/api/end_session', http_headers['ok'], requests_json['end_session_ok']).status_code)
        self.prepare()
        
        self.assertIsNone(POST('/api/PING', http_headers['ok'], requests_json['ping_ok']).headers.get('Reason'))
        # self.assertIsNone(POST('/api/SHUTDOWN', http_headers['ok'], requests_json['shutdown_ok']).headers.get('Reason'))
        self.assertIsNone(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_big']).headers.get('Reason'))
        self.assertIsNone(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_mid']).headers.get('Reason'))
        self.assertIsNone(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_smol']).headers.get('Reason'))
        self.assertIsNone(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_mid2']).headers.get('Reason'))
        self.assertIsNone(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_mid3']).headers.get('Reason'))
        self.assertIsNone(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_smol2']).headers.get('Reason'))
        self.assertIsNone(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_nodata']).headers.get('Reason'))
        self.assertIsNone(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_ok']).headers.get('Reason'))
        self.assertIsNone(POST('/api/calc_index', http_headers['ok'], requests_json['calc_index_ok1']).headers.get('Reason'))
        prev = POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_ok'])
        url_pr = prev.get_json()['result']['url'] + '&sb=0'
        index = POST('/api/calc_index', http_headers['ok'], requests_json['calc_index_ok1'])
        url_ind = index.get_json()['result']['url']
        self.assertIsNone(GET(url_pr, http_headers['get_preview_ok'], '').headers.get('Reason'))
        self.assertIsNone(GET(url_ind, http_headers['get_index_ok'], '').headers.get('Reason'))
        self.assertIsNone(POST('/api/set_satellite', http_headers['ok'], requests_json['set_satellite_ok']).headers.get('Reason'))
        self.assertIsNone(POST('/api/end_session', http_headers['ok'], requests_json['end_session_ok']).headers.get('Reason'))
        self.prepare()
   
    def test_http_endpoint(self):
        self.assertEqual(400, POST('/api/unsupported', http_headers['ok'], '').status_code)
        self.assertEqual(400, GET('resource/unsupported?id=0&sb=0', http_headers['ok'], '').status_code)
        self.assertEqual(404, GET('/resource/preview?id=4206934&sb=0', http_headers['get_preview_ok'], '').status_code)
        self.assertEqual(404, GET('/resource/index?id=4206934', http_headers['get_index_ok'], '').status_code)

        self.assertTrue(http_reason['unknown_endpoint'] in POST('/api/unsupported', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['unsupported_resource_type'] in GET('/resource/unsupported?id=0&sb=0', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['get_preview_404'] in GET('/resource/preview?id=4206934&sb=0', http_headers['get_preview_ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['get_index_404'] in GET('/resource/index?id=4206934', http_headers['get_index_ok'], '').headers.get('Reason'))
   
    def test_query_string(self):
        self.assertEqual(400, POST('/api/PING?=', http_headers['ok'], '').status_code)
        self.assertEqual(400, GET('/resource/preview', http_headers['ok'], '').status_code)
        self.assertEqual(400, GET('/resource/preview?a=1', http_headers['ok'], '').status_code)
        self.assertEqual(400, GET('/resource/preview?id=abc', http_headers['ok'], '').status_code)
        self.assertEqual(400, GET('/resource/preview?id=-1', http_headers['ok'], '').status_code)
        self.assertEqual(400, GET('/resource/preview?id=0', http_headers['ok'], '').status_code)
        self.assertEqual(400, GET('/resource/preview?id=0&sb=0&b=1', http_headers['ok'], '').status_code)
        self.assertEqual(400, GET('/resource/preview?id=0&sb=abc', http_headers['ok'], '').status_code)
        req = deepcopy(requests_json['calc_preview_ok'])
        req['parameters']['index'] = 'nat_col'
        prev = POST('/api/calc_preview', http_headers['ok'], req)
        url_pr = prev.get_json()['result']['url'] + '&sb=1'
        self.assertEqual(400, GET(url_pr, http_headers['get_preview_ok'], '').status_code)
        self.assertEqual(400, GET('/resource/index', http_headers['ok'], '').status_code)
        self.assertEqual(400, GET('/resource/index?a=1', http_headers['ok'], '').status_code)
        self.assertEqual(400, GET('/resource/index?id=abc', http_headers['ok'], '').status_code)
        self.assertEqual(400, GET('/resource/index?id=-1', http_headers['ok'], '').status_code)
        self.assertEqual(400, GET('/resource/index?id=0&a=1', http_headers['ok'], '').status_code)

        self.assertTrue(http_reason['no_query_string'] in POST('/api/PING?=', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['query_string_necessary'] in GET('/resource/preview', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['query_string_id'] in GET('/resource/preview?a=1', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_id_type_in_query_string'] in GET('/resource/preview?id=abc', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_id_in_query_string'] in GET('/resource/preview?id=-1', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['get_preview_no_sb'] in GET('/resource/preview?id=0', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['get_preview_odd_params'] in GET('/resource/preview?id=0&sb=0&b=1', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['get_preview_inv_sb'] in GET('/resource/preview?id=0&sb=abc', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['get_preview_not_grayscale'] in GET(url_pr, http_headers['get_preview_ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['query_string_necessary'] in GET('/resource/index', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['query_string_id'] in GET('/resource/index?a=1', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_id_type_in_query_string'] in GET('/resource/index?id=abc', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_id_in_query_string'] in GET('/resource/index?id=-1', http_headers['ok'], '').headers.get('Reason'))
        self.assertTrue(http_reason['get_index_odd_params'] in GET('/resource/index?id=0&a=1', http_headers['ok'], '').headers.get('Reason'))
   
    def test_http_headers(self):
        self.assertEqual(400, POST('/api/PING', http_headers['missing_content_type'], '').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['missing_accept'], '').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['missing_proto_v'], '').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['missing_request_id'], '').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['missing_many'], '').status_code)
        self.assertEqual(411, POST('/api/PING', http_headers['missing_content_length'], '').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['inv_content_type'], '').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['inv_accept'], '').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['inv_content_length_type'], '').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['inv_content_length_val1'], '').status_code)
        self.assertEqual(413, POST('/api/PING', http_headers['inv_content_length_val2'], '').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['inv_proto_v'], '').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['inv_request_id_type'], '').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['inv_request_id'], '').status_code)
        prev = POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_ok'])
        url_pr = prev.get_json()['result']['url'] + '&sb=0'
        self.assertEqual(400, GET('/resource/preview?id=0&sb=0', http_headers['missing_accept'], '').status_code)
        self.assertEqual(400, GET('/resource/preview?id=0&sb=0', http_headers['missing_proto_v'], '').status_code)
        self.assertEqual(400, GET('/resource/preview?id=0&sb=0', http_headers['missing_request_id'], '').status_code)
        self.assertEqual(400, GET('/resource/preview?id=0&sb=0', http_headers['inv_accept'], '').status_code)
        self.assertEqual(400, GET('/resource/preview?id=0&sb=0', http_headers['inv_proto_v'], '').status_code)
        self.assertEqual(400, GET('/resource/preview?id=0&sb=0', http_headers['inv_request_id_type'], '').status_code)
        self.assertEqual(400, GET('/resource/preview?id=0&sb=0', http_headers['inv_request_id'], '').status_code)
        self.assertEqual(400, GET('/resource/index?id=0', http_headers['missing_accept'], '').status_code)
        self.assertEqual(400, GET('/resource/index?id=0', http_headers['missing_proto_v'], '').status_code)
        self.assertEqual(400, GET('/resource/index?id=0', http_headers['missing_request_id'], '').status_code)
        self.assertEqual(400, GET('/resource/index?id=0', http_headers['inv_accept'], '').status_code)
        self.assertEqual(400, GET('/resource/index?id=0', http_headers['inv_proto_v'], '').status_code)
        self.assertEqual(400, GET('/resource/index?id=0', http_headers['inv_request_id_type'], '').status_code)
        self.assertEqual(400, GET('/resource/index?id=0', http_headers['inv_request_id'], '').status_code)

        self.assertTrue(http_reason['missing_content_type'] in POST('/api/PING', http_headers['missing_content_type'], '').headers.get('Reason'))
        self.assertTrue(http_reason['missing_accept'] in POST('/api/PING', http_headers['missing_accept'], '').headers.get('Reason'))
        self.assertTrue(http_reason['missing_proto_v'] in POST('/api/PING', http_headers['missing_proto_v'], '').headers.get('Reason'))
        self.assertTrue(http_reason['missing_request_id'] in POST('/api/PING', http_headers['missing_request_id'], '').headers.get('Reason'))
        self.assertTrue(
            http_reason['missing_many1'] in POST('/api/PING', http_headers['missing_many'], '').headers.get('Reason') or
            http_reason['missing_many2'] in POST('/api/PING', http_headers['missing_many'], '').headers.get('Reason')
        )
        self.assertTrue(http_reason['missing_content_length'] in POST('/api/PING', http_headers['missing_content_length'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_content_type'] in POST('/api/PING', http_headers['inv_content_type'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_accept'] in POST('/api/PING', http_headers['inv_accept'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_content_length_type'] in POST('/api/PING', http_headers['inv_content_length_type'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_content_length'] in POST('/api/PING', http_headers['inv_content_length_val1'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_content_length'] in POST('/api/PING', http_headers['inv_content_length_val2'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_proto_v'] in POST('/api/PING', http_headers['inv_proto_v'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_request_id_type'] in POST('/api/PING', http_headers['inv_request_id_type'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_request_id'] in POST('/api/PING', http_headers['inv_request_id'], '').headers.get('Reason'))
        self.assertTrue(http_reason['missing_accept'] in GET('/resource/preview?id=0&sb=0', http_headers['missing_accept'], '').headers.get('Reason'))
        self.assertTrue(http_reason['missing_proto_v'] in GET('/resource/preview?id=0&sb=0', http_headers['missing_proto_v'], '').headers.get('Reason'))
        self.assertTrue(http_reason['missing_request_id'] in GET('/resource/preview?id=0&sb=0', http_headers['missing_request_id'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_accept'] in GET('/resource/preview?id=0&sb=0', http_headers['inv_accept'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_proto_v'] in GET('/resource/preview?id=0&sb=0', http_headers['inv_proto_v'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_request_id_type'] in GET('/resource/preview?id=0&sb=0', http_headers['inv_request_id_type'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_request_id'] in GET('/resource/preview?id=0&sb=0', http_headers['inv_request_id'], '').headers.get('Reason'))
        self.assertTrue(http_reason['missing_accept'] in GET('/resource/index?id=0', http_headers['missing_accept'], '').headers.get('Reason'))
        self.assertTrue(http_reason['missing_proto_v'] in GET('/resource/index?id=0', http_headers['missing_proto_v'], '').headers.get('Reason'))
        self.assertTrue(http_reason['missing_request_id'] in GET('/resource/index?id=0', http_headers['missing_request_id'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_accept'] in GET('/resource/index?id=0', http_headers['inv_accept'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_proto_v'] in GET('/resource/index?id=0', http_headers['inv_proto_v'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_request_id_type'] in GET('/resource/index?id=0', http_headers['inv_request_id_type'], '').headers.get('Reason'))
        self.assertTrue(http_reason['inv_request_id'] in GET('/resource/index?id=0', http_headers['inv_request_id'], '').headers.get('Reason'))
   
    def test_http_body(self):
        self.assertEqual(400, client.post('/api/PING', headers=http_headers['ok'], data='{{"key": "str }').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['ok'], {}).status_code)
        self.assertEqual(400, GET('/resource/preview?id=0&sb=0', http_headers['get_preview_ok'], 'not empty', Width=123, Height=123).status_code)
        self.assertEqual(400, GET('/resource/index?id=0', http_headers['get_index_ok'], 'not empty').status_code)

        self.assertTrue(http_reason['inv_json'] in client.post('/api/PING', headers=http_headers['ok'], data='{{"key": "str }').headers.get('Reason'))
        self.assertTrue(http_reason['empty_json'] in POST('/api/PING', http_headers['ok'], {}).headers.get('Reason'))
        self.assertTrue(http_reason['get_body_not_empty'] in GET('/resource/preview?id=0&sb=0', http_headers['get_preview_ok'], 'not empty', Width=123, Height=123).headers.get('Reason'))
        self.assertTrue(http_reason['get_body_not_empty'] in GET('/resource/index?id=0', http_headers['get_index_ok'], 'not empty').headers.get('Reason'))
    
    ### JSON ONLY ###
    
    ### Common ###
   
    def test_json_ok(self):
        self.assertEqual(0, check_json(requests_json['ping_ok']))
        # self.assertEqual(0, check_json(requests_json['shutdown_ok']))
        self.assertEqual(0, check_json(requests_json['import_gtiff_ok_big']))
        self.assertEqual(0, check_json(requests_json['import_gtiff_ok_mid']))
        self.assertEqual(0, check_json(requests_json['import_gtiff_ok_smol']))
        self.assertEqual(0, check_json(requests_json['import_gtiff_ok_mid2']))
        self.assertEqual(0, check_json(requests_json['import_gtiff_ok_mid3']))
        self.assertEqual(0, check_json(requests_json['import_gtiff_ok_smol2']))
        self.assertEqual(0, check_json(requests_json['import_gtiff_ok_nodata']))
        self.assertEqual(0, check_json(requests_json['calc_preview_ok']))
        self.assertEqual(0, check_json(requests_json['calc_index_ok1']))
        self.assertEqual(0, check_json(requests_json['set_satellite_ok']))
        self.assertEqual(0, check_json(requests_json['end_session_ok']))
        self.prepare()
   
    def test_json_unknown_key(self):
        self.assertEqual(10000, check_json(requests_json['unknown_key1']))
        self.assertEqual(10000, check_json(requests_json['unknown_key2']))
   
    def test_json_missing_key(self):
        self.assertEqual(10001, check_json(requests_json['missing_key1']))
        self.assertEqual(10001, check_json(requests_json['missing_key2']))
        self.assertEqual(10001, check_json(requests_json['missing_key3']))
        self.assertEqual(10001, check_json(requests_json['missing_key4']))
        self.assertEqual(10001, check_json(requests_json['missing_key5']))
   
    def test_json_inv_proto_ver(self):
        self.assertEqual(10002, check_json(requests_json['inv_proto_ver1']))
        self.assertEqual(10002, check_json(requests_json['inv_proto_ver2']))
        self.assertEqual(10002, check_json(requests_json['inv_proto_ver3']))
        self.assertEqual(10002, check_json(requests_json['inv_proto_ver4']))
        self.assertEqual(10002, check_json(requests_json['inv_proto_ver5']))
        self.assertEqual(10002, check_json(requests_json['inv_proto_ver6']))
   
    def test_json_inv_server_ver(self):
        self.assertEqual(10003, check_json(requests_json['inv_serv_ver1']))
        self.assertEqual(10003, check_json(requests_json['inv_serv_ver2']))
        self.assertEqual(10003, check_json(requests_json['inv_serv_ver3']))
        self.assertEqual(10003, check_json(requests_json['inv_serv_ver4']))
        self.assertEqual(10003, check_json(requests_json['inv_serv_ver5']))
        self.assertEqual(10003, check_json(requests_json['inv_serv_ver6']))
   
    def test_json_inv_id(self):
        self.assertEqual(10004, check_json(requests_json['inv_id1']))
        self.assertEqual(10004, check_json(requests_json['inv_id2']))
   
    def test_json_unknown_operation(self):
        self.assertEqual(10005, check_json(requests_json['unknown_operation']))
   
    def test_json_invalid_parameters(self):
        self.assertEqual(10006, check_json(requests_json['inv_params']))
        self.assertEqual(10007, check_json(requests_json['params_missing_key']))
        self.assertEqual(10008, check_json(requests_json['params_unknown_key']))
   
    def test_json_incorrect_proto_version(self):
        self.assertEqual(10009, check_json(requests_json['incorrect_proto_ver']))
   
    def test_json_mismatching_keys(self):
        response = executor.execute(requests_json['ping_ok'])
        response['id'] = 69
        self.assertEqual(10010, proto.match(requests_json['ping_ok'], response)['status'])
   
    def test_json_incorrect_server_version(self):
        self.assertEqual(20000, check_json(requests_json['incorrect_serv_ver']))
   
    def test_json_unsupported_proto_version(self):
        ver = proto.get_version()
        proto.VERSION = '1.0.0'
        self.assertEqual(20001, check_json(requests_json['unsupported_proto_ver']))
        proto.VERSION = ver
   
    def test_json_unsupported_operation(self):
        self.assertEqual(20002, executor.execute(requests_json['unsupported_operation'])['status'])

    # 20003

    ### Operation specific ###
   
    def test_json_ping(self):
        self.assertEqual(10100, check_json(requests_json['ping_non_empty_params']))
   
    def test_json_shutdown(self):
        self.assertEqual(10200, check_json(requests_json['shutdown_non_empty_params']))
        # 20200, 20201
   
    def test_json_import_gtiff(self):
        self.assertEqual(10007, check_json(requests_json['import_gtiff_no_file']))
        self.assertEqual(10007, check_json(requests_json['import_gtiff_no_band']))
        self.assertEqual(10300, check_json(requests_json['import_gtiff_inv_band_type']))
        self.assertEqual(20300, check_json(requests_json['import_gtiff_not_geotiff1']))
        self.assertEqual(20300, check_json(requests_json['import_gtiff_not_geotiff2']))
        self.assertEqual(20300, check_json(requests_json['import_gtiff_not_geotiff3']))
        self.assertEqual(20301, check_json(requests_json['import_gtiff_non_existent']))
   
    def test_json_calc_preview(self):
        self.assertEqual(10007, check_json(requests_json['calc_preview_no_index']))
        self.assertEqual(10007, check_json(requests_json['calc_preview_no_width']))
        self.assertEqual(10007, check_json(requests_json['calc_preview_no_height']))
        self.assertEqual(10400, check_json(requests_json['calc_preview_inv_index_type']))
        self.assertEqual(10401, check_json(requests_json['calc_preview_inv_width_type']))
        self.assertEqual(10401, check_json(requests_json['calc_preview_inv_height_type']))
        self.assertEqual(10402, check_json(requests_json['calc_preview_inv_width']))
        self.assertEqual(10402, check_json(requests_json['calc_preview_inv_height']))
        self.assertEqual(20400, check_json(requests_json['calc_preview_unsupported_index']))
        self.assertEqual(20401, check_json(requests_json['calc_preview_index_not_created']))
        # 20402
   
    def test_json_calc_index(self):
        self.assertEqual(10007, check_json(requests_json['calc_index_no_index']))
        self.assertEqual(10500, check_json(requests_json['calc_index_inv_index_type']))
        self.assertEqual(20500, check_json(requests_json['calc_index_unsupported_index']))
        self.assertEqual(20501, check_json(requests_json['calc_index_not_enough_bands']))
        # 20502

    def test_json_set_satellite(self):
        self.assertEqual(10600, check_json(requests_json['set_satellite_inv_satellite_type']))
        self.assertEqual(20600, check_json(requests_json['set_satellite_unsupported_satellite']))

    def test_json_end_session(self):
        self.assertEqual(10700, check_json(requests_json['end_session_non_empty_params']))

    ### BOTH ###
   
    def test_cross(self):
        self.assertEqual(400, POST('/api/PING', http_headers['ok'], requests_json['shutdown_ok']).status_code)
        hdrs = http_headers['ok'].copy()
        # hdrs['Protocol-Version'] = '420.69.34'
        # self.assertEqual(400, POST('/api/PING', hdrs, requests_json['ping_ok']).status_code)
        # hdrs['Protocol-Version'] = http_headers['ok']['Protocol-Version']
        hdrs['Request-ID'] = 42069
        self.assertEqual(400, POST('/api/PING', hdrs, requests_json['ping_ok']).status_code)

        self.assertTrue(http_reason['endpoint_mismatch'] in POST('/api/PING', http_headers['ok'], requests_json['shutdown_ok']).headers.get('Reason'))
        hdrs = http_headers['ok'].copy()
        # hdrs['Protocol-Version'] = '420.69.34'
        # self.assertTrue(http_reason['proto_v_mismatch'] in POST('/api/PING', hdrs, requests_json['ping_ok']).headers.get('Reason'))
        # hdrs['Protocol-Version'] = http_headers['ok']['Protocol-Version']
        hdrs['Request-ID'] = 42069
        self.assertTrue(http_reason['request_id_mismatch'] in POST('/api/PING', hdrs, requests_json['ping_ok']).headers.get('Reason'))
   
    def test_status_codes(self):
        def _codes(response: 'Response'):
            return response.status_code, \
                   response.get_json().get('status') if response.get_json() else None

        self.assertEqual((200, 0) , _codes(POST('/api/PING', http_headers['ok'], requests_json['ping_ok'])))
        # self.assertEqual((200, 0) , _codes(POST('/api/SHUTDOWN', http_headers['ok'], requests_json['shutdown_ok'])))
        self.assertEqual((200, 0) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_big'])))
        self.assertEqual((200, 0) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_mid'])))
        self.assertEqual((200, 0) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_smol'])))
        self.assertEqual((200, 0) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_mid2'])))
        self.assertEqual((200, 0) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_mid3'])))
        self.assertEqual((200, 0) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_smol2'])))
        self.assertEqual((200, 0) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok_nodata'])))
        self.assertEqual((200, 0) , _codes(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_ok'])))
        self.assertEqual((200, 0) , _codes(POST('/api/calc_index', http_headers['ok'], requests_json['calc_index_ok1'])))
        self.assertEqual((200, 0) , _codes(POST('/api/set_satellite', http_headers['ok'], requests_json['set_satellite_ok'])))
        self.assertEqual((200, 0) , _codes(POST('/api/end_session', http_headers['ok'], requests_json['end_session_ok'])))
        self.prepare()

        self.assertEqual((400, 10000) , _codes(POST('/api/PING', http_headers['ok'], requests_json['unknown_key1'])))
        self.assertEqual((400, 10000) , _codes(POST('/api/PING', http_headers['ok'], requests_json['unknown_key2'])))

        self.assertEqual((400, 10001) , _codes(POST('/api/PING', http_headers['ok'], requests_json['missing_key1'])))
        self.assertEqual((400, 10001) , _codes(POST('/api/PING', http_headers['ok'], requests_json['missing_key2'])))
        self.assertEqual((400, 10001) , _codes(POST('/api/PING', http_headers['ok'], requests_json['missing_key3'])))
        self.assertEqual((400, 10001) , _codes(POST('/api/PING', http_headers['ok'], requests_json['missing_key4'])))
        self.assertEqual((400, 10001) , _codes(POST('/api/PING', http_headers['ok'], requests_json['missing_key5'])))

        self.assertEqual((400, None) , _codes(POST('/api/PING', http_headers['inv_proto_v'], requests_json['inv_proto_ver1'])))

        self.assertEqual((400, 10003) , _codes(POST('/api/PING', http_headers['ok'], requests_json['inv_serv_ver1'])))
        self.assertEqual((400, 10003) , _codes(POST('/api/PING', http_headers['ok'], requests_json['inv_serv_ver2'])))
        self.assertEqual((400, 10003) , _codes(POST('/api/PING', http_headers['ok'], requests_json['inv_serv_ver3'])))
        self.assertEqual((400, 10003) , _codes(POST('/api/PING', http_headers['ok'], requests_json['inv_serv_ver4'])))
        self.assertEqual((400, 10003) , _codes(POST('/api/PING', http_headers['ok'], requests_json['inv_serv_ver5'])))
        self.assertEqual((400, 10003) , _codes(POST('/api/PING', http_headers['ok'], requests_json['inv_serv_ver6'])))

        self.assertEqual((400, None) , _codes(POST('/api/PING', http_headers['inv_request_id_type'], requests_json['inv_id1'])))
        self.assertEqual((400, None) , _codes(POST('/api/PING', http_headers['inv_request_id'], requests_json['inv_id1'])))

        self.assertEqual((400, None) , _codes(POST('/api/PIG', http_headers['ok'], requests_json['ping_ok'])))

        self.assertEqual((400, 10006) , _codes(POST('/api/PING', http_headers['ok'], requests_json['inv_params'])))

        self.assertEqual((400, 10007), _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['params_missing_key'])))

        self.assertEqual((400, 10008), _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['params_unknown_key'])))

        self.assertEqual((400, None) , _codes(POST('/api/PING', http_headers['inv_proto_v'], requests_json['ping_ok'])))

        # mismatching keys ???

        self.assertEqual((500, 20000) , _codes(POST('/api/PING', http_headers['ok'], requests_json['incorrect_serv_ver'])))

        proto_v = proto.get_version()
        hdrs = http_headers['ok'].copy()
        proto.VERSION = requests_json['unsupported_proto_ver']['proto_version']
        hdrs['Protocol-Version'] = requests_json['unsupported_proto_ver']['proto_version']
        self.assertEqual((500, 20001) , _codes(POST('/api/PING', hdrs, requests_json['unsupported_proto_ver'])))
        proto.VERSION = proto_v
        hdrs['Protocol-Version'] = proto_v
        
        self.assertEqual((400, None) , _codes(POST('/api/new_operation', http_headers['ok'], requests_json['unsupported_operation'])))
        self.assertEqual((400, None) , _codes(GET('/resource/unsupported?id=0', http_headers['ok'], '')))

        self.assertEqual((400, None) , _codes(POST('/api/PING?=', http_headers['ok'], requests_json['ping_ok'])))
        self.assertEqual((400, None) , _codes(GET('/resource/preview', http_headers['ok'], '')))
        self.assertEqual((400, None) , _codes(GET('/resource/preview?a=1&b=2', http_headers['ok'], '')))
        self.assertEqual((400, None) , _codes(GET('/resource/preview?id=abc', http_headers['ok'], '')))
        
        # 20003

        # 20004 is checked in test_000

        self.assertEqual((400, 10100) , _codes(POST('/api/PING', http_headers['ok'], requests_json['ping_non_empty_params'])))

        self.assertEqual((400, 10200) , _codes(POST('/api/SHUTDOWN', http_headers['ok'], requests_json['shutdown_non_empty_params'])))
        # 20200, 20201

        self.assertEqual((400, 10007) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_no_file'])))
        self.assertEqual((400, 10007) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_no_band'])))
        self.assertEqual((400, 10300) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_inv_band_type'])))
        self.assertEqual((500, 20300) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_not_geotiff1'])))
        self.assertEqual((500, 20300) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_not_geotiff2'])))
        self.assertEqual((500, 20300) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_not_geotiff3'])))
        self.assertEqual((500, 20301) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_non_existent'])))

        self.assertEqual((400, 10007), _codes(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_no_index'])))
        self.assertEqual((400, 10007), _codes(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_no_width'])))
        self.assertEqual((400, 10007), _codes(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_no_height'])))
        self.assertEqual((400, 10400), _codes(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_inv_index_type'])))
        self.assertEqual((400, 10401), _codes(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_inv_width_type'])))
        self.assertEqual((400, 10401), _codes(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_inv_height_type'])))
        self.assertEqual((400, 10402), _codes(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_inv_width'])))
        self.assertEqual((400, 10402), _codes(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_inv_height'])))
        self.assertEqual((400, 20400), _codes(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_unsupported_index'])))
        self.assertEqual((500, 20401), _codes(POST('/api/calc_preview', http_headers['ok'], requests_json['calc_preview_index_not_created'])))
        # 20402

        self.assertEqual((400, 10007) , _codes(POST('/api/calc_index', http_headers['ok'], requests_json['calc_index_no_index'])))
        self.assertEqual((400, 10500) , _codes(POST('/api/calc_index', http_headers['ok'], requests_json['calc_index_inv_index_type'])))
        self.assertEqual((400, 20500) , _codes(POST('/api/calc_index', http_headers['ok'], requests_json['calc_index_unsupported_index'])))
        self.assertEqual((500, 20501) , _codes(POST('/api/calc_index', http_headers['ok'], requests_json['calc_index_not_enough_bands'])))
        # 20502

        self.assertEqual((400, 10600) , _codes(POST('/api/set_satellite', http_headers['ok'], requests_json['set_satellite_inv_satellite_type'])))
        self.assertEqual((500, 20600) , _codes(POST('/api/set_satellite', http_headers['ok'], requests_json['set_satellite_unsupported_satellite'])))

        self.assertEqual((400, 10700) , _codes(POST('/api/end_session', http_headers['ok'], requests_json['end_session_non_empty_params'])))

    ### DIFFERENT FILES ###

    # def test_calc_preview_files(self):
    #     f = deepcopy(requests_json['calc_preview_ok'])

    #     f['parameters']['ids'][0] = self.gtiffbig
    #     f['parameters']['ids'][1] = self.gtiffbig
    #     f['parameters']['ids'][2] = self.gtiffbig
    #     self.assertEqual(0, executor.execute(f)['status'])
    #     f['parameters']['ids'][0] = self.gtiffmid
    #     f['parameters']['ids'][1] = self.gtiffmid
    #     f['parameters']['ids'][2] = self.gtiffmid
    #     self.assertEqual(0, executor.execute(f)['status'])
    #     f['parameters']['ids'][0] = self.gtiffsmol
    #     f['parameters']['ids'][1] = self.gtiffsmol
    #     f['parameters']['ids'][2] = self.gtiffsmol
    #     self.assertEqual(0, executor.execute(f)['status'])
    #     f['parameters']['ids'][0] = self.gtiffmid2
    #     f['parameters']['ids'][1] = self.gtiffmid2
    #     f['parameters']['ids'][2] = self.gtiffmid2
    #     self.assertEqual(0, executor.execute(f)['status'])
    #     f['parameters']['ids'][0] = self.gtiffsmol2
    #     f['parameters']['ids'][1] = self.gtiffsmol2
    #     f['parameters']['ids'][2] = self.gtiffsmol2
    #     self.assertEqual(0, executor.execute(f)['status'])
    #     f['parameters']['ids'][0] = self.gtiffempty
    #     f['parameters']['ids'][1] = self.gtiffempty
    #     f['parameters']['ids'][2] = self.gtiffempty
    #     self.assertEqual(0, executor.execute(f)['status'])

    # def test_calc_index_files(self):
    #     f = deepcopy(requests_json['calc_index_ok1'])

    #     f['parameters']['ids'][0] = self.gtiffbig
    #     f['parameters']['ids'][1] = self.gtiffbig
    #     self.assertEqual(0, executor.execute(f)['status'])
    #     f['parameters']['ids'][0] = self.gtiffmid
    #     f['parameters']['ids'][1] = self.gtiffmid
    #     self.assertEqual(0, executor.execute(f)['status'])
    #     f['parameters']['ids'][0] = self.gtiffsmol
    #     f['parameters']['ids'][1] = self.gtiffsmol
    #     self.assertEqual(0, executor.execute(f)['status'])
    #     f['parameters']['ids'][0] = self.gtiffmid2
    #     f['parameters']['ids'][1] = self.gtiffmid2
    #     self.assertEqual(0, executor.execute(f)['status'])
    #     f['parameters']['ids'][0] = self.gtiffsmol2
    #     f['parameters']['ids'][1] = self.gtiffsmol2
    #     self.assertEqual(0, executor.execute(f)['status'])
    #     f['parameters']['ids'][0] = self.gtiffempty
    #     f['parameters']['ids'][1] = self.gtiffempty
    #     self.assertEqual(0, executor.execute(f)['status'])

if __name__ == '__main__':
    unittest.main()
