from math import isclose
import threading
from osgeo import gdal
import numpy as np
import index_calculator as indcal
gdal.UseExceptions()

class Preview:
    def __init__(self, array: np.ndarray, index: str):
        self.array = array
        self.index = index
        self.width = array.shape[1]
        self.height = array.shape[0]

class PreviewManager:
    def __init__(self):
        self._previews = {}
        self._counter = 0
        self._lock = threading.Lock()

    def add(self, array: np.ndarray, index: str) -> int:
        """Stores 'array' referring to a preview image and returns its id. The array must be suitable for PIL.Image.fromarray() function, i.e. of shape (height, width, channels).
        'index' refers to the index for which the preview was created. index='nat_col' is for natural color."""

        with self._lock:
            self._previews[self._counter] = Preview(array, index)
            self._counter += 1
            return self._counter - 1

    def find(self, index: str, width: int, height: int) -> int | None:
        """Tries to find a preview of 'width' x 'height' referring to 'index'. If the preview is found, returns its id, otherwise returns None."""

        with self._lock:
            for id_, pr in self._previews.items():
                if pr.index == index:
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
        ids = list(self._previews.keys())
        for id_ in ids:
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
    def __init__(self, dataset: gdal.Dataset, band: int | str=None, stats: dict=None):
        self.dataset = dataset
        self.band = band
        self.no_data = None
        self.stats = stats

