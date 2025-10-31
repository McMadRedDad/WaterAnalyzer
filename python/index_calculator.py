import numpy as np
from math import isclose

FLOAT_PRECISION = 1e-6

def map_to_8bit(array: np.ma.MaskedArray) -> np.ma.MaskedArray:
    """Fits 'array's values into [0; 255] range and returns a new masked array of uint8 type.
    If 'array's range is 0, i.e. array.min() == array.max(), all values are set to 0."""

    arr = np.nan_to_num(array.data, nan=0)
    min_, max_ = arr.min(), arr.max()
    if isclose(min_, max_, abs_tol=FLOAT_PRECISION):
        return np.ma.array(np.zeros(array.shape), mask=array.mask, dtype=np.uint8)
    else:
        return np.ma.array((arr - min_) / (max_ - min_) * 255, mask=array.mask, dtype=np.uint8)

def _full_mask(array: np.ma.MaskedArray, *arrays: np.ma.MaskedArray) -> np.typing.NDArray[bool]:
    """Combines masks from every array into one preserving invalid bits from each mask and returns it."""

    mask = array.mask
    for a in arrays:
        mask |= a.mask
    return mask

def _test(array1: np.ma.MaskedArray, array2: np.ma.MaskedArray, nodata: int | float) -> np.ma.MaskedArray:
    """array1 / array2"""
    
    test = np.ma.empty(array1.shape, dtype=np.float32)
    mask = _full_mask(array1, array2)
    zeros = np.isclose(array2, 0, atol=FLOAT_PRECISION)
    test[~zeros] = array1[~zeros] / array2[~zeros]
    test[zeros] = nodata
    test[mask] = nodata
    test.mask = mask
    return test

def wi2015(green: np.ma.MaskedArray, red: np.ma.MaskedArray, nir: np.ma.MaskedArray, swir1: np.ma.MaskedArray, swir2: np.ma.MaskedArray, nodata: int | float) -> np.ma.MaskedArray:
    """1.7204 + 171*green + 3*red - 70*nir - 45*swir1 - 71*swir2"""
    
    wi2015 = np.ma.empty(green.shape, dtype=np.float32)
    mask = _full_mask(green, red, nir, swir1, swir2)
    wi2015 = 1.7204 + 171*green + 3*red - 70*nir - 45*swir1 - 71*swir2
    wi2015[mask] = nodata
    wi2015.mask = mask
    return wi2015

def nsmi(red: np.ma.MaskedArray, green: np.ma.MaskedArray, blue: np.ma.MaskedArray, nodata: int | float) -> np.ma.MaskedArray:
    """(red + green - blue) / (red + green + blue)"""
    
    nsmi = np.ma.empty(red.shape, dtype=np.float32)
    mask = _full_mask(red, green, blue)
    numerator = red + green - blue
    denominator = red + green + blue
    zeros = np.isclose(denominator, 0, atol=FLOAT_PRECISION)
    nsmi[~zeros] = numerator[~zeros] / denominator[~zeros]
    nsmi[zeros] = nodata
    nsmi[mask] = nodata
    nsmi.mask = mask
    return nsmi

def oc3(aerosol: np.ma.MaskedArray, blue: np.ma.MaskedArray, green: np.ma.MaskedArray, nodata: int | float) -> np.ma.MaskedArray:
    """max(aerosol, blue) / green"""

    oc3 = np.ma.empty(aerosol.shape, dtype=np.float32)
    mask = _full_mask(aerosol, blue, green)
    zeros = np.isclose(green, 0, atol=FLOAT_PRECISION)
    oc3[~zeros] = np.maximum(aerosol, blue)[~zeros] / green[~zeros]
    oc3[zeros] = nodata
    oc3[mask] = nodata
    oc3.mask = mask
    return oc3

def cdom_ndwi(green: np.ma.MaskedArray, nir: np.ma.MaskedArray, nodata: int | float) -> np.ma.MaskedArray:
    """2119.5*ndwi^3 + 4559.1*ndwi^2 - 2760.4*ndwi + 603.6
    ndwi = (green - nir) / (green + nir)"""

    cdom_ndwi = np.ma.empty(green.shape, dtype=np.float32)
    ndwi = np.ma.empty(green.shape, dtype=np.float32)
    mask = _full_mask(green, nir)
    numerator = green - nir
    denominator = green + nir
    zeros = np.isclose(denominator, 0, atol=FLOAT_PRECISION)
    ndwi[~zeros] = numerator[~zeros] / denominator[~zeros]
    ndwi[zeros] = nodata
    cdom_ndwi[~zeros] = 2119.5*ndwi[~zeros]**3 + 4559.1*ndwi[~zeros]**2 - 2760.4*ndwi[~zeros] + 603.6
    cdom_ndwi[zeros] = nodata
    cdom_ndwi[mask] = nodata
    cdom_ndwi.mask = mask
    return cdom_ndwi

def landsat_dn_to_radiance(array: np.ma.MaskedArray, mult_factor: float, add_factor: float, nodata: float | int) -> np.ma.MaskedArray:
    """mult_factor * array + add_factor"""

    radiance = np.ma.empty(array.shape, dtype=np.float32)
    mask = array.mask
    radiance = mult_factor * array + add_factor
    radiance[mask] = nodata
    radiance.mask = mask
    return radiance

def landsat_temperature_toa(radiance: np.ma.MaskedArray, K1: float, K2: float, nodata: float | int, unit: str) -> np.ma.MaskedArray:
    """'unit' is either 'K' or 'C'
    for unit='K': temperature_toa = K2 / ln(K1/radiance + 1)
    for unit='C': temperature_toa = K2 / ln(K1/radiance + 1) - 273,15"""

    if unit not in ('K', 'C'):
        raise ValueError(f'invalid value "{unit}" passed as "unit" argument for "landsat_temperature_toa" function')
    temperature_toa = np.ma.empty(radiance.shape, dtype=np.float32)
    mask = radiance.mask
    denominator = np.log1p(K1 / radiance)
    zeros = np.isclose(denominator, 0, atol=FLOAT_PRECISION)
    if unit == 'K':
        temperature_toa[~zeros] = K2 / denominator[~zeros]
    if unit == 'C':
        temperature_toa[~zeros] = K2 / denominator[~zeros] - 273.15
    temperature_toa[zeros] = nodata
    temperature_toa[mask] = nodata
    temperature_toa.mask = mask
    return temperature_toa

def ndvi(nir: np.ma.MaskedArray, red: np.ma.MaskedArray, nodata: float | int) -> np.ma.MaskedArray:
    """(nir - red) / (nir + red)"""

    ndvi = np.ma.empty(nir.shape, dtype=np.float32)
    mask = _full_mask(nir, red)
    numerator = nir - red
    denominator = nir + red
    zeros = np.isclose(denominator, 0, atol=FLOAT_PRECISION)
    ndvi[~zeros] = numerator[~zeros] / denominator[~zeros]
    ndvi[zeros] = nodata
    ndvi[mask] = nodata
    ndvi.mask = mask
    return ndvi
