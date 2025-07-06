import unittest
import socket
from json_proto import Protocol
from gdal_executor import GdalExecutor

proto = Protocol(socket.socket())
proto_version = proto.get_version()
executor = GdalExecutor(proto_version)
server_version = executor.get_version()

def check(request):
    response = proto.validate(request)
    if response.get('status') != 0:
        return response.get('status')
    response = executor.execute(request)
    if response.get('status') != 0:
        return response.get('status')
    response = proto.match(request, response)
    return response.get('status')

requests = {
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
    'missing_key4': {
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
    }
    # shutdown other
}

class Test(unittest.TestCase):
    ### Common ###

    def test_ok(self):
        self.assertEqual(0, check(requests['ping_ok']))
        self.assertEqual(0, check(requests['shutdown_ok']))

    def test_unknown_key(self):
        self.assertEqual(10000, check(requests['unknown_key1']))
        self.assertEqual(10000, check(requests['unknown_key2']))

    def test_missing_key(self):
        self.assertEqual(10001, check(requests['missing_key1']))
        self.assertEqual(10001, check(requests['missing_key2']))
        self.assertEqual(10001, check(requests['missing_key3']))
        self.assertEqual(10001, check(requests['missing_key4']))

    def test_inv_proto_ver(self):
        self.assertEqual(10002, check(requests['inv_proto_ver1']))
        self.assertEqual(10002, check(requests['inv_proto_ver2']))
        self.assertEqual(10002, check(requests['inv_proto_ver3']))
        self.assertEqual(10002, check(requests['inv_proto_ver4']))
        self.assertEqual(10002, check(requests['inv_proto_ver5']))
        self.assertEqual(10002, check(requests['inv_proto_ver6']))

    def test_inv_server_ver(self):
        self.assertEqual(10003, check(requests['inv_serv_ver1']))
        self.assertEqual(10003, check(requests['inv_serv_ver2']))
        self.assertEqual(10003, check(requests['inv_serv_ver3']))
        self.assertEqual(10003, check(requests['inv_serv_ver4']))
        self.assertEqual(10003, check(requests['inv_serv_ver5']))
        self.assertEqual(10003, check(requests['inv_serv_ver6']))

    def test_inv_id(self):
        self.assertEqual(10004, check(requests['inv_id1']))
        self.assertEqual(10004, check(requests['inv_id2']))

    def test_unknown_operation(self):
        self.assertEqual(10005, check(requests['unknown_operation']))

    def test_invalid_parameters(self):
        self.assertEqual(10006, check(requests['inv_params']))

    def test_incorrect_proto_version(self):
        self.assertEqual(10009, check(requests['incorrect_proto_ver']))

    def test_mismatching_keys(self):
        response = executor.execute(requests['ping_ok'])
        response['id'] = 69
        self.assertEqual(10010, proto.match(requests['ping_ok'], response)['status'])

    def test_incorrect_server_version(self):
        self.assertEqual(20000, check(requests['incorrect_serv_ver']))

    def test_unsupported_proto_version(self):
        ver = proto.get_version()
        proto.VERSION = '1.0.0'
        self.assertEqual(20001, check(requests['unsupported_proto_ver']))
        proto.VERSION = ver

    def test_unsupported_operation(self):
        self.assertEqual(20002, executor.execute(requests['unsupported_operation'])['status'])

    ### Operation specific ###

    def test_ping_non_empty_parameters(self):
        self.assertEqual(10100, check(requests['ping_non_empty_params']))

    def test_shutdown_non_empty_parameters(self):
        self.assertEqual(10200, check(requests['shutdown_non_empty_params']))

    # shutdown other

if __name__ == '__main__':
    unittest.main()
