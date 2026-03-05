import numpy as np
from .utils.f_PowSpec import f_PowSpec


def f_SpecEdgeFreq(
    signal: np.ndarray,
    sampleRate: float,
    freqRef=None,
    percentage: float = 75,
    minFreq: float = 0,
    ARMethod: int = 0,
):
    """
    This function computes the edge frequency of the power spectral density of the input signal.

    Args:
        - signal (numpy.ndarray): input signal with matrix of n x m where n is the number of samples and m is the number of channels
        - sampleRate (float): sample rate of the signal in HZ
        - freqRef (optional): frequency reference for the edge frequency. Defaults half of the sample rate.
        - percentage (float, optional): percentage used to obtain the edge frequency (value in %). Defaults to 75%.
        - minFreq (float, optional): minimal frequency from wich the edge frequency is computed. Defaults to 0 Hz.
        - ARMethod (int, optional): set to 1 to compute the power spectral density via an AR model estimator. Defaults to 0 (FFT Squared Modulus Estimator).

    Returns:
        - v_SEF: edge frequency of the power spectral density
        - v_EdgePower: power of the signal at the edge frequency
    """

    freqRef = freqRef if freqRef else sampleRate / 2

    v_SEF = []
    v_EdgePower = []

    channels = signal.shape[1] if len(signal.shape) > 1 else 1
    for channel in range(channels):
        if len(signal.shape) > 1:
            v_powerSpec, v_freq, _ = f_PowSpec(signal[:, channel], sampleRate, ARMethod)
        else:
            v_powerSpec, v_freq, _ = f_PowSpec(signal, sampleRate, ARMethod)

        if minFreq == 0:
            minFreqIdx = 0
        else:
            minFreqIdx = np.where(v_freq >= minFreq)[0][0]

        try:
            freqRefIdx = np.where(v_freq >= freqRef)[0][0]
        except IndexError:
            freqRefIdx = np.argmax(v_freq)

        s_RefPow = np.sum(v_powerSpec[: freqRefIdx + 1])
        s_RefPow *= percentage / 100
        SEF = np.where(np.cumsum(v_powerSpec[minFreqIdx : freqRefIdx + 1]) >= s_RefPow)[
            0
        ]

        if SEF.size != 0:
            SEF = SEF[0] + minFreqIdx - 1

            v_SEF.append(v_freq[SEF])
            v_EdgePower.append(v_powerSpec[SEF])
        else:
            SEF = -1
            EdgePower = -1

            v_SEF.append(SEF)
            v_EdgePower.append(EdgePower)

    return v_SEF, v_EdgePower
