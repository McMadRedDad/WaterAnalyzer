import numpy as np

FLOAT_PRECISION = 1e-6

def map_to_8bit(array: np.ma.MaskedArray) -> np.ma.MaskedArray:
    """Fits 'array's values into [0; 255] range and returns a new masked array of uint8 type.
    If 'array's range is 0, i.e. array.min() == array.max(), all values are set to 0."""

    mask_ = array.mask
    arr = np.ma.array(np.nan_to_num(array.data, nan=0), mask=mask_)
    min_, max_ = arr.min(), arr.max()
    if np.isclose(min_, max_, atol=FLOAT_PRECISION):
        return np.ma.array(np.zeros(array.shape), mask=mask_, dtype=np.uint8)
    else:
        return np.ma.array((arr - min_) / (max_ - min_) * 255, mask=mask_, dtype=np.uint8)

def _otsu_threshold(array: np.ma.MaskedArray, nbins: int) -> float:
    """Using Otsu method, calculates threshold that best divides 'array's values into 2 classes and returns it.
    'nbins' defines length of the probability histogram."""

    data = array.compressed()
    if len(data) == 0:
        raise ValueError('Cannot calc Otsu threshold for array with all elements masked')

    hist, bin_edges = np.histogram(data, nbins)  # probability distribution (number of occurencies)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2  # centers of each of histogram's ranges, correspond to actual value

    prob = hist / hist.sum()
    cum_sum = np.cumsum(prob)  # cum_sum of the whole data range = 1 (sum of probabilities)
    cum_mean = np.cumsum(prob * bin_centers)
    
    glob_mean = cum_mean[-1]  # global mean ~ cumulative mean for the whole data range
    max_var = 0
    best_thresh = bin_centers[0]
    for i in range(1, nbins):
        if np.isclose(cum_sum[i], 0, atol=FLOAT_PRECISION) or np.isclose(cum_sum[i], 1, atol=FLOAT_PRECISION):
            continue

        mean0 = cum_mean[i] / cum_sum[i]  # mean of class0 (below threshold=current bin center)
        mean1 = (glob_mean - cum_mean[i]) / (1 - cum_sum[i])  # mean of class1 (above threshold=current bin center)
        inter_var = cum_sum[i] * (1 - cum_sum[i]) * (mean0 - mean1) ** 2  # main resulting formula by Otsu
        if inter_var > max_var:  # if inter_var > current variance, update current threshold
            max_var = inter_var
            best_thresh = bin_centers[i]
    
    return best_thresh

def otsu_binarization(array: np.ma.MaskedArray, nodata: int, nbins: int=256) -> np.ma.MaskedArray:
    ret = np.ma.empty(array.shape, dtype=np.uint8)
    mask = array.mask
    threshold = _otsu_threshold(array, nbins)
    ret[~mask] = np.ma.where(array[~mask] > threshold, 1, 0)
    ret[mask] = nodata
    ret.mask = mask
    return ret

def landsat_l1_dn_to_toa_radiance(dn: np.ma.MaskedArray, radio_mult: float, radio_add: float, nodata: float | int) -> np.ma.MaskedArray:
    """Converts DN to TOA radiance."""

    toa_rad = np.ma.empty(dn.shape, dtype=np.float32)
    mask = dn.mask
    toa_rad = radio_mult * dn + radio_add
    toa_rad[mask] = nodata
    toa_rad.mask = mask
    return toa_rad

def landsat_l1_dn_to_toa_reflectance(dn: np.ma.MaskedArray, radio_mult: float | int, radio_add: float | int, sun_elev: float | int, earth_sun_dist: float | int, rad_max: float | int, refl_max: float | int, nodata: float | int) -> np.ma.MaskedArray:
    """Converts DN to TOA reflectance. Negative reflectance is mapped to 1.01*FLOAT_PRECISION."""

    if np.isclose(refl_max, 0, atol=FLOAT_PRECISION):
        raise ZeroDivisionError(f'maximum reflectance = {refl_max}')
    if np.isclose(earth_sun_dist, 0, atol=FLOAT_PRECISION):
        raise ZeroDivisionError(f'Earth Sun distance = {earth_sun_dist}')

    toa_refl = np.ma.empty(dn.shape, dtype=np.float32)
    mask = dn.mask
    pi_d2 = np.pi * earth_sun_dist**2
    E_sun = pi_d2 * rad_max / refl_max
    sun_rad = E_sun * np.sin(sun_elev * np.pi/180) / pi_d2
    toa_rad = landsat_l1_dn_to_toa_radiance(dn, radio_mult, radio_add, nodata)
    toa_refl = toa_rad / sun_rad
    toa_refl[toa_refl < 0] = FLOAT_PRECISION * 1.01
    toa_refl[mask] = nodata
    toa_refl.mask = mask
    return toa_refl

