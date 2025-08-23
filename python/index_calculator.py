import numpy as np
from math import isclose

FLOAT_PRECISION = 1e-10

def map_to_8bit(array: np.ndarray) -> np.ndarray:
    """Fits 'array's values into [0; 255] range and returns a new array of uint8 type.
    If 'array's range is 0, i.e. array.min() == array.max(), all values are set to 0."""

    min, max = array.min(), array.max()
    if isclose(min, max, rel_tol=FLOAT_PRECISION):
        return np.zeros(array.shape, dtype=np.uint8)
    else:
        return np.array((array - min) / (max - min) * 255, dtype=np.uint8)

def _test(array1: np.ndarray, array2: np.ndarray, nodata: int | float) -> np.ndarray:
    """array1 / array2"""
    
    test = np.empty(array1.shape, dtype=np.float32)
    zeros = np.isclose(array2, 0, rtol=FLOAT_PRECISION)
    test[zeros] = nodata
    test[~zeros] = array1[~zeros] / array2[~zeros]
    return test
