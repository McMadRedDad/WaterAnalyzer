from math import isclose
import threading
from osgeo import gdal
import numpy as np
import index_calculator as indcal
gdal.UseExceptions()

class Preview:
    def __init__(self, array: np.ndarray, r: int, g: int, b: int):
        self.array = array
        self.ids = (r, g, b)
        self.width = array.shape[1]
        self.height = array.shape[0]

class PreviewManager:
    def __init__(self):
        self._previews = {}
        self._counter = 0
        self._lock = threading.Lock()

    def add(self, array: np.ndarray, red: int, green: int, blue: int) -> int:
        """Stores 'array' referring to a preview image and returns its id. The array must be suitable for PIL.Image.fromarray() function, i.e. of shape (height, width, channels).
        'red', 'green' and 'blue' refer to the datasets' ids from which the preview was created."""

        with self._lock:
            self._previews[self._counter] = Preview(array, red, green, blue)
            self._counter += 1
            return self._counter - 1

    def find(self, red: int, green: int, blue: int, width: int, height: int) -> int | None:
        """Tries to find a preview of 'width' x 'height' dimensions created from 'red', 'green' and 'blue' dataset ids.
        If the preview is found, returns its id, otherwise returns None."""

        ids = (red, green, blue)
        with self._lock:
            for id_, pr in self._previews.items():
                if pr.ids == ids:
                    if pr.width == width or pr.height == height:
                        return id_
            return None

    def remove(self, id_: int) -> None:
        with self._lock:
            try:
                self._previews.pop(id_)
            except KeyError:
                raise KeyError(f'Preview {id_} does not exist but "remove" method called')

    def remove_all(self) -> None:
        for id_ in self._previews.keys():
            self.remove(id_)

    def get(self, id_: int) -> Preview:
        with self._lock:
            try:
                return self._previews[id_]
            except KeyError:
                raise KeyError(f'Preview {id_} does not exist but "get" method called')

    def get_all(self) -> list[Preview]:
        with self._lock:
            return list(self._previews.values())

class Dataset:
    def __init__(self, dataset: gdal.Dataset, index: str=None, ids: tuple[int] | list[int]=None):
        self.dataset = dataset
        self.index = index
        self._ids = tuple(ids) if ids else None

