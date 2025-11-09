from math import isclose
from time import sleep
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
        """Stores 'array' referring to a preview image and returns its id. The array must be of shape (height, width, channels).
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
    def __init__(self, dataset: gdal.Dataset, band: str=None, nodata: float | int=None, stats: dict=None, description: dict=None):
        self.dataset = dataset
        self.band = band
        self.no_data = nodata
        self.radio_mult = None
        self.radio_add = None
        self.thermal_k1 = None
        self.thermal_k2 = None
        self.rad_max = None
        self.refl_max = None
        self.stats = stats
        self.description = description

class DatasetManager:
    def __init__(self):
        self._datasets = {}
        self._cloud_mask = None
        self._sun_elev = None
        self._earth_sun_dist = None
        self._counter = 0
        self._lock = threading.Lock()

    def add_index(self, dataset: gdal.Dataset, index: str, nodata: float | int, statistics: dict) -> int:
        """Stores 'dataset' with its associated 'index' name, 'nodata' and 'statistics' and returns its own generated id."""

        with self._lock:
            self._datasets[self._counter] = Dataset(dataset, index, nodata, statistics)
            self._counter += 1
            return self._counter - 1

    def open(self, filename: str, band: str, nodata: float | int) -> int:
        """Tries to open 'file' as a GDAL dataset, saves 'band' and 'nodata' and returns dataset's generated id.
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
                    self._datasets[id_] = Dataset(dataset, band, nodata)
                    return id_
            self._datasets[self._counter] = Dataset(dataset, band, nodata)
            self._counter += 1
            return self._counter - 1

    def find(self, band_index: str) -> int | None:
        """Tries to find a band by or a spectral index by its name.
        If the band or the index is found, returns its id, otherwise returns None."""

        with self._lock:
            for id_, ds in self._datasets.items():
                if ds.band == band_index:
                    return id_
            return None

    def add_cloud_mask(self, cloud_mask: np.ma.MaskedArray) -> None:
        """Save the cloud mask for future calculations."""
        self._cloud_mask = cloud_mask

    def add_description(self, id_: int, notes: str=None, desc: str=None) -> None:
        """Adds 'notes' and 'desc' to index's description."""

        ds = self.get(id_)
        with self._lock:
            ds.description = {
                'notes': notes if notes is not None else '',
                'text': desc if desc is not None else ''
            }
            
    def append_description(self, id_: int, notes: str=None, desc: str=None) -> None:
        """Appends 'notes' and 'desc' to index's description without rewriting the existing one."""

        ds = self.get(id_)
        with self._lock:
            if notes is not None:
                ds.description['notes'] += notes
            if desc is not None:
                ds.description['text'] += text

    def remove_description(self, id_: int) -> None:
        ds = self.get(id_)
        with self._lock:
            ds.description = None

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
        self._cloud_mask = None
        self._sun_elev = None
        self._earth_sun_dist = None

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

    def get_cloud_mask(self) -> np.ma.MaskedArray | None:
        return self._cloud_mask

    def get_sun_elevation(self) -> float | None:
        return self._sun_elev

    def get_earth_sun_distance(self) -> float | None:
        return self._earth_sun_dist

    def get_description(self, id_: int) -> dict | None:
        return self.get(id_).description

    def set_sun_elevation(self, val: float) -> None:
        self._sun_elev = val

    def set_earth_sun_distance(self, val: float) -> None:
        self._earth_sun_dist = val

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
            data = np.ma.masked_values(data, nodata, atol=indcal.FLOAT_PRECISION)
            data = np.ma.masked_invalid(data)
        elif dataset.no_data is not None:
            data = np.ma.masked_values(data, dataset.no_data, atol=indcal.FLOAT_PRECISION)
            data = np.ma.masked_invalid(data)
        else:
            data = np.ma.array(data, mask=False)
        clouds = self.get_cloud_mask()
        if clouds is not None:
            if resolution_percent != 100:
                x = np.linspace(0, clouds.shape[0] - 1, data.shape[0]).astype(int)
                y = np.linspace(0, clouds.shape[1] - 1, data.shape[1]).astype(int)
                data.mask |= clouds[np.ix_(x, y)]
            else:
                data.mask |= clouds
        return np.ma.array(data, dtype=np.float32)

class IndexErr:
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg

