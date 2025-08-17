from math import isclose
import threading
from osgeo import gdal
import numpy as np
import index_calculator as indcal
gdal.UseExceptions()

class Preview:
    def __init__(self, array: np.ndarray, r: int, g: int, b: int):
        self.array = array
        self.width = array.shape[1]
        self.height = array.shape[0]
        self._ids = (r, g, b)

class PreviewManager:
    def __init__(self):
        self._previews = {}
        self._counter = 0
        self._lock = threading.Lock()

    def add(self, array: np.ndarray, red: int, green: int, blue: int) -> int:
        """Stores a new numpy array referring to a preview image and returns its id. The array must be suitable for PIL.Image.fromarray() function.
        'red', 'green' and 'blue' refer to the datasets' ids from which the preview was created."""

        with self._lock:
            self._previews[self._counter] = Preview(array, red, green, blue)
            self._counter += 1
            return self._counter - 1

    def find(self, red: int, green: int, blue: int) -> int | None:
        """Tries to find a preview created from 'red', 'green' and 'blue' dataset ids.
        If the preview is found, returns its id, otherwise returns None."""

        ids = (red, green, blue)
        with self._lock:
            for id_, pr in self._previews.items():
                if pr._ids == ids:
                    return id_
            return None

    def remove(self, id: int) -> None:
        with self._lock:
            try:
                self._previews.pop(id)
            except KeyError:
                raise KeyError(f'Preview {id} does not exist but "remove" method called')

    def remove_all(self) -> None:
        for id_ in self._previews.keys():
            self.remove(id_)

    def get(self, id: int) -> Preview:
        with self._lock:
            try:
                return self._previews[id]
            except KeyError:
                raise KeyError(f'Preview {id} does not exist but "get" method called')

    def get_all(self) -> list[Preview]:
        return self._previews.values()

class DatasetManager:
    def __init__(self):
        self._datasets = {}
        self._counter = 0
        self._lock = threading.Lock()

    def open(self, file: str) -> int:
        """Tries to open 'file' as a GDAL dataset and returns its generated id."""

        try:
            dataset = gdal.Open(file, gdal.GA_ReadOnly)
        except RuntimeError:
            dataset = None
            raise RuntimeError(f'Cannot open file {file}')
        if dataset.GetSpatialRef() is None:
            dataset = None
            raise ValueError(f'Opened file {file} is not a spatial image')

        with self._lock:
            for id_, ds in self._datasets.items():
                if ds.GetDescription() == dataset.GetDescription():
                    dataset = None
                    return id_
            self._datasets[self._counter] = dataset
            self._counter += 1
            return self._counter - 1

    def close(self, id: int) -> None:
        with self._lock:
            try:
                dataset = self._datasets.pop(id)
            except KeyError:
                raise KeyError(f'Dataset {id} is not opened but "close" method called')
            dataset = None

    def close_all(self) -> None:
        for id_ in self._datasets.keys():
            self.close(id_)

    def get(self, id: int) -> gdal.Dataset:
        with self._lock:
            try:
                return self._datasets[id]
            except KeyError:
                raise KeyError(f'Dataset {id} is not opened but "get" method called')

    def get_all(self) -> list[gdal.Dataset]:
        return self._datasets.values()

    def read_band(self, dataset_id: int, band_id: int, step_size_percent: float | int, resolution_percent: float | int) -> np.ndarray:
        """Reads a band from the dataset and returns it as a numpy array.
        'step_size' is the percent of the raster's rows or columns that will be read during one iteration. For example, if the raster is 100x100 pixels and 'step_size'=20, the band will be read entirely within 5 iterations with five 20x100 windows.
        'step_size' <=0 means the band will be read line by line. 'step_size' >=100 means the band will be read at once.
        The less 'step_size' is, the less memory is used and the slower the function is.
        'resolution_percent' controls the resulting array resolution. if <=0 resoltion is set to 0.01 percent of the original raster; if >=100 the band is read at full resolution."""

        def _to_percent(value):
            if (
                isclose(0, value, abs_tol=0.01) or
                value < 0
            ):
                return 0
            elif (
                isclose(100, value, abs_tol=0.01) or
                value > 100
            ):
               return 100
            else:
                return value

        try:
            ds = self.get(dataset_id)
        except KeyError:
            raise KeyError(f'Dataset {dataset_id} is not opened but "read_band" method called')
        try:
            band = ds.GetRasterBand(band_id)
        except RuntimeError:
            raise RuntimeError(f'Daraset {dataset_id} does not have band number {band_id}')

        x_size, y_size, step, res, data = ds.RasterXSize, ds.RasterYSize, 0, 0, 0
        if _to_percent(step_size_percent) == 0:
            step = 1
        elif _to_percent(step_size_percent) == 100:
            step = x_size - 1 if x_size >= y_size else y_size - 1
        else:
            step = int(x_size * step_size_percent/100) if x_size >= y_size else int(y_size * step_size_percent/100)
            if step == 0:
                step = 1
        if _to_percent(resolution_percent) == 0:
            res = 0.0001
        elif _to_percent(resolution_percent) == 100:
            res = 1
        else:
            res = resolution_percent / 100

        # we'll read along the side that is shorter
        # e.g. raster size 100x50 -> read along y=50
        if x_size >= y_size:
            data = band.ReadAsArray(xoff=0, yoff=0, win_xsize=x_size, win_ysize=1, buf_xsize=int(x_size * res), buf_ysize=int(1 * res))
            for i in range(1, y_size, step):
                if y_size >= i + step:
                    win = band.ReadAsArray(xoff=0, yoff=i, win_xsize=x_size, win_ysize=step, buf_xsize=int(x_size * res), buf_ysize=int(step * res))
                else:
                    win = band.ReadAsArray(xoff=0, yoff=i, win_xsize=x_size, win_ysize=y_size - i, buf_xsize=int(x_size * res), buf_ysize=int((y_size - i) * res))
                data = np.vstack((data, win))
        else:
            data = band.ReadAsArray(xoff=0, yoff=0, win_xsize=1, win_ysize=y_size, buf_xsize=int(1 * res), buf_ysize=int(y_size * res))
            for i in range(1, x_size, step):
                if x_size >= i + step:
                    win = band.ReadAsArray(xoff=i, yoff=0, win_xsize=step, win_ysize=y_size, buf_xsize=int(step * res), buf_ysize=int(y_size * res))
                else:
                    win = band.ReadAsArray(xoff=i, yoff=0, win_xsize=x_size - i, win_ysize=y_size, buf_xsize=int((x_size - i) * res), buf_ysize=int(y_size * res))
                data = np.hstack((data, win))

        return data

