from osgeo import gdal
import numpy as np
from math import isclose
import index_calculator as indcal
gdal.UseExceptions()

class PreviewManager:
    def __init__(self):
        self._previews = {}
        self._counter = 0

    def add(self, array: np.ndarray) -> int:
        """Stores a new numpy array referring to a preview image and returns its id."""

        self._previews[self._counter] = array
        self._counter += 1
        return self._counter - 1

    def remove(self, id: int) -> None:
        try:
            self._previews.pop(id)
        except KeyError:
            raise KeyError(f'Preview {id} does not exist but "remove" method called')

    def get(self, id: int) -> np.ndarray:
        try:
            return self._previews[id]
        except KeyError:
            raise KeyError(f'Preview {id} does not exist but "get" method called')

# thread-safe in the future
class DatasetManager:
    def __init__(self):
        self._datasets = {}
        self._counter = 0
        # mutex

    def open(self, file: str) -> int:
        """Tries to open 'file' as a GDAL dataset and returns its generated id."""

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

    def read_band(self, dataset_id: int, band_id: int, step_size_percent: float | int) -> np.ndarray:
        """Reads a band from the dataset and returns it as a numpy array.
        'step_size' is the percent of the raster's rows or columns that will be read during one iteration. For example, if the raster is 100x100 pixels and 'step_size'=20, the band will be read entirely with 5 iterations by five 20x100 windows.
        'step_size' <=0 means the band will be read line by line. 'step_size' >=100 means the band will be read at once.
        The less 'step_size' is, the less memory is used and the slower the function is."""

        try:
            ds = self.get(dataset_id)
            band = ds.GetRasterBand(band_id)
        except KeyError:
            raise KeyError(f'Dataset {dataset_id} is not opened but "read_band" method called')

        x_size, y_size, step, data = ds.RasterXSize, ds.RasterYSize, 0, 0
        if (
            isclose(0, step_size_percent, abs_tol=0.01) or
            step_size_percent < 0
        ):
            step = 1
        elif (
            isclose(100, step_size_percent, abs_tol=0.01) or
            step_size_percent > 100
        ):
            step = x_size - 1 if x_size >= y_size else y_size - 1
        else:
            step = int(x_size * step_size_percent/100) if x_size >= y_size else int(y_size * step_size_percent/100)
            if step == 0:
                step = 1

        # we'll read along the side that is shorter
        # e.g. raster size 100x50 -> read along y=50
        if x_size >= y_size:
            data = band.ReadAsArray(xoff=0, yoff=0, win_xsize=x_size, win_ysize=1)
            for i in range(1, y_size, step):
                if y_size >= i + step:
                    win = band.ReadAsArray(xoff=0, yoff=i, win_xsize=x_size, win_ysize=step)
                else:
                    win = band.ReadAsArray(xoff=0, yoff=i, win_xsize=x_size, win_ysize=y_size - i)
                data = np.vstack((data, win))
        else:
            data = band.ReadAsArray(xoff=0, yoff=0, win_xsize=1, win_ysize=y_size)
            for i in range(1, x_size, step):
                if x_size >= i + step:
                    win = band.ReadAsArray(xoff=i, yoff=0, win_xsize=step, win_ysize=y_size)
                else:
                    win = band.ReadAsArray(xoff=i, yoff=0, win_xsize=x_size - i, win_ysize=y_size)
                data = np.hstack((data, win))

        return data

class GdalExecutor:
    SUPPORTED_PROTOCOL_VERSIONS = ('2.1.0')
    VERSION = '1.0.0'
    
    def __new__(cls, protocol):
        if protocol.get_version() not in GdalExecutor.SUPPORTED_PROTOCOL_VERSIONS:
            return None
        return super().__new__(cls)
    
    def __init__(self, protocol: str):
        self.proto_version = protocol.get_version()
        self.supported_operations = protocol.get_supported_operations()
        self.ds_man = DatasetManager()
        self.pv_man = PreviewManager()
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
                'file': parameters['file'],
                'info': {
                    'width': dataset.RasterXSize,
                    'height': dataset.RasterYSize,
                    'projection': f'{dataset.GetSpatialRef().GetAuthorityName(None)}:{dataset.GetSpatialRef().GetAuthorityCode(None)}',
                    'unit': dataset.GetSpatialRef().GetAttrValue('UNIT', 0),
                    'origin': [geotransform[0], geotransform[3]],
                    'pixel_size': [geotransform[1], geotransform[5]]
                }
            }
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
            # error 20502
            
            r, g, b = 0, 0, 0
            r = self.ds_man.read_band(parameters['ids'][0], 1, 100)
            g = self.ds_man.read_band(parameters['ids'][1], 1, 100) if ds[1] is not ds[0] else r
            if ds[2] is ds[0]:
                b = r
            elif ds[2] is ds[1]:
                b = g
            else:
                b = self.ds_man.read_band(parameters['ids'][2], 1, 100)
            r = indcal.map_to_8bit(r)
            g = indcal.map_to_8bit(g)
            b = indcal.map_to_8bit(b)            
            pv_id = self.pv_man.add(np.stack((r, g, b)))

            return _response(0, {
                "url": pv_id,
                "width": ds[0].RasterXSize,
                "height": ds[0].RasterYSize
            })
        
        return _response(-1, {"error": "how's this even possible?"})
    
    def get_supported_protocol_versions(self) -> tuple:
        return self.SUPPORTED_PROTOCOL_VERSIONS

    def get_supported_operations(self) -> tuple:
        return self.supported_operations

    def get_version(self) -> str:
        return self.VERSION
