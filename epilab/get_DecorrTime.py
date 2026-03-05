import numpy as np


def get_DecorrTime(signal, samplerate=1):
    """
    Calculate the decorrelation time of a signal.

    Parameters:
    - signal: Signal to calculate the decorrelation time where signal is a matrix of size N x M where N is the number of samples and M is the number of channels.
    - sampleRate: Sampling rate of the signal in Hz. Default value is 1.

    Returns:
    - decorrTime: Decorrelation time of the signal.

    This function calculates the decorrelation time of a signal using the
    autocorrelation function. The decorrelation time is the time at which the
    autocorrelation function falls to 1/e of its initial value.

    """
    try:
        numChannels = signal.shape[1]
        decorrTime = np.zeros(numChannels)

        for i in range(numChannels):
            s_DecorrTime = np.correlate(signal[:, i], signal[:, i], mode="full")
            s_DecorrTime = s_DecorrTime[len(signal[:, i]) - 1 :]

            # Normalizing the correlation to get unbiased result
            norm_factor = np.arange(len(signal[:, i]), 0, -1)
            s_DecorrTime = s_DecorrTime / norm_factor

            idx = np.where(s_DecorrTime < 0)[0]
            if len(idx) > 0:
                decorrTime[i] = idx[0] - 1 / samplerate
            else:
                decorrTime[i] = -1
    except:
        numChannels = 1
        s_DecorrTime = np.correlate(signal, signal, mode="full")
        s_DecorrTime = s_DecorrTime[len(signal) - 1 :]

        # Normalizing the correlation to get unbiased result
        norm_factor = np.arange(len(signal), 0, -1)
        s_DecorrTime = s_DecorrTime / norm_factor

        # Zero Crossing
        idx = np.where(s_DecorrTime < 0)[0]
        if len(idx) > 0:
            decorrTime = (idx[0] - 1) / samplerate
        else:
            decorrTime = -1

    return decorrTime