class GdalExecutor:
    SUPPORTED_PROTOCOL_VERSIONS = ('2.1.1')
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
            except (RuntimeError, KeyError):
                return _response(20301, {"error": f"failed to open file '{parameters['file']}'"})
            except ValueError:
                return _response(20300, {"error": f"provided file '{parameters['file']}' is not a GeoTiff image"})
            if dataset.GetDriver().ShortName != 'GTiff':
                return _response(20300, {"error": f"provided file '{parameters['file']}' is not a GeoTiff image"})
            
            geotransform = dataset.GetGeoTransform()
            result = {
                'id': dataset_id,
                'file': parameters['file'],
                'info': {
                    'width': dataset.RasterXSize,
                    'height': dataset.RasterYSize,
                    'projection': '{}:{}'.format(dataset.GetSpatialRef().GetAuthorityName(None), dataset.GetSpatialRef().GetAuthorityCode(None)),
                    'unit': dataset.GetSpatialRef().GetAttrValue('UNIT', 0),
                    'origin': [geotransform[0], geotransform[3]],
                    'pixel_size': [geotransform[1], geotransform[5]]
                }
            }
            return _response(0, result)

        if operation == 'calc_preview':
            id_r, id_g, id_b = parameters['ids'][0], parameters['ids'][1], parameters['ids'][2]
            ds = []
            for i in (id_r, id_g, id_b):
                try:
                    ds.append(self.ds_man.get(i))
                except KeyError:
                    return _response(20400, {"error": f"id {i} provided in 'ids' key does not exist"})
            if not (
                ds[0].RasterXSize == ds[1].RasterXSize == ds[2].RasterXSize and
                ds[0].RasterYSize == ds[1].RasterYSize == ds[2].RasterYSize
            ):
                return _response(20401, {"error": "unable to create a preview from requested ids: rasters do not match in size"})
            # error 20402

            existing = self.pv_man.find(id_r, id_g, id_b)
            if existing is not None:
                return _response(0, {
                    "url": existing,
                    "width": self.pv_man.get(existing).width,
                    "height": self.pv_man.get(existing).height
                })
            
            r, g, b = 0, 0, 0
            r = self.ds_man.read_band(id_r, 1, 100, 5)
            g = self.ds_man.read_band(id_g, 1, 100, 5) if ds[1] is not ds[0] else r
            if ds[2] is ds[0]:
                b = r
            elif ds[2] is ds[1]:
                b = g
            else:
                b = self.ds_man.read_band(id_b, 1, 100, 5)
                
            r = indcal.map_to_8bit(r)
            g = indcal.map_to_8bit(g)
            b = indcal.map_to_8bit(b)            
            pv_id = self.pv_man.add(np.transpose(np.stack((r, g, b)), (1, 2, 0)), id_r, id_g, id_b)

            return _response(0, {
                "url": pv_id,
                "width": self.pv_man.get(pv_id).width,
                "height": self.pv_man.get(pv_id).height
            })
        
        return _response(-1, {"error": "how's this even possible?"})
    
    def get_supported_protocol_versions(self) -> tuple:
        return self.SUPPORTED_PROTOCOL_VERSIONS

    def get_supported_operations(self) -> tuple:
        return self.supported_operations

    def get_version(self) -> str:
        return self.VERSION
