import numpy as np
from math import isclose

def map_to_8bit(array: np.ndarray) -> np.ndarray:
    """Fits 'array's values into [0; 255] range and returns a new array of uint8 type.
    If 'array's range is 0, e.g. array.min() == array.max(), all values are set to 0."""

    min, max = array.min(), array.max()
    if isclose(min, max, rel_tol=1e-10):
        return np.zeros(array.shape, dtype=np.uint8)
    else:
        return np.array((array - min) / (max - min) * 255, dtype=np.uint8)