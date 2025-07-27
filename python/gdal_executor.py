from osgeo import gdal

gdal.UseExceptions()

class GdalExecutor:
    SUPPORTED_PROTOCOL_VERSIONS = ('2.0.0')
    SUPPORTED_OPERATIONS = ('PING', 'SHUTDOWN', 'import_gtiff', 'export_gtiff', 'calc_preview', 'calc_index')
    VERSION = '1.0.0'
    
    def __new__(cls, protocol_version):
        if protocol_version not in GdalExecutor.SUPPORTED_PROTOCOL_VERSIONS:
            return None
        return super().__new__(cls)
    
    def __init__(self, protocol_version: str):
        self.proto_version = protocol_version
        print(f'Server running version {self.VERSION}')

    def execute(self, request: dict) -> dict:
        """Processes the request and returns a dictionary to be used by Protocol.send method.
        Must be called after 'Protocol.validate'.
        The dictionary returned is guaranteed to be valid according to the protocol used."""

        proto_version = request['proto_version']
        server_version = request['server_version']
        id_ = request['id']
        operation = request['operation']
        parameters = request['parameters']
        status = 0
        result = {}

        def _response(status: int, result: dict) -> dict:
            return {
                'proto_version': proto_version,
                'server_version': self.VERSION,
                'id': id_,
                'status': status,
                'result': result
            }

        if server_version != self.VERSION:
            return _response(20000, {"error": f"incorrect server version: '{server_version}'. The server runs version {self.VERSION}"})
        
        if proto_version not in self.SUPPORTED_PROTOCOL_VERSIONS:
            return _response(20001, {"error": f"unsupported protocol version: '{proto_version}'. The server understands protocol versions {self.SUPPORTED_PROTOCOL_VERSIONS}"})
        
        if operation not in self.SUPPORTED_OPERATIONS:
            return _response(20002, {"error": f"unsupported operation '{operation}' requested. Supported operations are {self.SUPPORTED_OPERATIONS}"})
        
        if operation == 'PING':
            return _response(0, {"data": "PONG"})

        if operation == 'SHUTDOWN':
            # errors 20200 and 20201
            return _response(0, {})

        if operation == 'import_gtiff':
            try:
                dataset = gdal.Open(parameters['file'])
            except RuntimeError:
                return _response(20301, {"error": f"failed to open file '{parameters['file']}'"})

            # 20300 error
            
            geotransform = dataset.GetGeoTransform()
            result = {'id': None, 'metadata': {
                'width': dataset.RasterXSize,
                'height': dataset.RasterYSize,
                'projection': dataset.GetProjection(),
                'origin': [geotransform[0], geotransform[3]],
                'pixel_size': [geotransform[1], geotransform[5]]
            }}
            dataset = None
            return _response(0, result)
        
        return _response(-1, {"error": "how's this even possible?"})
    
    def get_supported_protocol_versions(self) -> tuple:
        return self.SUPPORTED_PROTOCOL_VERSIONS

    def get_supported_operations(self) -> tuple:
        return self.SUPPORTED_OPERATIONS

    def get_version(self) -> str:
        return self.VERSION
