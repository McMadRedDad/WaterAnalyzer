# 1. Test HTTP part only, without JSON
# 2. Test JSON part only, without HTTP
# 3. Test both together

import unittest
from werkzeug.test import EnvironBuilder
from server import server, proto, executor, generate_http_response

server.testing = True
client = server.test_client()
proto_version = proto.get_version()
server_version = executor.get_version()

# Substrings of the Reason HTTP header that contains HTTP-level error description. Most HTTP-level errors return 400 response, so checking only the status code is not enough.
http_reason = {
    'unknown_endpoint': 'Unknown/unsupported command ',
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
    'inv_json': ' is not a valid JSON.',
    'empty_json': ' must not be an empty JSON document ',
    'endpoint_mismatch': ' does not match to the endpoint ',
    'proto_v_mismatch': 'Protocol versions do not match ',
    'request_id_mismatch': 'Request ids do not match '
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
    'import_gtiff_ok1': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['gtiff_ok1']
        }
    },
    'import_gtiff_ok2': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['gtiff_ok2']
        }
    },
    'import_gtiff_non_existent': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['non_existent']
        }
    },
    'import_gtiff_not_geotiff1': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['saga_grid']
        }
    },
    'import_gtiff_not_geotiff2': {
        "proto_version": proto_version,
        "server_version": server_version,
        "id": 0,
        "operation": "import_gtiff",
        "parameters": {
            "file": test_files['shape']
        }
    }
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

    ### HTTP ONLY ###

    def test_http_ok(self):
        self.assertEqual(200, POST('/api/PING', http_headers['ok'], requests_json['ping_ok']).status_code)
        self.assertEqual(200, POST('/api/SHUTDOWN', http_headers['ok'], requests_json['shutdown_ok']).status_code)
        self.assertEqual(200, POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok1']).status_code)
        self.assertEqual(200, POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok2']).status_code)
        
        self.assertIsNone(POST('/api/PING', http_headers['ok'], requests_json['ping_ok']).headers.get('Reason'))
        self.assertIsNone(POST('/api/SHUTDOWN', http_headers['ok'], requests_json['shutdown_ok']).headers.get('Reason'))
        self.assertIsNone(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok1']).headers.get('Reason'))
        self.assertIsNone(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok2']).headers.get('Reason'))

    def test_http_endpoint(self):
        self.assertEqual(400, POST('/api/unsupported', http_headers['ok'], '').status_code)
        self.assertTrue(http_reason['unknown_endpoint'] in POST('/api/unsupported', http_headers['ok'], '').headers.get('Reason'))

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

    def test_http_body(self):
        self.assertEqual(400, client.post('/api/PING', headers=http_headers['ok'], data='{{"key": "str }').status_code)
        self.assertEqual(400, POST('/api/PING', http_headers['ok'], {}).status_code)

        self.assertTrue(http_reason['inv_json'] in client.post('/api/PING', headers=http_headers['ok'], data='{{"key": "str }').headers.get('Reason'))
        self.assertTrue(http_reason['empty_json'] in POST('/api/PING', http_headers['ok'], {}).headers.get('Reason'))
    
    ### JSON ONLY ###
    
    ### Common ###

    def test_json_ok(self):
        self.assertEqual(0, check_json(requests_json['ping_ok']))
        self.assertEqual(0, check_json(requests_json['shutdown_ok']))
        self.assertEqual(0, check_json(requests_json['import_gtiff_ok1']))
        self.assertEqual(0, check_json(requests_json['import_gtiff_ok2']))

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

    ### Operation specific ###

    def test_json_ping(self):
        self.assertEqual(10100, check_json(requests_json['ping_non_empty_params']))

    def test_json_shutdown(self):
        self.assertEqual(10200, check_json(requests_json['shutdown_non_empty_params']))
        # shutdown other

    def test_json_import_gtiff(self):
        self.assertEqual(20300, check_json(requests_json['import_gtiff_not_geotiff1']))
        self.assertEqual(20300, check_json(requests_json['import_gtiff_not_geotiff2']))
        self.assertEqual(20301, check_json(requests_json['import_gtiff_non_existent']))

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
        self.assertEqual((200, 0) , _codes(POST('/api/SHUTDOWN', http_headers['ok'], requests_json['shutdown_ok'])))
        self.assertEqual((200, 0) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok1'])))
        self.assertEqual((200, 0) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_ok2'])))

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

        # mismatching keys

        self.assertEqual((500, 20000) , _codes(POST('/api/PING', http_headers['ok'], requests_json['incorrect_serv_ver'])))

        proto_v = proto.get_version()
        hdrs = http_headers['ok'].copy()
        proto.VERSION = requests_json['unsupported_proto_ver']['proto_version']
        hdrs['Protocol-Version'] = requests_json['unsupported_proto_ver']['proto_version']
        self.assertEqual((500, 20001) , _codes(POST('/api/PING', hdrs, requests_json['unsupported_proto_ver'])))
        proto.VERSION = proto_v
        hdrs['Protocol-Version'] = proto_v
        
        self.assertEqual((400, None) , _codes(POST('/api/new_operation', http_headers['ok'], requests_json['unsupported_operation'])))
        
        #  20003

        self.assertEqual((400, 10100) , _codes(POST('/api/PING', http_headers['ok'], requests_json['ping_non_empty_params'])))

        self.assertEqual((400, 10200) , _codes(POST('/api/PING', http_headers['ok'], requests_json['shutdown_non_empty_params'])))
        # 20200, 20201

        self.assertEqual((500, 20300) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_not_geotiff1'])))
        self.assertEqual((500, 20300) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_not_geotiff2'])))
        self.assertEqual((500, 20301) , _codes(POST('/api/import_gtiff', http_headers['ok'], requests_json['import_gtiff_non_existent'])))

if __name__ == '__main__':
    unittest.main()
