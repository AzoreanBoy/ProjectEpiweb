import numpy as np
from .utils.f_RelPow import f_RelPow


def get_RelPow(
    signal: np.ndarray, fs: float, freqRanges: np.ndarray, ARmethod: int = 0
):
    """
    "Calculate the relative power of a signal in different frequency bands.

    Args:
        - signal (np.ndarray): input signal with MxN matrix where M is the number of samples and N is the number of channels
        - fs (float): sample rate in Hz
        - freqRanges (np.ndarray): nx2 matrix containing the frequency ranges to compute the relative power. Each row contains the start and end frequencies of the range. n is the number of frequency bands.
        - ARmethod (int, optional): set to 1 to compute the power spectral density via an AR (Autoregressive) method. Defaults to 0 (FFT Squared Modulus Estimator).

    Returns:
        - relPow (np.ndarray): relative power of the signal in each frequency band
        - PowSpec (np.ndarray): power spectral density of the signal from 0 to fs/2
        - freqs (np.ndarray): center frequencies of the frequency bands
    """
    # Check if the input signal is a 1D array
    channels = signal.shape[1] if len(signal.shape) > 1 else 1

    # Initialize the relative power matrix
    relPow = np.zeros((channels, freqRanges.shape[0]))
    # PowSpecMatrix = np.zeros((channels, int(fs//2 + 1)))

    for channel in range(channels):
        v_RelPow, PowSpec, freqs = f_RelPow(
            signal[:, channel], fs, freqRanges, ARmethod
        )
        relPow[channel, :] = v_RelPow
        # PowSpecMatrix[channel, :] = PowSpec

    # return relPow, PowSpecMatrix, freqs
    return relPow
