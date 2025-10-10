import numpy as np
from math import isclose

FLOAT_PRECISION = 1e-10

def map_to_8bit(array: np.ma.MaskedArray) -> np.ma.MaskedArray:
    """Fits 'array's values into [0; 255] range and returns a new masked array of uint8 type.
    If 'array's range is 0, i.e. array.min() == array.max(), all values are set to 0."""

    min_, max_ = array.min(), array.max()
    if isclose(min_, max_, rel_tol=FLOAT_PRECISION):
        return np.ma.zeros(array.shape, dtype=np.uint8)
    else:
        return np.ma.array((array - min_) / (max_ - min_) * 255, dtype=np.uint8)

def _test(array1: np.ma.MaskedArray, array2: np.ma.MaskedArray, nodata: int | float) -> np.ma.MaskedArray:
    """array1 / array2"""
    
    test = np.ma.empty(array1.shape, dtype=np.float32)
    zeros = np.isclose(array2, 0, rtol=FLOAT_PRECISION)
    test[~zeros] = array1[~zeros] / array2[~zeros]
    test[zeros] = nodata
    test[array1.mask] = nodata
    return test

def wi2015(green: np.ma.MaskedArray, red: np.ma.MaskedArray, nir: np.ma.MaskedArray, swir1: np.ma.MaskedArray, swir2: np.ma.MaskedArray, nodata: int | float) -> np.ma.MaskedArray:
    """1.7204 + 171*green + 3*red - 70*nir - 45*swir1 - 71*swir2"""
    
    wi2015 = np.ma.empty(green.shape, dtype=np.float32)
    wi2015 = 1.7204 + 171*green + 3*red - 70*nir - 45*swir1 - 71*swir2
    wi2015[green.mask] = nodata
    return wi2015

def nsmi(red: np.ma.MaskedArray, green: np.ma.MaskedArray, blue: np.ma.MaskedArray, nodata: int | float) -> np.ma.MaskedArray:
    """(red + green - blue) / (red + green + blue)"""
    
    nsmi = np.ma.empty(red.shape, dtype=np.float32)
    numerator = red + green - blue
    denominator = red + green + blue
    zeros = np.isclose(denominator, 0, rtol=FLOAT_PRECISION)
    nsmi[~zeros] = numerator[~zeros] / denominator[~zeros]
    nsmi[zeros] = nodata
    nsmi[red.mask] = nodata
    return nsmi
