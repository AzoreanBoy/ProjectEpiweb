import sys
import pandas as pd
import numpy as np
import pickle
import ast
import traceback

from app.models import *
from epilab import *
from epilab.file_processing import process_files
from epilab.binfile import bin_file

from joblib import Parallel, delayed

decomposition_level = 0


def getSubFeatLegend(decomposition_level):
    subfeats_legend = {
        "Statistic": ["Mean", "Variance", "Skewness", "Kurtosis"],
        "RelPow": ["Delta", "Theta", "Alpha", "Beta", "Gamma"],
        "Hjorth": ["Mobility", "Complexity"],
        "WaveletCoefficient": [
            "db{}".format(i) for i in range(1, decomposition_level + 1)
        ],
        "Energy": ["energy"],
        "ARModCoeff": ["ARModCoeff"],
        "DecorrTime": ["DecorrTime"],
        "SpectreEdge": ["SEF", "EdgePower"],
    }
    return subfeats_legend


def extractFeatures(
        patient,
        sampFreq,
        channels,
        filter,
        filteroptions,
        window,
        step,
        features,
        featsoptions,
        dir,
        SPH,
        SOP,
        operationflag="default",
):
    global decomposition_level
    # Load data and labels
    files = Information.objects.filter(patient=patient).order_by("startts")
    binfiles = [bin_file(file.headfile.path[:-5], file.headfile.path) for file in files]

    del files  # Free memory

    features_array = []
    features2d_array = None
    columnsNames = []
    sublegend_array = []
    timevector = []
    # Lists of features (only computing the chosen ones)
    for feature_idx, feature in enumerate(features):
        print("\n" + "-" * 50 + f"\nComputing feature {feature}" + "\n" + "-" * 50 + "\n")

        # ---------------------------------------------
        #               DATA PREPARATION
        # ---------------------------------------------
        datasets = process_files(
                binfiles[106:141], # TODO: Remove this slice for the final version
                window)
        datasets = (dataset[channels] for dataset in datasets)

        # ---------------------------------------------
        #               FEATURE INITIALIZATION
        # ---------------------------------------------

        if "Statistic" in feature:
            mean_list = []
            variance_list = []
            skewness_list = []
            kurtosis_list = []

        if "RelPow" in feature:
            rsp_delta_list = []
            rsp_theta_list = []
            rsp_alpha_list = []
            rsp_beta_list = []
            rsp_gamma_list = []

            # Frequency Bands
            freqRange = np.array(
                [
                    [0.1, 4],  # Delta band (< 4Hz)
                    [4, 8],  # Theta band (4-8Hz)
                    [8, 15],  # Alpha band (8-15Hz)
                    [15, 30],  # Beta band (15-30Hz)
                    [30, np.ceil(float(sampFreq) / 2)],  # Gamma band (> 30 Hz)
                ]
            )

            RP_ARMethod = int(featsoptions["RelPowARMethod"])

        if "Hjorth" in feature:
            mobility_list = []
            complexity_list = []

        if "WaveletCoefficient" in feature:
            decomposition_level = int(featsoptions["WaveletCoefficientLevel"])
            energy_d_list = [[] for i in range(decomposition_level)]

        if "Energy" in feature:
            accu_energy_list = []

        if "ARModCoeff" in feature:  # TODO: Implement AR Model Coefficients feature
            # Initialize lists for AR model coefficients
            armod_coeffs = []

            # Variables for AR model coefficients
            armod_order = featsoptions["ARModCoeffOrder"]
            armod_order = int(armod_order)
            armod_method = int(featsoptions["ARModCoeffMethod"])

        if "DecorrTime" in feature:
            # Initialize lists for Decorrelation Time function results
            decorr_times = []

        if "SpectreEdge" in feature:
            # Initialize lists for Spectre Edge function results
            SEF_list = []
            EdgePower_list = []

            # Variables for Spectre Edge function
            SE_freqRef = float(featsoptions["SpectreEdgeFreqRef"])
            SE_percentage = float(featsoptions["SpectreEdgePercentage"])
            SE_minFreq = float(featsoptions["SpectreEdgeMinFreq"])
            SE_ARMethod = int(featsoptions["SpectreEdgeARMethod"])

        # ---------------------------------------------
        #               FEATURE EXTRACTION
        # ---------------------------------------------
        for idx, data_df in enumerate(datasets):
            print(f"Processing dataset {idx + 1}")

            if filter != "none":
                print("\n" + "-" * 50 + f"\nFiltering data\n" + "-" * 50 + "\n")
                if filter == "lowpass":
                    conf = ["lowpass", float(filteroptions[0]), float(filteroptions[1]), float(sampFreq)]
                elif filter == "highpass":
                    conf = ["highpass", float(filteroptions[0]), float(filteroptions[1]), float(sampFreq)]
                elif filter == "notch":
                    conf = ["notch", float(filteroptions[0]), float(sampFreq)]

                data_df = pd.DataFrame(filters.filtering(data_df, conf), columns=data_df.columns, index=data_df.index)

            begin_window = data_df.index[0]
            while begin_window < data_df.index[-1]:
                # DEFINE THE BEGINING AND END OF THE WINDOW
                end_window = begin_window + pd.Timedelta(seconds=window)
                if end_window > data_df.index[-1]:
                    end_window = data_df.index[-1]

                # VERIFY IF THE END OF THE WINDOW IS A VALID INDEX
                try:
                    end_window = data_df.index[data_df.index <= end_window][-1]
                except IndexError:
                    print("Not nearest index found")
                    break
                # GET THE DATA FOR THE WINDOW
                window_values = data_df.loc[begin_window:end_window].to_numpy()

                # SAVE THE TIME VECTOR
                if feature_idx == 0:
                    timevector.append(begin_window)

                # -------- STATISTICAL MOMENTS --------
                if "Statistic" in feature:
                    mean, variance, skewness, kurt = get_stats.statistical_moments(
                        window_values
                    )
                    
                    mean_list.append(mean)
                    variance_list.append(variance)
                    skewness_list.append(skewness)
                    kurtosis_list.append(kurt)

                # -------- RELATIVE POWER --------
                if "RelPow" in feature:
                    relPow = get_RelPow.get_RelPow(
                        window_values, float(sampFreq), freqRange, RP_ARMethod
                    )

                    # Relative powers
                    rsp_delta_list.append(relPow[:, 0])
                    rsp_theta_list.append(relPow[:, 1])
                    rsp_alpha_list.append(relPow[:, 2])
                    rsp_beta_list.append(relPow[:, 3])
                    rsp_gamma_list.append(relPow[:, 4])

                # -------- HJORTH PARAMETERS --------
                if "Hjorth" in feature:
                    mobility, complexity = get_hjorth.hjorth_parameters(window_values)

                    mobility_list.append(mobility)
                    complexity_list.append(complexity)

                # -------- WAVELET COEFFICIENTS --------
                if "WaveletCoefficient" in feature:
                    # TODO: Implement Wavellets Features Algorithm
                    mother_wavelet = "db4"
                    # Decomposition level
                    e = []
                    for values in window_values.T:
                        energies = get_wavelet.coefficients_energy(
                            values, mother_wavelet, decomposition_level
                        )
                        e.append(energies)

                    e = list(map(list, zip(*e)))
                    for i in range(len(energy_d_list)):
                        energy_d_list[i].append(e[i])

                # -------- ENERGY --------
                if "Energy" in feature:
                    energy = np.sum(np.square(window_values), axis=0)
                    accu_energy_list.append(energy)

                    del energy

                # ------ Decorrelation Time --------------
                if "DecorrTime" in feature:
                    decorr_time = get_DecorrTime.get_DecorrTime(
                        window_values, float(sampFreq)
                    )
                    decorr_times.append(decorr_time)

                # ------ Spectre Edge --------------
                if "SpectreEdge" in feature:
                    SEF, EdgePower = get_SpecEdgeFreq.f_SpecEdgeFreq(
                        window_values,
                        float(sampFreq),
                        freqRef=SE_freqRef,
                        percentage=SE_percentage,
                        minFreq=SE_minFreq,
                        ARMethod=SE_ARMethod,
                    )
                    SEF_list.append(SEF)
                    EdgePower_list.append(EdgePower)

                # UPDATE THE BEGINING OF THE WINDOW FOR THE NEXT ITERATION
                begin_window = begin_window + pd.Timedelta(seconds=step)
                try:
                    begin_window = data_df.index[data_df.index <= begin_window][-1]
                except IndexError:
                    print("Not nearest index found")
                    break
                if end_window == data_df.index[-1]:
                    break

        # ---------------------------------------------
        #               POST PROCESSING
        # ---------------------------------------------

        # Convert to arrays (num of channels x num of windows)
        if "Statistic" in feature:
            mean_arr = np.array(mean_list)
            variance_arr = np.array(variance_list)
            skewness_arr = np.array(skewness_list)
            kurtosis_arr = np.array(kurtosis_list)
            mean_arr[np.isnan(mean_arr)] = 0
            variance_arr[np.isnan(variance_arr)] = 0
            skewness_arr[np.isnan(skewness_arr)] = 0
            kurtosis_arr[np.isnan(kurtosis_arr)] = 0

            stat_arr = np.stack(
                [
                    np.transpose(mean_arr),
                    np.transpose(variance_arr),
                    np.transpose(skewness_arr),
                    np.transpose(kurtosis_arr),
                ]
            )
            features_array.append(stat_arr)
            sublegend_array.append(["Mean", "Variance", "Skewness", "Kurtosis"])

            temp_data = np.hstack([mean_arr, variance_arr, skewness_arr, kurtosis_arr])
            for stat in ["Mean", "Variance", "Skewness", "Kurtosis"]:
                for channel in channels:
                    columnsNames.append(f"{channel}_{stat}")

        if "RelPow" in feature:
            rsp_delta_arr = np.array(rsp_delta_list)
            rsp_theta_arr = np.array(rsp_theta_list)
            rsp_alpha_arr = np.array(rsp_alpha_list)
            rsp_beta_arr = np.array(rsp_beta_list)
            rsp_gamma_arr = np.array(rsp_gamma_list)

            rsp_delta_arr[np.isnan(rsp_delta_arr)] = 0
            rsp_theta_arr[np.isnan(rsp_theta_arr)] = 0
            rsp_alpha_arr[np.isnan(rsp_alpha_arr)] = 0
            rsp_beta_arr[np.isnan(rsp_beta_arr)] = 0
            rsp_gamma_arr[np.isnan(rsp_gamma_arr)] = 0

            rsp_arr = np.stack(
                [
                    np.transpose(rsp_delta_arr),
                    np.transpose(rsp_theta_arr),
                    np.transpose(rsp_alpha_arr),
                    np.transpose(rsp_beta_arr),
                    np.transpose(rsp_gamma_arr),
                ]
            )
            features_array.append(rsp_arr)
            sublegend_array.append(["delta", "theta", "alpha", "beta", "gamma"])

            temp_data = np.hstack([rsp_delta_arr, rsp_theta_arr, rsp_alpha_arr, rsp_beta_arr, rsp_gamma_arr])
            for band in ["Delta", "Theta", "Alpha", "Beta", "Gamma"]:
                for channel in channels:
                    columnsNames.append(f"{channel}_{band}")

        if "Hjorth" in feature:
            mobility_arr = np.array(mobility_list)
            complexity_arr = np.array(complexity_list)
            mobility_arr[np.isnan(mobility_arr)] = 0
            complexity_arr[np.isnan(complexity_arr)] = 0

            hjorth_arr = np.stack(
                [np.transpose(mobility_arr), np.transpose(complexity_arr)]
            )
            features_array.append(hjorth_arr)
            sublegend_array.append(["mobility", "complexity"])

            temp_data = np.hstack([mobility_arr, complexity_arr])
            for hjorth in ["Mobility", "Complexity"]:
                for channel in channels:
                    columnsNames.append(f"{channel}_{hjorth}")

        if "WaveletCoefficient" in feature:
            energy_arr = np.array([np.transpose(i) for i in energy_d_list])
            energy_arr[np.isnan(energy_arr)] = 0

            features_array.append(energy_arr)
            sublegend_array.append(
                ["db{}".format(i) for i in range(1, decomposition_level + 1)]
            )

        if "Energy" in feature:
            accu_energy_arr = np.array(accu_energy_list)
            accu_energy_arr[np.isnan(accu_energy_arr)] = 0

            energy_arr = np.stack([np.transpose(accu_energy_arr)])
            features_array.append(energy_arr)
            sublegend_array.append(["energy"])

            temp_data = np.hstack([accu_energy_arr])
            for energy in ["Energy"]:
                for channel in channels:
                    columnsNames.append(f"{channel}_{energy}")

            del accu_energy_arr, energy_arr

        if "DecorrTime" in feature:
            decorr_times_arr = np.array(decorr_times)

            temp_data = np.hstack([decorr_times_arr])

            decorr_times_arr = np.stack([np.transpose(decorr_times_arr)])
            features_array.append(decorr_times_arr)
            sublegend_array.append(["DecorrTime"])

            for decorr in ["DecorrTime"]:
                for channel in channels:
                    columnsNames.append(f"{channel}_{decorr}")

        if "SpectreEdge" in feature:
            SEF_arr = np.array(SEF_list)
            EdgePower_arr = np.array(EdgePower_list)

            spectral_edge_arr = np.stack(
                [np.transpose(SEF_arr), np.transpose(EdgePower_arr)]
            )

            features_array.append(spectral_edge_arr)
            sublegend_array.append(["SEF", "EdgePower"])

            temp_data = np.hstack([SEF_arr, EdgePower_arr])
            for edge in ["SEF", "EdgePower"]:
                for channel in channels:
                    columnsNames.append(f"{channel}_{edge}")

        # ---------------------------------------------
        if features2d_array is None:
            features2d_array = temp_data
        else:
            features2d_array = np.hstack([features2d_array, temp_data])

    features_array = np.array(features_array, dtype=object)
    target = get_target_labels(patient, timevector, int(SPH), int(SOP))
    print(f"Features array shape: {features_array.shape}")
    print(f"Features2d array shape: {features2d_array.shape}")
    print(f"Target shape: {target.shape}")
    print(f"Timevector shape: {len(timevector)}")

    if "FEATURES" in operationflag:
        tmp = []
        features_array_old = np.load(dir + ".npy", allow_pickle=True)
        for i in features_array_old:
            tmp.append(i)
        for i in features_array:
            tmp.append(i)
        np.save(dir, np.array(tmp, dtype=object), allow_pickle=True)
    elif "CHANNELS" in operationflag:
        features_array_old = np.load(dir + ".npy", allow_pickle=True)
        tmp = []
        for i in range(len(features_array_old)):
            tmp.append(
                np.concatenate([features_array_old[i], features_array[i]], axis=1)
            )
        np.save(dir, np.array(tmp, dtype=object), allow_pickle=True)
    else:
        np.savez(
            dir,
            data=features_array,
            timevector=timevector,
            target=target,
            data2d=features2d_array,
            columns=columnsNames,
            allow_pickle=False,
        )

    return getSubFeatLegend(decomposition_level)


