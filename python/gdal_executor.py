from osgeo import gdal
import numpy as np
gdal.UseExceptions()

# thread-safe in the future
class DatasetManager:
    def __init__(self):
        self._datasets = {}
        self._counter = 0
        # mutex

    def open(self, file: str) -> int:
        """Tries to open 'file' as a GDAL dataset and returns its id to be used with 'get' method."""

        try:
            dataset = gdal.Open(file, gdal.GA_ReadOnly)
        except RuntimeError:
            raise RuntimeError(f'Cannot open file {file}')
        self._datasets[self._counter] = dataset
        self._counter += 1
        return self._counter - 1

    def close(self, id: int) -> None:
        try:
            dataset = self._datasets.pop(id)
        except KeyError:
            raise KeyError(f'Dataset {id} is not opened but "close" method called')
        dataset = None

    def get(self, id: int) -> gdal.Dataset:
        try:
            return self._datasets[id]
        except KeyError:
            raise KeyError(f'Dataset {id} is not opened but "get" method called')

class GdalExecutor:
    SUPPORTED_PROTOCOL_VERSIONS = ('2.0.1')
    VERSION = '1.0.0'
    
    def __new__(cls, protocol):
        if protocol.get_version() not in GdalExecutor.SUPPORTED_PROTOCOL_VERSIONS:
            return None
        return super().__new__(cls)
    
    def __init__(self, protocol: str):
        self.proto_version = protocol.get_version()
        self.supported_operations = protocol.get_supported_operations()
        self.ds_man = DatasetManager()
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
        
        if operation not in self.supported_operations:
            return _response(20002, {"error": f"unsupported operation '{operation}' requested. Supported operations are {self.supported_operations}"})
        
        if operation == 'PING':
            return _response(0, {"data": "PONG"})

        if operation == 'SHUTDOWN':
            # errors 20200 and 20201
            return _response(0, {})

        if operation == 'import_gtiff':
            try:
                dataset_id = self.ds_man.open(parameters['file'])
                dataset = self.ds_man.get(dataset_id)
            except RuntimeError:
                return _response(20301, {"error": f"failed to open file '{parameters['file']}'"})
            if dataset.GetDriver().ShortName != 'GTiff':
                return _response(20300, {"error": f"provided file '{parameters['file']}' is not a GeoTiff image"})
            
            geotransform = dataset.GetGeoTransform()
            result = {
                'id': dataset_id,
                'info': {
                    'width': dataset.RasterXSize,
                    'height': dataset.RasterYSize,
                    'projection': f'{dataset.GetSpatialRef().GetAuthorityName(None)}:{dataset.GetSpatialRef().GetAuthorityCode(None)}',
                    'unit': dataset.GetSpatialRef().GetAttrValue('UNIT', 0),
                    'origin': [geotransform[0], geotransform[3]],
                    'pixel_size': [geotransform[1], geotransform[5]]
                }
            }
            # self.ds_man.close(dataset_id)
            return _response(0, result)

        if operation == 'calc_preview':
            ds = []
            for i in range(3):
                try:
                    ds.append(self.ds_man.get(parameters['ids'][i]))
                except KeyError:
                    return _response(20500, {"error": f"id {parameters['ids'][i]} provided in 'ids' key does not exist"})
            if not (
                ds[0].RasterXSize == ds[1].RasterXSize == ds[2].RasterXSize and
                ds[0].RasterYSize == ds[1].RasterYSize == ds[2].RasterYSize
            ):
                return _response(20501, {"error": "unable to create a preview from requested ids: rasters do not match in size"})
            
            rgb = []
            for i in range(3):
                band = ds[i].GetRasterBand(1)
                rgb.append(band.ReadAsArray(win_ysize=1))
                for j in range(1, ds[i].RasterYSize - 1):
                    scanline = band.ReadAsArray(yoff=j, win_ysize=1)[0]
                    rgb[i] = np.vstack((rgb[i], scanline))

            with open('tmp', 'w') as f:
                f.write(rgb[0])

            return _response(0, {"data": "ok"})
            # error 20502
        
        return _response(-1, {"error": "how's this even possible?"})
    
    def get_supported_protocol_versions(self) -> tuple:
        return self.SUPPORTED_PROTOCOL_VERSIONS

    def get_supported_operations(self) -> tuple:
        return self.supported_operations

    def get_version(self) -> str:
        return self.VERSION