class DatasetManager:
    def __init__(self):
        self._datasets = {}
        self._counter = 0
        self._lock = threading.Lock()

    def add_index(self, dataset: gdal.Dataset, index: str, ids: tuple[int] | list[int]) -> int:
        """Stores 'dataset' with its associated 'index' name and 'ids' and returns its own generated id."""

        with self._lock:
            self._datasets[self._counter] = Dataset(dataset, index, ids)
            self._counter += 1
            return self._counter - 1

    def find(self, index: str, ids: tuple[int] | list[int]) -> int | None:
        """Tries to find a spectral index associated with 'index' created from 'ids' dataset ids.
        If the index is found, returns its id, otherwise returns None."""

        ids_ = tuple(ids)
        with self._lock:
            for id_, ind in self._datasets.items():
                if ind._ids == ids_ and ind.index == index:
                    return id_
            return None

    def open(self, filename: str) -> int:
        """Tries to open 'file' as a GDAL dataset and returns its generated id."""

        try:
            dataset = gdal.Open(filename, gdal.GA_ReadOnly)
        except RuntimeError:
            raise RuntimeError(f'Cannot open file {filename}')
        if dataset.GetSpatialRef() is None:
            raise ValueError(f'Opened file {filename} is not a spatial image')

        with self._lock:
            for id_, ds in self._datasets.items():
                if ds.dataset.GetDescription() == dataset.GetDescription():
                    return id_
            self._datasets[self._counter] = Dataset(dataset)
            self._counter += 1
            return self._counter - 1

    def close(self, id_: int) -> None:
        with self._lock:
            try:
                self._datasets.pop(id_)
            except KeyError:
                raise KeyError(f'Dataset {id_} is not opened but "close" method called')

    def close_all(self) -> None:
        for id_ in self._datasets.keys():
            self.close(id_)

    def get(self, id_: int) -> Dataset:
        with self._lock:
            try:
                return self._datasets[id_]
            except KeyError:
                raise KeyError(f'Dataset {id_} is not opened but "get" method called')

    def get_as_array(self, id_: int) -> np.array:
        return self.read_band(id_, 1)

    def get_all(self) -> list[Dataset]:
        with self._lock:
            return self._datasets.values()

    def read_band(self, dataset_id: int, band_id: int, nodata: float | int=None, step_size_percent: float | int=100, resolution_percent: float | int=100) -> np.ma.MaskedArray:
        """Reads a band from the dataset and returns it as a numpy masked array, where mask corresponds to NoData values.
        'nodata' sets the pixel value that will be treated as the NoData value and will be used to define the resulting array's mask. If the parameter is left to None, all pixels are treated as valid data.
        'step_size_percent' is the percent of the raster's rows or columns that will be read during one iteration. For example, if the raster is 100x100 pixels and 'step_size'=20, the band will be read entirely within 5 iterations with five 20x100 windows.
        'step_size_percent' <=0 means the band will be read line by line. 'step_size' >=100 means the band will be read at once.
        The less 'step_size' is, the less memory is used and the slower the function is.
        'resolution_percent' controls the resulting array resolution. if <=0, resoltion is set to 0.01 percent of the original raster; if >=100, the band will be read at full resolution."""

        def _to_percent(value):
            if isclose(0, value, abs_tol=0.01) or value < 0:
                return 0
            elif isclose(100, value, abs_tol=0.01) or value > 100:
               return 100
            else:
                return value

        try:
            ds = self.get(dataset_id).dataset
        except KeyError:
            raise KeyError(f'Dataset {dataset_id} is not opened but "read_band" method called')
        try:
            band = ds.GetRasterBand(band_id)
        except RuntimeError:
            raise RuntimeError(f'Dataset {dataset_id} does not have band number {band_id}')

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
            buf_x = int(x_size * res) if int(x_size * res) > 0 else 1
            buf_y = int(1 * res) if int(1 * res) > 0 else 1
            with self._lock:
                data = band.ReadAsMaskedArray(xoff=0, yoff=0, win_xsize=x_size, win_ysize=1, buf_xsize=buf_x, buf_ysize=buf_y)
            buf_y = int(step * res) if int(step * res) > 0 else 1
            for i in range(1, y_size, step):
                if y_size >= i + step:
                    with self._lock:
                        win = band.ReadAsMaskedArray(xoff=0, yoff=i, win_xsize=x_size, win_ysize=step, buf_xsize=buf_x, buf_ysize=buf_y)
                else:
                    buf_y = int((y_size - i) * res) if int((y_size - i) * res) > 0 else 1
                    with self._lock:
                        win = band.ReadAsMaskedArray(xoff=0, yoff=i, win_xsize=x_size, win_ysize=y_size - i, buf_xsize=buf_x, buf_ysize=buf_y)
                data = np.ma.vstack((data, win))
        else:
            buf_x = int(1 * res) if int(1 * res) > 0 else 1
            buf_y = int(y_size * res) if int(y_size * res) > 0 else 1
            with self._lock:
                data = band.ReadAsMaskedArray(xoff=0, yoff=0, win_xsize=1, win_ysize=y_size, buf_xsize=buf_x, buf_ysize=buf_y)
            buf_x = int(step * res) if int(step * res) > 0 else 1
            for i in range(1, x_size, step):
                if x_size >= i + step:
                    with self._lock:
                        win = band.ReadAsMaskedArray(xoff=i, yoff=0, win_xsize=step, win_ysize=y_size, buf_xsize=buf_x, buf_ysize=buf_y)
                else:
                    buf_x = int((x_size - i) * res) if int((x_size - i) * res) > 0 else 1
                    with self._lock:
                        win = band.ReadAsMaskedArray(xoff=i, yoff=0, win_xsize=x_size - i, win_ysize=y_size, buf_xsize=buf_x, buf_ysize=buf_y)
                data = np.ma.hstack((data, win))
                
        if nodata is not None:
            data = np.ma.masked_values(data, nodata, rtol=indcal.FLOAT_PRECISION)
        return np.ma.array(data, dtype=np.float32)