class DatasetManager:
    def __init__(self):
        self._datasets = {}
        self._counter = 0
        self._lock = threading.Lock()

    def add_index(self, dataset: gdal.Dataset, index: str, stats: dict) -> int:
        """Stores 'dataset' with its associated 'index' name and 'stats' and returns its own generated id."""

        with self._lock:
            self._datasets[self._counter] = Dataset(dataset, index, stats)
            self._counter += 1
            return self._counter - 1

    def find(self, band_index: int | str) -> int | None:
        """Tries to find a band by its number or spectral index by its name.
        If the band or the index is found, returns its id, otherwise returns None."""

        with self._lock:
            for id_, ds in self._datasets.items():
                if ds.band == band_index:
                    return id_
            return None

    def open(self, filename: str, band: int) -> int:
        """Tries to open 'file' as a GDAL dataset, saves 'band' and returns dataset's generated id.
        If a dataset with 'band' is already open, overwrites it with a new dataset."""

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
                if ds.band == band:
                    self._datasets[id_] = Dataset(dataset, band)
                    return id_
            self._datasets[self._counter] = Dataset(dataset, band)
            self._counter += 1
            return self._counter - 1

    def close(self, id_: int) -> None:
        with self._lock:
            try:
                self._datasets.pop(id_)
            except KeyError:
                raise KeyError(f'Dataset {id_} is not opened but "close" method called')

    def close_all(self) -> None:
        ids = list(self._datasets.keys())
        for id_ in ids:
            self.close(id_)

    def get(self, id_: int) -> Dataset:
        with self._lock:
            try:
                return self._datasets[id_]
            except KeyError:
                raise KeyError(f'Dataset {id_} is not opened but "get" method called')

    def get_as_array(self, id_: int) -> np.ma.MaskedArray:
        return self.read_band(id_, 1)

    def get_all(self) -> list[Dataset]:
        with self._lock:
            return self._datasets.values()

    def read_band(self, dataset_id: int, band_id: int, nodata: float | int=None, step_size_percent: float | int=100, resolution_percent: float | int=100) -> np.ma.MaskedArray:
        """Reads a band from the dataset and returns it as a numpy masked array, where mask corresponds to NoData values.
        'nodata' sets the pixel value that will be treated as the NoData value and will be used to define the resulting array's mask. If the parameter is left to None, the dataset's own nodata value will be used, if it was set prevously (if it was not set, all pixels will be treated as valid).
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
            dataset = self.get(dataset_id)
        except KeyError:
            raise KeyError(f'Dataset {dataset_id} is not opened but "read_band" method called')
        ds = dataset.dataset
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
            dataset.no_data = nodata
        if dataset.no_data is None:
            data = np.ma.array(data, mask=False)
        else:
            data = np.ma.masked_values(data, dataset.no_data, atol=indcal.FLOAT_PRECISION)
            
        return np.ma.array(data, dtype=np.float32)

class IndexErr:
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg

class GdalExecutor:
    VERSION = '1.0.0'
    SUPPORTED_PROTOCOL_VERSIONS = ('3.0.1')
    SUPPORTED_INDICES = ('test', 'wi2015', 'nsmi', 'oc3', 'cdom_ndwi')
    SUPPORTED_SATELLITES = {
        'Landsat 8/9': ('L1TP', 'L2SP')
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
        self.satellite = None
        self.proc_level = None
        print(f'Server running version {self.VERSION}')

    def _index(self, index: str) -> (IndexErr, (tuple[float], str, np.ma.MaskedArray, gdal.GDT_Float32, float | int, str)):
        """Returns (None, (...)) on success and (err, ()) on failure."""

        geotransform, projection = None, ''
        data_type, nodata, ph_unit = gdal.GDT_Float32, -99999, '--'
        result = None
        if index == 'test':
            nodata = -99999.0
            id1, id2 = -1, -1
            if self.satellite == 'Landsat 8/9':
                id1, id2 = self.ds_man.find(2), self.ds_man.find(4)
                if id1 is None or id2 is None:
                    return IndexErr(20501, f"unable to calculate index '{index}': {self.satellite} bands number 2 and 4 are needed"), ()
            # if self.satellite == 'Sentinel 2:'
            geotransform = self.ds_man.get(id1).dataset.GetGeoTransform()
            projection = self.ds_man.get(id1).dataset.GetProjection()
            array1 = self.ds_man.read_band(id1, 1, nodata=0)
            array2 = self.ds_man.read_band(id2, 1, nodata=0)
            result = indcal._test(array1, array2, nodata)
        if index == 'wi2015':
            nodata = float('nan')
            id1, id2, id3, id4, id5 = -1, -1, -1, -1, -1
            if self.satellite == 'Landsat 8/9':
                id1, id2, id3, id4, id5 = self.ds_man.find(3), self.ds_man.find(4), self.ds_man.find(5), self.ds_man.find(6), self.ds_man.find(7)
                if id1 is None or id2 is None or id3 is None or id4 is None or id5 is None:
                    return IndexErr(20501, f"unable to calculate index '{index}': {self.satellite} bands number 3, 4, 5, 6 and 7 are needed"), ()
            # if self.satellite == 'Sentinel 2:'
            geotransform = self.ds_man.get(id1).dataset.GetGeoTransform()
            projection = self.ds_man.get(id1).dataset.GetProjection()
            green = self.ds_man.read_band(id1, 1, nodata=0)
            red = self.ds_man.read_band(id2, 1, nodata=0)
            nir = self.ds_man.read_band(id3, 1, nodata=0)
            swir1 = self.ds_man.read_band(id4, 1, nodata=0)
            swir2 = self.ds_man.read_band(id5, 1, nodata=0)
            result = indcal.wi2015(green, red, nir, swir1, swir2, nodata)
        if index == 'nsmi':
            nodata = float('nan')
            id1, id2, id3 = -1, -1, -1
            if self.satellite == 'Landsat 8/9':
                id1, id2, id3 = self.ds_man.find(4), self.ds_man.find(3), self.ds_man.find(2)
                if id1 is None or id2 is None or id3 is None:
                    return IndexErr(20501, f"unable to calculate index '{index}': {self.satellite} bands number 2, 3 and 4 are needed"), ()
            # if self.satellite == 'Sentinel 2:'
            geotransform = self.ds_man.get(id1).dataset.GetGeoTransform()
            projection = self.ds_man.get(id1).dataset.GetProjection()
            red = self.ds_man.read_band(id1, 1, nodata=0)
            green = self.ds_man.read_band(id2, 1, nodata=0)
            blue = self.ds_man.read_band(id3, 1, nodata=0)
            result = indcal.nsmi(red, green, blue, nodata)
        if index == 'oc3':
            nodata = float('nan')
            id1, id2, id3 = -1, -1, -1
            if self.satellite == 'Landsat 8/9':
                id1, id2, id3 = self.ds_man.find(1), self.ds_man.find(2), self.ds_man.find(3)
                if id1 is None or id2 is None or id3 is None:
                    return IndexErr(20501, f"unable to calculate index '{index}': {self.satellite} bands number 1, 2 and 3 are needed"), ()
            # if self.satellite == 'Sentinel 2:'
            geotransform = self.ds_man.get(id1).dataset.GetGeoTransform()
            projection = self.ds_man.get(id1).dataset.GetProjection()
            aerosol = self.ds_man.read_band(id1, 1, nodata=0)
            blue = self.ds_man.read_band(id2, 1, nodata=0)
            green = self.ds_man.read_band(id3, 1, nodata=0)
            result = indcal.oc3(aerosol, blue, green, nodata)
        if index == 'cdom_ndwi':
            nodata = float('nan')
            ph_unit = 'mg/L'
            id1, id2 = -1, -1
            if self.satellite == 'Landsat 8/9':
                id1, id2 = self.ds_man.find(3), self.ds_man.find(5)
                if id1 is None or id2 is None:
                    return IndexErr(20501, f"unable to calculate index '{index}': {self.satellite} bands number 3 and 5 are needed"), ()
            # if self.satellite == 'Sentinel 2:'
            geotransform = self.ds_man.get(id1).dataset.GetGeoTransform()
            projection = self.ds_man.get(id1).dataset.GetProjection()
            green = self.ds_man.read_band(id1, 1, nodata=0)
            nir = self.ds_man.read_band(id2, 1, nodata=0)
            result = indcal.cdom_ndwi(green, nir, nodata)
        return None, (geotransform, projection, result, data_type, nodata, ph_unit)

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
            if self.satellite is None or self.proc_level is None:
                return _response(20004, {"error": "request 'import_gtiff' was received before 'set_satellite' request"})
            try:
                dataset_id = self.ds_man.open(parameters['file'], parameters['band'])
            except RuntimeError:
                return _response(20301, {"error": f"failed to open file '{parameters['file']}'"})
            except ValueError:
                return _response(20300, {"error": f"provided file '{parameters['file']}' is not a GeoTiff image"})
            dataset = self.ds_man.get(dataset_id).dataset
            if dataset.GetDriver().ShortName != 'GTiff':
                return _response(20300, {"error": f"provided file '{parameters['file']}' is not a GeoTiff image"})
            
            geotransform = dataset.GetGeoTransform()
            result = {
                'file': parameters['file'],
                'band': parameters['band'],
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
            if self.satellite is None or self.proc_level is None:
                return _response(20004, {"error": "request 'calc_preview' was received before 'set_satellite' request"})
            index, width, height = parameters['index'], parameters['width'], parameters['height']
            if index not in self.SUPPORTED_INDICES and index != 'nat_col':
                return _response(20400, {"error": f"index '{index}' is not supported or unknown"})
            ids = []
            if index == 'nat_col':
                if self.satellite == 'Landsat 8/9':
                    ids.append(self.ds_man.find(4))
                    ids.append(self.ds_man.find(3))
                    ids.append(self.ds_man.find(2))
                    for num, id__ in zip((4, 3, 2), ids):
                        if id__ is None:
                            return _response(20401, {"error": f"{self.satellite} band number '{num}' is not loaded but needed for preview generation"})
            else:
                ids.append(self.ds_man.find(index))
                if ids[0] is None:
                    return _response(20401, {"error": f"index '{index}' is not calculated but needed for preview generation"})
            # error 20402

            existing = self.pv_man.find(index, width, height)
            if existing is not None:
                return _response(0, {
                    "url": existing
                })

            ds = self.ds_man.get(ids[0])
            res = 0
            if height <= width:
                res = height / ds.dataset.RasterYSize * 100
            else:
                res = width / ds.dataset.RasterXSize * 100
            no_data = ds.no_data if ds.no_data else 0
            r, g, b, a = 0, 0, 0, 0
            r = self.ds_man.read_band(ids[0], 1, nodata=no_data, resolution_percent=res)
            r = indcal.map_to_8bit(r)
            if index == 'nat_col':
                g = self.ds_man.read_band(ids[1], 1, nodata=no_data, resolution_percent=res)
                b = self.ds_man.read_band(ids[2], 1, nodata=no_data, resolution_percent=res)
                g = indcal.map_to_8bit(g)
                b = indcal.map_to_8bit(b)
            else:
                g = r
                b = r
            a = np.empty(r.shape, dtype=np.uint8)
            if np.ma.is_masked(r):
                a = np.array(np.where(r.mask, 0, 255), dtype=np.uint8)
            else:
                a.fill(255)

            pv_id = self.pv_man.add(np.transpose(np.stack((r, g, b, a)), (1, 2, 0)), index)
            return _response(0, {
                "url": pv_id
            })

        if operation == 'calc_index':
            if self.satellite is None or self.proc_level is None:
                return _response(20004, {"error": "request 'calc_index' was received before 'set_satellite' request"})
            index = parameters['index']
            if index not in self.SUPPORTED_INDICES:
                return _response(20500, {"error": f"index '{index}' is not supported or unknown"})
            # error 20502

            existing = self.ds_man.find(index)
            if existing is not None:
                dataset = self.ds_man.get(existing)
                ind = dataset.dataset
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
                        'pixel_size': [geotransform[1], geotransform[5]],
                        'min': dataset.stats['min'],
                        'max': dataset.stats['max'],
                        'mean': dataset.stats['mean'],
                        'stdev': dataset.stats['stdev'],
                        'ph_unit': dataset.stats['ph_unit']
                    }
                })

            err, res = self._index(index)
            if err is not None:
                return _response(err.code, {"error": err.msg})
            else:
                geotransform, projection, result, data_type, nodata, ph_unit = res

            res_ds = gdal.GetDriverByName('MEM').Create('', result.shape[1], result.shape[0], 1, data_type)
            res_ds.SetGeoTransform(geotransform)
            res_ds.SetProjection(projection)
            res_ds.GetRasterBand(1).SetNoDataValue(nodata)
            res_ds.GetRasterBand(1).WriteArray(result)
            stats = {
                'min': np.nanmin(result).item(),
                'max': np.nanmax(result).item(),
                'mean': np.nanmean(result).item(),
                'stdev': np.nanstd(result).item(),
                'ph_unit': ph_unit
            }
            dataset_id = self.ds_man.add_index(res_ds, index, stats)

            result = {
                'url': dataset_id,
                'index': index,
                'info': {
                    'width': res_ds.RasterXSize,
                    'height': res_ds.RasterYSize,
                    'projection': '{}:{}'.format(res_ds.GetSpatialRef().GetAuthorityName(None), res_ds.GetSpatialRef().GetAuthorityCode(None)),
                    'unit': res_ds.GetSpatialRef().GetAttrValue('UNIT', 0),
                    'origin': [geotransform[0], geotransform[3]],
                    'pixel_size': [geotransform[1], geotransform[5]],
                    'min': stats['min'],
                    'max': stats['max'],
                    'mean': stats['mean'],
                    'stdev': stats['stdev'],
                    'ph_unit': stats['ph_unit']
                }
            }
            return _response(0, result)

        if operation == 'set_satellite':
            satellite, proc_level = parameters['satellite'], parameters['proc_level']
            if satellite not in self.SUPPORTED_SATELLITES.keys():
                return _response(20600, {"error": f"unsupported satellite model: '{satellite}'"})
            if proc_level not in self.SUPPORTED_SATELLITES[satellite]:
                return _response(20601, {"error": f"unknown/unsupported processing level '{proc_level}' for '{satellite}'"})

            self.satellite = satellite
            self.proc_level = proc_level
            return _response(0, {})

        if operation == 'end_session':
            # 20700 !!! TBA with overall cancel mechanism !!!
            self.ds_man.close_all()
            self.pv_man.remove_all()
            self.satellite = None
            self.proc_level = None
            return _response(0, {})
        
        return _response(-1, {"error": "how's this even possible?"})

    def get_version(self) -> str:
        return self.VERSION

    def get_supported_protocol_versions(self) -> tuple[str]:
        return self.SUPPORTED_PROTOCOL_VERSIONS

    def get_supported_indices(self) -> tuple[str]:
        return self.SUPPORTED_INDICES

    def get_supported_operations(self) -> tuple[str]:
        return self.supported_operations

    def get_supported_satellites(self) -> dict:
        return self.SUPPORTED_SATELLITES
