import numpy as np
import matplotlib.pyplot as plt
import scipy.signal


def obtain_PSD(data, fs):

    f_values, psd_values = scipy.signal.welch(
        data, fs, window='hann', scaling='spectrum', nperseg=fs, noverlap=0.5, axis=0)

    return f_values, psd_values


def figure_PSD(f_values, psd_values, signal_number):

    fig, ax = plt.subplots()
    ax.plot(f_values, psd_values[signal_number])
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('PSD [V^2/Hz]')
    ax.set_title('Spectrum of the signal')
    plt.show()


def relative_power(freq_band, f_values, psd_values):

    band_powers = psd_values[(
        (f_values >= freq_band[0]) & (f_values < freq_band[1])), :]
    band_power = scipy.integrate.simps(band_powers, axis=0)

    total_power = scipy.integrate.simps(psd_values, axis=0)

    rsp = band_power/total_power

    return rsp


def spectral_edge_freq_power(percentage, psd_values, f_values):

    # Total power
    total_power = np.sum(psd_values, axis=0)

    # Spectral edge power (SEP)
    sep = percentage/100 * total_power

    # Spectral edge frequency (SEF)
    cumsum_values = np.cumsum(psd_values, axis=0)

    # Save last idx where cumsum_value < sep value
    idx_sef = [np.where(cumsum_values[i] < sep[i])[0][-1]
               for i in range(len(sep))]
    sef = f_values[idx_sef]

    return sep, sef