class GdalExecutor:
    VERSION = '1.0.0'
    SUPPORTED_PROTOCOL_VERSIONS = ('2.1.4')
    SUPPORTED_INDICES = {   # { 'name': number_of_datasets_to_calc_from }
        'test': 2,
        'wi2015': 5,
        'nsmi': 3
    }
    
    def __new__(cls, protocol):
        if protocol.get_version() not in GdalExecutor.SUPPORTED_PROTOCOL_VERSIONS:
            return None
        return super().__new__(cls)
    
    def __init__(self, protocol: 'Protocol'):
        self.supported_operations = protocol.get_supported_operations()
        self.ds_man = DatasetManager()
        self.pv_man = PreviewManager()
        self.geotiff = gdal.GetDriverByName('GTiff')
        print(f'Server running version {self.VERSION}')

    def execute(self, request: dict) -> dict:
        """Processes the request and returns a dictionary to be used by Protocol.send method.
        Must be called after 'Protocol.validate'."""

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
            except RuntimeError:
                return _response(20301, {"error": f"failed to open file '{parameters['file']}'"})
            except ValueError:
                return _response(20300, {"error": f"provided file '{parameters['file']}' is not a GeoTiff image"})
            dataset = self.ds_man.get(dataset_id).dataset
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
            width, height = parameters['width'], parameters['height']
            ds = []
            for i in (id_r, id_g, id_b):
                try:
                    ds.append(self.ds_man.get(i).dataset)
                except KeyError:
                    return _response(20400, {"error": f"id {i} provided in 'ids' key does not exist"})
            for i in ds[1:]:
                if not (i.RasterXSize == ds[0].RasterXSize and i.RasterYSize == ds[0].RasterYSize):
                    return _response(20401, {"error": "unable to create preview from requested ids: rasters do not match in dimensions"})
            # error 20402

            existing = self.pv_man.find(id_r, id_g, id_b, width, height)
            if existing is not None:
                return _response(0, {
                    "url": existing,
                    "width": self.pv_man.get(existing).width,
                    "height": self.pv_man.get(existing).height
                })

            res = 0
            if height <= width:
                res = height / ds[0].RasterYSize * 100
            else:
                res = width / ds[0].RasterXSize * 100            
            r, g, b = 0, 0, 0
            r = self.ds_man.read_band(id_r, 1, resolution_percent=res)
            r = indcal.map_to_8bit(r)
            if id_g == id_r:
                g = r
            else:
                g = self.ds_man.read_band(id_g, 1, resolution_percent=res)
                g = indcal.map_to_8bit(g)
            if id_b == id_r:
                b = r
            elif id_b == id_g:
                b = g
            else:
                b = self.ds_man.read_band(id_b, 1, resolution_percent=res)
                b = indcal.map_to_8bit(b)
                
            pv_id = self.pv_man.add(np.transpose(np.stack((r, g, b)), (1, 2, 0)), id_r, id_g, id_b)
            return _response(0, {
                "url": pv_id,
                "width": self.pv_man.get(pv_id).width,
                "height": self.pv_man.get(pv_id).height
            })

        if operation == 'calc_index':
            ids = parameters['ids']
            index = parameters['index']
            if index not in self.SUPPORTED_INDICES:
                return _response(20500, {"error": f"index '{index}' is not supported or unknown"})
            if len(ids) != self.SUPPORTED_INDICES[index]:
                return _response(20501, {"error": "exactly {} values must be specified in 'ids' key for calculating '{}' index, but {} values given".format(self.SUPPORTED_INDICES[index], index, len(ids))})
            ds = []
            for i in ids:
                try:
                    ds.append(self.ds_man.get(i).dataset)
                except KeyError:
                    return _response(20502, {"error": f"id {i} provided in 'ids' key does not exist"})
            for i in ds[1:]:
                if not (i.RasterXSize == ds[0].RasterXSize and i.RasterYSize == ds[0].RasterYSize):
                    return _response(20503, {"error": "unable to create index from requested ids: rasters do not match in dimensions"})
            # error 20504

            existing = self.ds_man.find(index, ids)
            if existing is not None:
                ind = self.ds_man.get(existing).dataset
                geotransform = ind.GetGeoTransform()
                return _response(0, {
                    'url': existing,
                    'index': index,
                    'info': {
                        'width': ind.RasterXSize,
                        'height': ind.RasterYSize,
                        'projection': '{}:{}'.format(ind.GetSpatialRef().GetAuthorityName(None), ind.GetSpatialRef().GetAuthorityCode(None)),
                        'unit': ind.GetSpatialRef().GetAttrValue('UNIT', 0),
                        'origin': [geotransform[0], geotransform[3]],
                        'pixel_size': [geotransform[1], geotransform[5]]
                    }
                })

            result, data_type, nodata = 0, 0, -99999
            if index == 'test':
                data_type = gdal.GDT_Float32
                nodata = -99999.0
                array1, array2 = self.ds_man.read_band(ids[0], 1, nodata=0), self.ds_man.read_band(ids[1], 1, nodata=0)
                result = indcal._test(array1, array2, nodata)
            if index == 'wi2015':
                data_type = gdal.GDT_Float32
                nodata = float('nan')
                green = self.ds_man.read_band(ids[0], 1, nodata=0)
                red = self.ds_man.read_band(ids[1], 1, nodata=0)
                nir = self.ds_man.read_band(ids[2], 1, nodata=0)
                swir1 = self.ds_man.read_band(ids[3], 1, nodata=0)
                swir2 = self.ds_man.read_band(ids[4], 1, nodata=0)
                result = indcal.wi2015(green, red, nir, swir1, swir2, nodata)
            if index == 'nsmi':
                data_type = gdal.GDT_Float32
                nodata = float('nan')
                red = self.ds_man.read_band(ids[0], 1, nodata=0)
                green = self.ds_man.read_band(ids[1], 1, nodata=0)
                blue = self.ds_man.read_band(ids[2], 1, nodata=0)
                result = indcal.nsmi(red, green, blue, nodata)

            res_ds = gdal.GetDriverByName('MEM').Create('', ds[0].RasterXSize, ds[0].RasterYSize, 1, data_type)
            res_ds.SetGeoTransform(ds[0].GetGeoTransform())
            res_ds.SetProjection(ds[0].GetProjection())
            res_ds.GetRasterBand(1).SetNoDataValue(nodata)            
            res_ds.GetRasterBand(1).WriteArray(result)
            dataset_id = self.ds_man.add_index(res_ds, index, ids)

            geotransform = res_ds.GetGeoTransform()
            result = {
                'url': dataset_id,
                'index': index,
                'info': {
                    'width': res_ds.RasterXSize,
                    'height': res_ds.RasterYSize,
                    'projection': '{}:{}'.format(res_ds.GetSpatialRef().GetAuthorityName(None), res_ds.GetSpatialRef().GetAuthorityCode(None)),
                    'unit': res_ds.GetSpatialRef().GetAttrValue('UNIT', 0),
                    'origin': [geotransform[0], geotransform[3]],
                    'pixel_size': [geotransform[1], geotransform[5]]
                }
            }
            return _response(0, result)
        
        return _response(-1, {"error": "how's this even possible?"})

    def get_version(self) -> str:
        return self.VERSION

    def get_supported_protocol_versions(self) -> tuple[str]:
        return self.SUPPORTED_PROTOCOL_VERSIONS

    def get_supported_indices(self) -> tuple[str]:
        return tuple(self.SUPPORTED_INDICES.keys())

    def get_supported_operations(self) -> tuple[str]:
        return self.supported_operations
