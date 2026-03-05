import numpy as np
import spectrum as sp


def f_PowSpec(signal, sampleRate: float, ARMethod: int = 0):
    """
    This function computes the power spectrum of the input signal.

    Args:
        - signal: a vector of 1D
        - sampleRate (float): sample rate of the signal in HZ
        - ARMethod (int, optional): Set to 1 to compute the power spectral density via Autoregressive model estimator. Set to 0 to compute via FFT Squared Modulus Estimator. Defaults to 0.

    Returns:
        - v_PowSpec: power spectral density
        - v_Freq: frequency vector
        - totalPower: total power of the signal
    """

    if ARMethod == 0:
        # FFT Squared Modulus
        v_PowSpec = np.fft.fft(signal)
        v_PowSpec = v_PowSpec * np.conj(v_PowSpec)
        v_PowSpec = v_PowSpec.real / sampleRate
        v_Freq = np.arange(0, int(len(v_PowSpec))) * (sampleRate / len(v_PowSpec))
        s_LenHalf = np.floor(len(v_Freq) / 2)
        v_PowSpec = v_PowSpec[: int(s_LenHalf + 1)]
        v_Freq = v_Freq[: int(s_LenHalf + 1)]

    elif ARMethod == 1:
        # Autoregressive model estimator (Burg method)
        AR_order = 10
        if len(signal) < AR_order * 5:
            AR_order = np.round(len(signal) / 5)
        p = sp.pburg(signal, AR_order, NFFT=len(signal), sampling=sampleRate)
        v_PowSpec = p.psd
        v_Freq = p.frequencies()

    totalPower = np.sum(v_PowSpec)

    return np.array(v_PowSpec), np.array(v_Freq), totalPower