class GdalExecutor:
    VERSION = '1.0.0'
    SUPPORTED_PROTOCOL_VERSIONS = ('3.2.1')
    SUPPORTED_INDICES = ('test', 'water_mask', 'ndbi', 'wi2015', 'andwi', 'ndwi', 'nsmi', 'oc3', 'cdom_ndwi', 'toa_temperature_landsat', 'ls_temperature_landsat')
    WATER_EXTRACTION_INDICES = ('wi2105', 'andwi', 'ndwi')
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

    def _index(self, index: str) -> (IndexErr, (tuple[float], str, np.ma.MaskedArray, gdal.GDT_Float32, float | int, str, str)):
        """Returns (None, (...)) on success and (err, ()) on failure."""

        def _prepare_inputs(convert_to: str, nodata: float | int, *bands: int) -> (IndexErr, (tuple[float], str, tuple[np.ma.MaskedArray], str)):
            if convert_to not in ('toa_rad', 'toa_refl', 'ls_rad', 'ls_refl'):
                raise ValueError(f'invalid argument "{convert_to}"')

            inputs = []
            geotransform, projection, notes = None, '', ''
            for i in bands:
                id_ = self.ds_man.find(str(i))
                if id_ is None:
                    return IndexErr(20502, f"unable to calculate index '{index}': {self.satellite} bands number {bands} are needed"), ()
                ds = self.ds_man.get(id_)
                inp = self.ds_man.read_band(id_, 1)
                if len(projection) <= 0:
                    geotransform = ds.dataset.GetGeoTransform()
                    projection = ds.dataset.GetProjection()
                if self.satellite == 'Landsat 8/9':
                    if self.proc_level == 'L1TP':
                        if convert_to =='toa_rad':
                            inp = indcal.landsat_l1_dn_to_toa_radiance(inp, ds.radio_mult, ds.radio_add, nodata)
                            notes = 'Рассчитано по излучению верхнего слоя атмосферы.'
                        if convert_to == 'toa_refl':
                            sun_elev, es_dist = self.ds_man.get_sun_elevation(), self.ds_man.get_earth_sun_distance()
                            inp = indcal.landsat_l1_dn_to_toa_reflectance(inp, ds.radio_mult, ds.radio_add, sun_elev, es_dist, ds.rad_max, ds.refl_max, nodata)
                            notes = 'Рассчитано по отражательной способности верхнего слоя атмосферы.'
                        # if convert_to == 'ls_rad':
                        if convert_to == 'ls_refl':
                            sun_elev, es_dist = self.ds_man.get_sun_elevation(), self.ds_man.get_earth_sun_distance()
                            inp = indcal.landsat_l1_dn_to_dos1_reflectance(inp, ds.radio_mult, ds.radio_add, sun_elev, es_dist, ds.rad_max, ds.refl_max, nodata)
                            notes = 'Рассчитано по отражательной способности поверхности Земли, корректировка влияния атмосферы методом DOS1.'
                    if self.proc_level == 'L2SP':
                        if convert_to == 'ls_refl':
                            inp = indcal.landsat_l2_dn_to_ls_reflectance(inp, nodata)
                            notes = 'Рассчитано по отражательной способности поверхности Земли.'
                # if self.satellite == 'Sentinel 2':
                inputs.append(inp)
            return None, (geotransform, projection, notes, inputs)

        geotransform, projection, notes = [], '', ''
        data_type, nodata, ph_unit = gdal.GDT_Float32, float('nan'), '--'
        result = None
        conversion = ''
        if self.satellite == 'Landsat 8/9':
            if self.proc_level == 'L1TP':
                conversion = 'toa_refl'
            else:
                conversion = 'ls_refl'

        if index == 'test':
            nodata = -99999.0
            if self.satellite == 'Landsat 8/9':
                err, res = _prepare_inputs(conversion, nodata, 2, 4)
            if err is not None:
                return err, ()
            geotransform, projection, notes, inputs = res
            result = indcal._test(*inputs, nodata)
        if index == 'water_mask':
            id_ = -1
            for i in self.get_water_extraction_indices():
                id_ = self.ds_man.find(i)
                if id_ is not None:
                    break
            if id_ is None:
                return IndexErr(20503, 'unable to create water mask: water extraction index is not calculated'), ()
            ds = self.ds_man.get(id_)
            geotransform, projection = ds.dataset.GetGeoTransform(), ds.dataset.GetProjection()
            data_type, nodata = gdal.GDT_Byte, 0
            if ds.band == 'wi2015':
                result, thresh = indcal.otsu_binarization(self.ds_man.read_band(id_, 1), nodata)
                result = result.astype(np.bool)
                notes += '\n' + f'Классификация выполнена методом Оцу, пороговое значение {thresh}.'
            if ds.band == 'andwi':
                result, thresh = indcal.otsu_binarization(self.ds_man.read_band(id_, 1), nodata)
                result = result.astype(np.bool)
                notes += '\n' + f'Классификация выполнена методом Оцу, пороговое значение {thresh}.'
            if ds.band == 'ndwi':
                result = np.ma.array(self.ds_man.read_band(id_, 1) > 0.01, dtype=np.bool)
                notes += '\n' + 'Классификация выполнена по пороговому значению 0.01.'
        if index == 'wi2015':
            if self.satellite == 'Landsat 8/9':
                err, res = _prepare_inputs(conversion, nodata, 3, 4, 5, 6, 7)
            if err is not None:
                return err, ()
            geotransform, projection, notes, inputs = res
            result = indcal.wi2015(*inputs, nodata)
        if index == 'andwi':
            if self.satellite == 'Landsat 8/9':
                err, res = _prepare_inputs(conversion, nodata, 2, 3, 4, 5, 6, 7)
            if err is not None:
                return err, ()
            geotransform, projection, notes, inputs = res
            result = indcal.andwi(*inputs, nodata)
        if index == 'ndwi':
            if self.satellite == 'Landsat 8/9':
                err, res = _prepare_inputs(conversion, nodata, 3, 5)
            if err is not None:
                return err, ()
            geotransform, projection, notes, inputs = res
            result = indcal.ndwi(*inputs, nodata)
        if index == 'nsmi':
            if self.satellite == 'Landsat 8/9':
                err, res = _prepare_inputs(conversion, nodata, 4, 3, 2)
            if err is not None:
                return err, ()
            geotransform, projection, notes, inputs = res
            result = indcal.nsmi(*inputs, nodata)
        if index == 'oc3':
            if self.satellite == 'Landsat 8/9':
                err, res = _prepare_inputs(conversion, nodata, 1, 2, 3)
            if err is not None:
                return err, ()
            geotransform, projection, notes, inputs = res
            result = indcal.oc3(*inputs, nodata)
        if index == 'cdom_ndwi':
            ph_unit = 'mg/L'
            if self.satellite == 'Landsat 8/9':
                err, res = _prepare_inputs(conversion, nodata, 3, 5)
            if err is not None:
                return err, ()
            geotransform, projection, notes, inputs = res
            result = indcal.cdom_ndwi(*inputs, nodata)
        if index == 'toa_temperature_landsat':
            if not (self.satellite == 'Landsat 8/9' and self.proc_level == 'L1TP'):
                return IndexErr(20501, f"index '{index}' is not supported for {self.satellite} {self.proc_level}"), ()
            ph_unit = '°C'
            err, res = _prepare_inputs('toa_rad', nodata, 10)
            if err is not None:
                return err, ()
            geotransform, projection, _, inputs = res
            ds = self.ds_man.get(self.ds_man.find("10"))
            result = indcal.landsat_l1_toa_radiance_to_toa_temperature(*inputs, ds.thermal_k1, ds.thermal_k2, nodata, 'C')
        if index == 'ls_temperature_landsat':
            if self.satellite != 'Landsat 8/9':
                return IndexErr(20501, f"index '{index}' is not supported for {self.satellite} {self.proc_level}"), ()
            ph_unit = '°C'
            if self.proc_level == 'L1TP':
                id_ = self.ds_man.find('toa_temperature_landsat')
                if id_ is not None:
                    temperature_toa = self.ds_man.get(id_)
                    geotransform = temperature_toa.dataset.GetGeoTransform()
                    projection = temperature_toa.dataset.GetProjection()
                    data_type = temperature_toa.dataset.GetRasterBand(1).DataType
                    nodata = temperature_toa.no_data
                    temperature_toa = self.ds_man.read_band(id_, 1)
                else:
                    err, res = self._index('toa_temperature_landsat')
                    if err is not None:
                        return err, ()
                    geotransform, projection, temperature_toa, data_type, nodata, _, _ = res
                andwi = self.ds_man.find('andwi')
                if andwi is not None:
                    andwi = self.ds_man.read_band(andwi, 1)
                else:
                    err, res = self._index('andwi')
                    _, _, andwi, _, _, _, _ = res
                ndbi = self.ds_man.find('ndbi')
                if ndbi is not None:
                    ndbi = self.ds_man.read_band(ndbi, 1)
                else:
                    err, res = self._index('ndbi')
                    _, _, ndbi, _, _, _, _ = res
                ndvi = self.ds_man.find('ndvi')
                if ndvi is not None:
                    ndvi = self.ds_man.read_band(ndvi, 1)
                else:
                    err, res = self._index('ndvi')
                    _, _, ndvi, _, _, _, _ = res
                water, _ = indcal.otsu_binarization(andwi, 2)
                water = np.ma.array(water, dtype=np.bool)
                built_up = np.ma.empty(ndbi.shape, dtype=np.bool)
                built_up[~ndbi.mask] = np.ma.where(ndbi[~ndbi.mask] > 0.2, True, False)
                result = indcal.landsat_l1_toa_temperature_to_ls_temperature(temperature_toa, ndvi, water, built_up, nodata)
            if self.proc_level == 'L2SP':
                ph_unit = '°C'
                id_ = self.ds_man.find("10")
                if id_ is None:
                    return IndexErr(20502, f"unable to calculate index '{index}': {self.satellite} band number 10 is needed"), ()
                ds = self.ds_man.get(id_)
                geotransform = ds.dataset.GetGeoTransform()
                projection = ds.dataset.GetProjection()
                result = self.ds_man.read_band(id_, 1)
                result = indcal.landsat_l2_dn_to_ls_temperature(result, nodata, 'C')
        if index == 'ndvi':
            if self.satellite == 'Landsat 8/9':
                err, res = _prepare_inputs('ls_refl', nodata, 5, 4)
            if err is not None:
                return err, ()
            geotransform, projection, notes, inputs = res
            result = indcal.ndvi(*inputs, nodata)
        if index == 'ndbi':
            if self.satellite == 'Landsat 8/9':
                err, res = _prepare_inputs('ls_refl', nodata, 6, 5)
            if err is not None:
                return err, ()
            geotransform, projection, notes, inputs = res
            result = indcal.ndbi(*inputs, nodata)
        return None, (geotransform, projection, result, data_type, nodata, ph_unit, notes)

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
                return _response(20003, {"error": "request 'import_gtiff' was received before 'set_satellite' request"})
            file, band, nodata = parameters['file'], parameters['band'], -1
            if self.satellite == 'Landsat 8/9':
                nodata = 0
                if band == 'QA_PIXEL':
                    nodata = 1
            try:
                dataset_id = self.ds_man.open(file, band, nodata)
            except RuntimeError:
                return _response(20301, {"error": f"failed to open file '{file}'"})
            except ValueError:
                return _response(20300, {"error": f"provided file '{file}' is not a GeoTiff image"})
            dataset = self.ds_man.get(dataset_id).dataset
            if dataset.GetDriver().ShortName != 'GTiff':
                return _response(20300, {"error": f"provided file '{file}' is not a GeoTiff image"})

            if self.satellite == 'Landsat 8/9' and band == 'QA_PIXEL':
                cloud_mask = self.ds_man.read_band(dataset_id, 1).astype(np.uint16)
                cloud_mask = indcal.cloud_mask(cloud_mask, 3)
                self.ds_man.add_cloud_mask(cloud_mask)
            
            geotransform = dataset.GetGeoTransform()
            result = {
                'file': file,
                'band': band,
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
                return _response(20003, {"error": "request 'calc_preview' was received before 'set_satellite' request"})
            index, width, height = parameters['index'], parameters['width'], parameters['height']
            if index not in self.SUPPORTED_INDICES and index != 'nat_col':
                return _response(20400, {"error": f"index '{index}' is not supported or unknown"})
            ids = []
            if index == 'nat_col':
                if self.satellite == 'Landsat 8/9':
                    ids.append(self.ds_man.find("4"))
                    ids.append(self.ds_man.find("3"))
                    ids.append(self.ds_man.find("2"))
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
            r, g, b, a = 0, 0, 0, 0
            r = self.ds_man.read_band(ids[0], 1, resolution_percent=res)
            r = indcal.map_to_8bit(r)
            a = r.mask
            if index == 'nat_col':
                g = self.ds_man.read_band(ids[1], 1, resolution_percent=res)
                b = self.ds_man.read_band(ids[2], 1, resolution_percent=res)
                g = indcal.map_to_8bit(g)
                b = indcal.map_to_8bit(b)
                a = a | g.mask | b.mask
            else:
                g = r
                b = r
            a = np.array(np.where(a, 0, 255), dtype=np.uint8)

            pv_id = self.pv_man.add(np.transpose(np.stack((r, g, b, a)), (1, 2, 0)), index)
            return _response(0, {
                "url": pv_id
            })

        if operation == 'calc_index':
            if self.satellite is None or self.proc_level is None:
                return _response(20003, {"error": "request 'calc_index' was received before 'set_satellite' request"})
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
                geotransform, projection, result, data_type, nodata, ph_unit, notes_ = res

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
            dataset_id = self.ds_man.add_index(res_ds, index, nodata, stats)
            self.ds_man.add_description(dataset_id, notes=notes_)

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

        if operation == 'import_metafile':
            if self.satellite is None or self.proc_level is None:
                return _response(20003, {"error": "request 'import_metafile' was received before 'set_satellite' request"})
            filename, file = parameters['file'], 0
            try:
                file = open(filename, 'r', encoding='utf-8')
            except OSError:
                return _response(20801, {"error": f"failed to open metadata file '{filename}'"})

            with file:
                if self.satellite == 'Landsat 8/9' and self.proc_level == 'L1TP':
                    parsing = False
                    count, count_1_9, count_10_11 = 0, 0, 0
                    for l in file:
                        if self.ds_man.get_sun_elevation() is None and 'SUN_ELEVATION' in l:
                            _, _, s_elev = l.partition('=')
                            try:
                                s_elev = float(s_elev.strip())
                            except ValueError:
                                return _response(20800, {"error": f"metadata file '{filename}' is invalid, unsupported or does not contain calibration coefficients"})
                            self.ds_man.set_sun_elevation(s_elev)
                            count += 1
                            continue
                        if self.ds_man.get_earth_sun_distance() is None and 'EARTH_SUN_DISTANCE' in l:
                            _, _, es_dist = l.partition('=')
                            try:
                                es_dist = float(es_dist.strip())
                            except ValueError:
                                return _response(20800, {"error": f"metadata file '{filename}' is invalid, unsupported or does not contain calibration coefficients"})
                            self.ds_man.set_earth_sun_distance(es_dist)
                            count += 1
                            continue
                        if 'MIN_MAX_RADIANCE' in l:
                            parsing = True if not parsing else False
                            continue
                        if parsing and 'RADIANCE_MAXIMUM' in l:
                            band, _, coeff = l.partition('=')
                            band = band.strip()[-2:]
                            band = band[1:] if band[0] == '_' else band
                            try:
                                coeff = float(coeff.strip())
                            except ValueError:
                                return _response(20800, {"error": f"metadata file '{filename}' is invalid, unsupported or does not contain calibration coefficients"})
                            id__ = self.ds_man.find(band)
                            if id__ is not None:
                                self.ds_man.get(id__).rad_max = coeff
                                if band in ('10', '11'):
                                    count_10_11 += 1
                                else:
                                    count_1_9 += 1
                            continue
                        if 'MIN_MAX_REFLECTANCE' in l:
                            parsing = True if not parsing else False
                            continue
                        if parsing and 'REFLECTANCE_MAXIMUM' in l:
                            band, _, coeff = l.partition('=')
                            band = band.strip()[-2:]
                            band = band[1:] if band[0] == '_' else band
                            try:
                                coeff = float(coeff.strip())
                            except ValueError:
                                return _response(20800, {"error": f"metadata file '{filename}' is invalid, unsupported or does not contain calibration coefficients"})
                            id__ = self.ds_man.find(band)
                            if id__ is not None:
                                self.ds_man.get(id__).refl_max = coeff
                                count_1_9 += 1
                            continue
                        if 'RADIOMETRIC_RESCALING' in l:
                            parsing = True if not parsing else False
                            continue
                        if parsing and 'RADIANCE' in l:
                            band, _, coeff = l.partition('=')
                            band = band.strip()[-2:]
                            band = band[1:] if band[0] == '_' else band
                            try:
                                coeff = float(coeff.strip())
                            except ValueError:
                                return _response(20800, {"error": f"metadata file '{filename}' is invalid, unsupported or does not contain calibration coefficients"})
                            id__ = self.ds_man.find(band)
                            if id__ is not None:
                                if 'MULT' in l:
                                    self.ds_man.get(id__).radio_mult = coeff
                                    if band in ('10', '11'):
                                        count_10_11 += 1
                                    else:
                                        count_1_9 += 1
                                if 'ADD' in l:
                                    self.ds_man.get(id__).radio_add = coeff
                                    if band in ('10', '11'):
                                        count_10_11 += 1
                                    else:
                                        count_1_9 += 1
                            continue
                        if 'THERMAL_CONSTANTS' in l:
                            parsing = True if not parsing else False
                            continue
                        if parsing and 'CONSTANT' in l:
                            band, _, coeff = l.partition('=')
                            const = band.strip()[:2]
                            band = band.strip()[-2:]
                            if const not in ('K1', 'K2'):
                                return _response(20800, {"error": f"metadata file '{filename}' is invalid, unsupported or does not contain calibration coefficients"})
                            try:
                                coeff = float(coeff.strip())
                            except ValueError:
                                return _response(20800, {"error": f"metadata file '{filename}' is invalid, unsupported or does not contain calibration coefficients"})
                            id__ = self.ds_man.find(band)
                            if id__ is not None:
                                if const == 'K1':
                                    self.ds_man.get(id__).thermal_k1 = coeff
                                    count_10_11 += 1
                                if const == 'K2':
                                    self.ds_man.get(id__).thermal_k2 = coeff
                                    count_10_11 += 1
                            continue
                if count + count_1_9 + count_10_11 == 0:
                    return _response(20800, {"error": f"metadata file '{filename}' is either invalid or does not contain calibration coefficients"})
            return _response(0, {
                "loaded": count_1_9 / 4 + count_10_11 / 5
            })

        if operation == 'generate_description':
            index, lang = parameters['index'], parameters['lang']
            if not (index in self.SUPPORTED_INDICES or index == 'summary'):
                return _response(20900, {"error": f"index '{index}' is not supported or unknown"})
            # error 20901
            ds, desc = None, ''
            if index == 'summary':
                ds = self.ds_man.find('water_mask')
            else:
                ds = self.ds_man.find(index)
            if ds is None:
                return _response(20902, {"error": f"index '{index}' is not calculated"})

            # request to external service here
            desc = self.ds_man.get_description(ds)
            if desc is None:
                desc = ''
            else:
                if index == 'summary':
                    desc = desc['notes']
                else:
                    desc = desc['notes'] + '\n' + desc['text']

            return _response(0, {
                "index": index,
                "desc": desc
            })
        
        return _response(-1, {"error": "how's this even possible?"})

    def get_water_mask(self, width: int, height: int) -> np.ma.MaskedArray[np.bool] | None:
        """Returns a boolean array where True=water and False=non-water. Returns None if water mask was not created.
        If 'width' > 'height', array size is [width, y], y < height, otherwise [x, height], x < width."""

        id_ = self.ds_man.find('water_mask')
        if id_ is None:
            return None

        mask = self.ds_man.get(id_)
        res = 100
        if not (width == mask.dataset.RasterXSize and height == mask.dataset.RasterYSize):
            if height <= width:
                res = height / mask.dataset.RasterYSize * 100
            else:
                res = width / mask.dataset.RasterXSize * 100
        mask = self.ds_man.read_band(id_, 1, resolution_percent=res)
        return np.ma.array(mask, dtype=np.bool)

    def get_version(self) -> str:
        return self.VERSION

    def get_supported_protocol_versions(self) -> tuple[str]:
        return self.SUPPORTED_PROTOCOL_VERSIONS

    def get_supported_indices(self) -> tuple[str]:
        return self.SUPPORTED_INDICES

    def get_water_extraction_indices(self) -> tuple[str]:
        return self.WATER_EXTRACTION_INDICES

    def get_supported_operations(self) -> tuple[str]:
        return self.supported_operations

    def get_supported_satellites(self) -> dict:
        return self.SUPPORTED_SATELLITES
