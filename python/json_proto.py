class Protocol:
    VERSION = '3.0.3'
    SUPPORTED_OPERATIONS = ('PING', 'SHUTDOWN', 'import_gtiff', 'calc_preview', 'calc_index', 'set_satellite', 'end_session', 'import_metafile')

    def __init__(self):
        print(f'Using protocol version {self.VERSION}')

    def validate(self, request: dict) -> dict:
        """Checks for all protocol-specific request errors related to message structure, spelling, etc. and returns a dictionary. Does not check for data-specific errors (e.g. non-existent image id, server version, etc.).
        Must be called first to validate the request."""

        proto_version = request.get('proto_version')
        server_version = request.get('server_version')
        id_ = request.get('id')
        operation = request.get('operation')
        parameters = request.get('parameters')
        status = 0
        result = {}
        
        def _non_standard_response(request: dict, status: int, result: dict) -> dict:
            response = {}
            for k, v in request.items():
                response[k] = v
            response['status'] = status
            response['result'] = result
            return response

        def _response(status: int, result: dict) -> dict:
            return {
                'proto_version': self.VERSION,
                'server_version': server_version,
                'id': id_,
                'status': status,
                'result': result
            }

        def _check_param_keys(operation: str, correct_keys: list, keys_to_check: list) -> dict:
            present_keys = []
            for key in keys_to_check:
                if key not in correct_keys:
                    return _response(10008, {"error": f"unknown key '{key}' in parameters for '{operation}' operation"})
                else:
                    present_keys.append(key)
            if len(present_keys) != len(correct_keys):
                diff = set(correct_keys) - set(present_keys)
                return _response(10007, {"error": f"keys '{diff}' are not specified in parameters for '{operation}' operation"})
            return {}

        ### Common errors ###
        keys = list(request.keys())
        correct_keys = ['proto_version', 'server_version', 'id', 'operation', 'parameters']
        present_keys = []
        for key in keys:
            if key not in correct_keys:
                return _non_standard_response(request, 10000, {"error": f"key '{key}' is unknown"})
            else:
                present_keys.append(key)
        
        if len(keys) != len(correct_keys):
            diff = set(correct_keys) - set(present_keys)
            return _non_standard_response(request, 10001, {"error": f"keys '{diff}' are not specified"})
                    
        if type(proto_version) is not str:
            return _response(10002, {"error": f"invalid protocol version string: '{proto_version}'"})
        digits = proto_version.split('.')
        if len(digits) != 3:
            return _response(10002, {"error": f"invalid protocol version string: '{proto_version}'"})   
        for i in range(3):
            try:
                digits[i] = int(digits[i])
            except ValueError:
                return _response(10002, {"error": f"invalid protocol version string: '{proto_version}'"})

        if type(server_version) is not str:
            return _response(10003, {"error": f"invalid server version string: '{server_version}'"})
        digits = server_version.split('.')
        if len(digits) != 3:
            return _response(10003, {"error": f"invalid server version string: '{server_version}'"})
        for i in range(3):
            try:
                digits[i] = int(digits[i])
            except ValueError:
                return _response(10003, {"error": f"invalid server version string: '{server_version}'"})
                    
        if type(id_) is not int:
            return _response(10004, {"error": f"invalid request id: '{id_}'"})
            
        if operation not in self.SUPPORTED_OPERATIONS:
            return _response(10005, {"error": f"unknown operation '{operation}' requested"})
            
        if type(parameters) is not dict:
            return _response(10006, {"error": "invalid 'parameters' key: must be of JSON object type"})
            
        if proto_version != self.VERSION:
            return _response(10009, {"error": f"incorrect protocol version: '{proto_version}'. The current protocol version is {self.VERSION}"})

        if operation == 'PING':
            if len(parameters) != 0:
                return _response(10100, {"error": "'parameters' must be an empty JSON object for 'PING' request"})
            return _response(0, {})

        if operation == 'SHUTDOWN':
            if len(parameters) != 0:
                return _response(10200, {"error": "'parameters' must be an empty JSON object for 'SHUTDOWN' request"})
            return _response(0, {})

        if operation == 'import_gtiff':
            params_check = _check_param_keys('import_gtiff', ['file', 'band'], list(parameters.keys()))
            if len(params_check) != 0: 
                return params_check
            band = parameters['band']
            if type(band) is not str:
                return _response(10300, {"error": "invalid 'band' key: must be of string type"})
            return _response(0, {})
            
        if operation == 'calc_preview':
            params_check = _check_param_keys('calc_preview', ['index', 'width', 'height'], list(parameters.keys()))
            if len(params_check) != 0: 
                return params_check
            index, width, height = parameters['index'], parameters['width'], parameters['height']
            if type(index) is not str:
                return _response(10400, {"error": "invalid 'index' key: must be of string type"})
            if type(width) is not int:
                return _response(10401, {"error": "invalid 'width' key: must be of integer type"})
            if type(height) is not int:
                return _response(10401, {"error": "invalid 'height' key: must be of integer type"})
            if width <= 0:
                return _response(10402, {"error": f"invalid width '{width}' in 'width' key: must be > 0"})
            if height <= 0:
                return _response(10402, {"error": f"invalid height '{height}' in 'height' key: must be > 0"})
            return _response(0, {})

        if operation == 'calc_index':
            params_check = _check_param_keys('calc_index', ['index'], list(parameters.keys()))
            if len(params_check) != 0:
                return params_check
            index = parameters['index']
            if type(index) is not str:
                return _response(10500, {"error": "invalid 'index' key: must be of string type"})
            return _response(0, {})

        if operation == 'set_satellite':
            params_check = _check_param_keys('set_satellite', ['satellite', 'proc_level'], list(parameters.keys()))
            if len(params_check) != 0:
                return params_check
            satellite, proc_level = parameters['satellite'], parameters['proc_level']
            if type(satellite) is not str:
                return _response(10600, {"error": "invalid 'satellite' key: must be of string type"})
            if type(proc_level) is not str:
                return _response(10601, {"error": "invalid 'proc_level' key: must be of string type"})
            return _response(0, {})

        if operation == 'end_session':
            if len(parameters) != 0:
                return _response(10700, {"error": "'parameters' must be an empty JSON object for 'end_session' request"})
            return _response(0, {})

        if operation == 'import_metafile':
            params_check = _check_param_keys('import_metafile', ['file'], list(parameters.keys()))
            if len(params_check) != 0:
                return params_check
            return _response(0, {})
        
        return _response(-1, {"error": "how's this even possible?"})

    def match(self, request: dict, result: dict) -> dict:
        """Checks if 'result' corresponds to 'request' and returns a dictionary.
        Must be called after 'Protocol.validate' and 'GdalExecutor.execute'."""

        proto_version = request.get('proto_version')
        server_version = request.get('server_version')
        id_ = request.get('id')

        def _response(status: int, result: dict) -> dict:
            return {
                'proto_version': self.VERSION,
                'server_version': server_version,
                'id': id_,
                'status': status,
                'result': result
            }

        if proto_version != result['proto_version']:
            return _response(10010, {"error": "values 'proto_version' do not match in request and response"})
        if server_version != result['server_version']:
            return _response(10010, {"error": "values 'server_version' do not match in request and response"})
        if id_ != result['id']:
            return _response(10010, {"error": "values 'id' do not match in request and response"})

        return _response(result['status'], result['result'])

    def get_version(self) -> str:
        return self.VERSION

    def get_supported_operations(self) -> tuple[str]:
        return self.SUPPORTED_OPERATIONS