def landsat_l1_dn_to_dos1_reflectance(dn: np.ma.MaskedArray, radio_mult: float | int, radio_add: float | int, sun_elev: float | int, earth_sun_dist: float | int, rad_max: float | int, refl_max: float | int, nodata: float | int) -> np.ma.MaskedArray:
    """DOS1 algorithm to approximately account for atmosphere. Converts DN to LS reflectance. Negative reflectance is mapped to 1.01*FLOAT_PRECISION."""

    if np.isclose(refl_max, 0, atol=FLOAT_PRECISION):
        raise ZeroDivisionError(f'maximum reflectance = {refl_max}')
    if np.isclose(earth_sun_dist, 0, atol=FLOAT_PRECISION):
        raise ZeroDivisionError(f'Earth Sun distance = {earth_sun_dist}')

    def _darkest_dn(DN, pixel_count=1000):
        data = DN.compressed()
        hist, bin_edges = np.histogram(data, bins=int(data.min()+data.max()+2))
        for i, count in enumerate(hist):
            if count >= pixel_count:
                return np.ceil(bin_edges[i])
        return np.ceil(data.min())

    ls_refl = np.ma.empty(dn.shape, dtype=np.float32)
    mask = dn.mask
    pi_d2 = np.pi * earth_sun_dist**2
    E_sun = pi_d2 * rad_max / refl_max
    sun_rad = E_sun * np.sin(sun_elev * np.pi/180) / pi_d2
    dark_dn = _darkest_dn(dn, dn.size * 0.05)
    dark_rad = radio_mult * dark_dn + radio_add
    path_rad = dark_rad - 0.01 * sun_rad
    toa_rad = landsat_l1_dn_to_toa_radiance(dn, radio_mult, radio_add, nodata)
    ls_rad = toa_rad - path_rad
    ls_refl = ls_rad / sun_rad
    ls_refl[ls_refl < 0] = FLOAT_PRECISION * 1.01
    ls_refl[mask] = nodata
    ls_refl.mask = mask
    return ls_refl

def cloud_mask(array: np.ma.MaskedArray, bit_pos: int) -> np.ma.MaskedArray:
    """Returns a boolean array of bits at 'bit_pos'."""

    if bit_pos < 0 or bit_pos > 15:
        raise ValueError(f'Cloud mask is 16 bit, but bit position {bit_pos} provided')

    ret = np.ma.empty(array.shape, dtype=np.bool)
    mask = array.mask
    ret[~mask] = ((array[~mask] & (1 << bit_pos)) >> bit_pos) != 0
    ret.mask = mask
    return ret

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

def landsat_temperature_toa(radiance: np.ma.MaskedArray, K1: float, K2: float, nodata: float | int, unit: str) -> np.ma.MaskedArray:
    """'unit' is either 'K' or 'C'
    for unit='K': temperature_toa = K2 / ln(K1/radiance + 1)
    for unit='C': temperature_toa = K2 / ln(K1/radiance + 1) - 273,15"""

    if unit not in ('K', 'C'):
        raise ValueError(f'invalid value "{unit}" passed as "unit" argument to "landsat_temperature_toa" function')

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

def andwi(blue: np.ma.MaskedArray, green: np.ma.MaskedArray, red: np.ma.MaskedArray, nir: np.ma.MaskedArray, swir1: np.ma.MaskedArray, swir2: np.ma.MaskedArray, nodata: int | float) -> np.ma.MaskedArray:
    """(blue + green + red - nir - swir1 - swir2) / (blue + green + red + nir + swir1 + swir2)"""
    
    andwi = np.ma.empty(blue.shape, dtype=np.float32)
    mask = _full_mask(blue, green, red, nir, swir1, swir2)
    numerator = blue + green + red - nir - swir1 - swir2
    denominator = blue + green + red + nir + swir1 + swir2
    zeros = np.isclose(denominator, 0, atol=FLOAT_PRECISION)
    andwi[~zeros] = numerator[~zeros] / denominator[~zeros]
    andwi[zeros] = nodata
    andwi[mask] = nodata
    andwi.mask = mask
    return andwi

def ndbi(swir1: np.ma.MaskedArray, nir: np.ma.MaskedArray, nodata: int | float) -> np.ma.MaskedArray:
    """(swir1 - nir) / (swir1 + nir)"""
    
    ndbi = np.ma.empty(swir1.shape, dtype=np.float32)
    mask = _full_mask(swir1, nir)
    numerator = swir1 - nir
    denominator = swir1 + nir
    zeros = np.isclose(denominator, 0, atol=FLOAT_PRECISION)
    ndbi[~zeros] = numerator[~zeros] / denominator[~zeros]
    ndbi[zeros] = nodata
    ndbi[mask] = nodata
    ndbi.mask = mask
    return ndbi
