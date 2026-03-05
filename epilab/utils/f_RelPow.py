import numpy as np
from .f_PowSpec import f_PowSpec


def f_RelPow(signal: np.ndarray, fs: float, freqRanges: np.ndarray, ARMethod: int = 0):
    """
    Computes the Relative Power of a signal in a set of frequency bands.

    Args:
        - signal (np.ndarray): input signal of 1D array
        - fs (float): sample rate in Hz
        - freqRanges(np.ndarray): nx2 matrix containing the frequency ranges to compute the relative power. Each row contains the start and end frequencies of the range. n is the number of frequency bands.
        - ARMethod (int, optional): set to 1 to compute the power spectral density via an AR (Autoregressive) method. Defaults to 0 (FFT Squared Modulus Estimator).

    Returns:
        - relPow (np.ndarray): relative power of the signal in each frequency band
        - PowSpec (np.ndarray): power spectral density of the signal from 0 to fs/2
        - freqs (np.ndarray): center frequencies of the frequency bands
    """

    v_RelPow = np.zeros(freqRanges.shape[0])  # Initialize the relative power vector

    # Compute the power spectral density of the signal
    PowSpec, freqs, totalPower = f_PowSpec(signal, fs, ARMethod)

    for band in range(freqRanges.shape[0]):
        v_ind = np.where(
            (freqs >= freqRanges[band, 0]) & (freqs <= freqRanges[band, 1])
        )[0]
        v_RelPow[band] = np.sum(PowSpec[v_ind]) / totalPower

    return v_RelPow, PowSpec, freqs