def get_target_labels(patient: Patient, timevector, SPH: int, SOP: int) -> np.array:
    """
    Function to compute the target labels for the EEG recordings
    :param patient: Patient object
    :param timevector: vector with the timestamps of the EEG recordings
    :param SPH: time in minutes for the SPH interval
    :param SOP: time in minutes for the SOP interval
    :return: np.array with the target labels for the EEG recordings (1 if the EEG recording is in the SOP interval, 2 if in the SPH interval, 3 if in the seizure interval, 0 otherwise)
    """
    # GET THE ONSETS OF THE EEG RECORDINGS
    onsets = Event.objects.values_list('eeg_onset', flat=True).filter(patient=patient)
    onsets = pd.Series([pd.to_datetime(onset) for onset in onsets])

    offsets = Event.objects.values_list('eeg_offset', flat=True).filter(patient=patient)
    offsets = pd.Series([pd.to_datetime(offset) for offset in offsets])

    # COMPUTET THE START OF THE PRE-SPH AND PRE-SOP
    sph_times = onsets - pd.Timedelta(minutes=SPH)
    sop_times = sph_times - pd.Timedelta(minutes=SOP)

    # COMPUTE THE TARGET LABELS
    target = []
    for tempo in timevector:
        found = False
        for idx in range(len(sph_times)):
            if sop_times[idx] <= tempo < sph_times[idx]:
                target.append(1)
                found = True
                break
            if sph_times[idx] <= tempo < onsets[idx]:
                target.append(2)
                found = True
                break
            if onsets[idx] <= tempo <= offsets[idx]:
                target.append(3)
                found = True
                break
        if not found:
            target.append(0)

    target = np.array(target)
    return target