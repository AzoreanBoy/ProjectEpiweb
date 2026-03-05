import pywt
import numpy as np


def coefficients_energy(data, mother_wavelet, decomposition_level):

    # extraction of the aproximation(a) and details(d) reconstructed
    all_d = decomposite(data, 'd', mother_wavelet, decomposition_level)

    # reconstruc = all d coefficients (d1,d2,...,df) + coeff af
    reconstruc = all_d

    # same size (ignore last extra elements)
    reconstruc = [array_d[0:len(data)] for array_d in reconstruc]

    # energy values
    energy_values = [energy(reconstruc, k)
                     for k in range(0, decomposition_level, 1)]

    return energy_values


def decomposite(data, coef_type, mother_wavelet, decomposition_level):
    ca = []
    cd = []
    for i in range(decomposition_level):
        (a, d) = pywt.dwt(data, mother_wavelet)
        ca.append(a)
        cd.append(d)
        # the next decomposition is performed in the aproximation (a) of the previous level
        data = a
    rec_a = []
    rec_d = []
    for i, coeff in enumerate(ca):
        coeff_list = [coeff, None] + [None] * i
        rec_a.append(pywt.waverec(coeff_list, mother_wavelet))
    for i, coeff in enumerate(cd):
        coeff_list = [None, coeff] + [None] * i
        rec_d.append(pywt.waverec(coeff_list, mother_wavelet))
    if coef_type == 'd':
        return rec_d
    elif coef_type == 'a':
        return rec_a


def energy(array_coeff, k):
    return np.sum(array_coeff[k]**2)
