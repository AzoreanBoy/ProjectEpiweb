import pandas as pd
import numpy as np
from scipy import signal


def notch_filter(data, fs, f0, Q):

    # Design notch filter
    b, a = signal.iirnotch(f0, Q, fs)

    # Frequency response
    freqz, h = signal.freqz(b, a, fs=fs)

    # Filter signal
    filtered_signal = signal.filtfilt(b, a, data, axis=0)

    return filtered_signal


def butter_filter(data, type_filter, cutoff, fs, order):
    nyq = 0.5 * fs  # Nyquist Frequency
    normal_cutoff = cutoff / nyq
    # Get the filter coefficients
    b, a = signal.butter(order, normal_cutoff, btype=type_filter, analog=False)
    filtered_signal = signal.filtfilt(b, a, data, axis=0)
    return filtered_signal


def filtering(data, conf):
    sampFreq = conf[-1]

    np_data = np.asarray(data, dtype=np.float32)

    if conf[0] == "lowpass":
        filter_type = 'low'
        cutoffLowPass = conf[1]  # cut-off frequency
        orderLowPass = conf[2]  # order of butterworth filter

        dataFiltered = butter_filter(
            np_data, filter_type, cutoffLowPass, sampFreq, orderLowPass)

    if conf[0] == "highpass":
        filter_type = 'high'
        cutoffHighPass = conf[1]  # cut-off frequency
        orderHighPass = conf[2]  # order of butterworth filter

        dataFiltered = butter_filter(
            np_data, filter_type, cutoffHighPass, sampFreq, orderHighPass)

    if conf[0] == "notch":
        Q = 25.0  # Quality factor
        cutoffNotch = conf[1]  # cut-off frequency

        dataFiltered = notch_filter(np_data, sampFreq, cutoffNotch, Q)

    return dataFiltered
