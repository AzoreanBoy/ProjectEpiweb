import numpy as np


def inst_energy(data):

    # squared values
    square_values = np.square(data)
    return square_values


def average_energy(data, window_size, step):

    # instantaneous energy (squared values of EEG)
    inst_values = inst_energy(data)

    avg_energy_values = []
    i = 0
    while i + window_size <= inst_values.shape[0]:
        begin_window = i
        end_window = begin_window + window_size

        window_inst_values = inst_values[begin_window:end_window, :]

        i = i + step

        # average energy
        avg_ener = np.sum(window_inst_values, axis=0) / \
            window_inst_values.shape[0]

        # average energy list
        avg_energy_values.append(avg_ener)

    avg_energy_values = np.array(avg_energy_values)

    return avg_energy_values


def accumulated_energy(data, window_avg, step, accu_energy_list):

    # average energy values (Ea)
    avg_energy_values = average_energy(data, window_avg, step)

    # average energy
    avg_energy = np.sum(avg_energy_values, axis=0)/avg_energy_values.shape[0]

    # accumulated energy
    if len(accu_energy_list) == 0:
        accu_energy = avg_energy

    else:
        # last value of the list
        previous_accu_energy_values = accu_energy_list[-1]
        accu_energy = avg_energy + previous_accu_energy_values

    return accu_energy
