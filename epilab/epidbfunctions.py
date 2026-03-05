from django.db.models import QuerySet
from django.db.models import F
from django.db.models.functions import Coalesce

from app.models import *
from epilab.binfile import bin_file
from epilab.file_processing import process_files
from epilab import *

from celery import shared_task

import paramiko
import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()


class ServerConnection:
    ssh = None
    sftp_client = None

    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(
            hostname=os.getenv('EPIDB_HOSTNAME'),
            username=os.getenv('EPIDB_USERNAME'),
            password=os.getenv('EPIDB_PASSWORD')
        )
        self.sftp_client = self.ssh.open_sftp()
        self.sftp_client.MAX_REQUEST_SIZE = 65536

    def connect(self):
        return self.sftp_client

    def close(self):
        self.sftp_client.close()
        self.ssh.close()
        return None


def get_admission_files(admid: int) -> QuerySet:
    """
    Get all files associated with an Admission
    :param admid: ID
    :return: QuerySet with all files
    """
    adm = Admission.objects.get(id=admid)
    recordings = Recording.objects.filter(admission=adm)
    blocks = Block.objects.filter(recording__in=recordings)
    filesid = blocks.values_list('eeg_file', flat=True).distinct()
    files = Files.objects.filter(id__in=filesid)
    return files


def get_channels_list(admission_id: int) -> list:
    """
    Get all channels associated with an Admission
    :param admission_id: ID
    :return: list with all channels
    """
    # print("-" * 30 + "\nGETTING CHANNELS LIST\n" + "-" * 30)
    # GET ALL FILES FROM ADMISSION
    files = get_admission_files(admission_id)

    # RECORDING PATHS FROM FILES
    recording_paths = files.values_list('path', flat=True).distinct()

    # ADD /dados TO PATHS (SERVER PATH)
    recording_paths = ['/dados' + recpath for recpath in recording_paths]
    recording_paths = [recpath if recpath[-1] == '/' else recpath + '/' for recpath in recording_paths]

    # CREATE TMP FOLDER
    tmp_folder = os.path.join(os.getcwd(), 'data', 'epidb', 'tmpfiles')
    os.makedirs(tmp_folder, exist_ok=True)
    # MAKING SURE THE FOLDER IS EMPTY
    for file in os.listdir(tmp_folder):
        os.remove(os.path.join(tmp_folder, file))

    # CONNECT TO SERVER VIA SSH
    sftp_client = ServerConnection().connect()

    # GET 1 HEAD FILE FROM EACH RECORDING PATH
    for recpath in recording_paths:
        firstfile = None
        for filename in sftp_client.listdir(recpath):
            if filename.endswith('.head') and sftp_client.stat(recpath + filename).st_size != 0:
                firstfile = filename
                break
        originfile = recpath + firstfile
        destfile = os.path.join(tmp_folder, firstfile)

        try:
            sftp_client.get(originfile, destfile)
        except FileNotFoundError:
            print("File not found: " + originfile)

    # TRANSFORM FILES INTO BIN FILES
    files = []
    for file in os.listdir(tmp_folder):
        try:
            files.append(bin_file(tmp_folder + '\\' + file[:-5], tmp_folder + '\\' + file))
        except Exception as e:
            print("Error: " + str(e))

    # CHECK IF CHANNELS ARE THE SAME
    if len(files) == 0:
        channels = []
    else:
        # Initialize the channels with the channels of the first file
        channels = files[0].elecNames

        # Create a set of common channels starting with the channels from the first file
        common_channels = set(channels)

        # Intersect with the channels of the remaining files
        for file in files[1:]:
            common_channels.intersection_update(file.elecNames)

        channels = [ch for ch in channels if ch in common_channels]

    # CLOSE CONNECTION
    sftp_client.close()

    # DELETE TMP FOLDER CONTENT
    for file in os.listdir(tmp_folder):
        os.remove(os.path.join(tmp_folder, file))

    return channels


def download_all_files_from_admission(adm_id: int):
    """
    Download all files from an Admission
    :return: None
    """
    # GET ALL FILES FROM ADMISSION
    files = get_admission_files(adm_id)
    paths = files.values_list('path', flat=True).distinct()
    recording_paths = ['/dados' + recpath for recpath in paths]
    recording_paths = [recpath if recpath[-1] == '/' else recpath + '/' for recpath in recording_paths]

    # parent_path = os.path.dirname(recording_paths[0].rstrip('/'))

    # CREATE DESTINATION FOLDER
    prefix = '/dados/eeg/'
    folders = recording_paths[0][len(prefix):].split('/')

    dest_folder = os.path.join(os.getcwd(), 'data', 'epidb', folders[0], folders[1])
    print(dest_folder)
    os.makedirs(dest_folder, exist_ok=True)

    # CONNECT TO SERVER VIA SSH
    sftp_client = ServerConnection().connect()

    # DOWNLOAD FILES
    for recpath in recording_paths:
        # Create folder for each recording
        recordin_folder = recpath[len(prefix):].rstrip('/').split('/')[-1]
        os.makedirs(os.path.join(dest_folder, recordin_folder), exist_ok=True)

        print(f"Downloading files from {recpath}")
        # Get all files from the recording
        files = sftp_client.listdir(recpath)
        # print(files)

        # Download all files from the recording
        for file in files:
            if file.endswith('.head'):
                headfile = file
                datafile = file[:-5] + '.data'

                if datafile in files:
                    # CHECK IF FILES ARE EMPTY
                    headfile_size = sftp_client.stat(recpath + headfile).st_size
                    datafile_size = sftp_client.stat(recpath + datafile).st_size

                    if headfile_size > 0 and datafile_size > 0:
                        # DOWNLOAD HEAD AND DATA FILES IF THEY ARE NOT EMPTY
                        sftp_client.get(recpath + headfile, os.path.join(dest_folder, recordin_folder, headfile))
                        sftp_client.get(recpath + datafile, os.path.join(dest_folder, recordin_folder, datafile))
                    else:
                        print(f"One or both Files are empty with name {headfile[:-5]}")
                else:
                    print(f"Data file not found for {headfile}")

    print("\nFiles downloaded to: " + dest_folder + "\n")
    return None


def try_files_not_found(files):
    """
    Try to download files that were not found
    """
    remote_files = ['/dados/eeg/' + file[:-5] for file in files]
    sftp_client = ServerConnection().connect()
    for file in remote_files:
        dest = os.path.join(os.getcwd(), 'data', 'epidb', file[len('/dados/eeg/'):])
        try:
            headfile = file + '.head'
            datafile = file + '.data'

            # CHECK IF FILES ARE EMPTY
            headfile_size = sftp_client.stat(headfile).st_size
            datafile_size = sftp_client.stat(datafile).st_size

            if headfile_size > 0 and datafile_size > 0:
                sftp_client.get(headfile, dest + '.head')
                sftp_client.get(datafile, dest + '.data')
        except Exception:
            print(f"Error downloading file {file}. Empty head file or empty data file.")
    return None


@shared_task(name='extract_epidb_features')
def extract_epidb_features(
        userid,
        adm_id: int,
        sampFreq: int,
        channels: list[str],
        filter,
        filteroptions,
        window,
        step,
        features,
        featsoptions,
        model_dir,
        studyid,
        SPH,
        SOP,
):
    """
    Extract features from an Admission of EPIDB
    :param adm_id: Admission ID
    :return: None
    """
    study = Study.objects.get(pk=studyid)
    study.completed = False
    study.save()

    # EXTRACTION STUDY
    new_extraction = Extraction(
            study=study,
            channels=channels,
            filter=filter,
            windowsize=window,
            windowstep=step,
            feats=features,
            featsoptions=featsoptions,
            SPH=int(SPH),
            SOP=int(SOP),
    )
    # FILTER OPTIONS
    if filter != "none":
        new_extraction.filter_cutoff = filteroptions[0]
        new_extraction.filter_order = filteroptions[1]
    new_extraction.save()
    # FEATURES LIST
    for feat in features:
        feature = Feature.objects.get(name=feat)
        new_extraction.features.add(feature)
    # CHANNELS
    for ch in channels:
        try:  # CHECK IF CHANNEL EXISTS IN DATABASE AND ADD IT TO THE EXTRACTION
            channel = Channel.objects.get(val=ch)
            new_extraction.channs.add(channel)
        except Channel.DoesNotExist:  # IF CHANNEL DOES NOT EXIST, CREATE IT AND ADD IT TO THE EXTRACTION
            new_channel = Channel(val=ch)
            new_channel.save()
            new_extraction.channs.add(new_channel)

    # GET ALL FILES FROM ADMISSION
    files = get_admission_files(adm_id)
    print(f"Files: {files.count()}")
    files = files.values_list('path', 'name')
    new_files = []
    for path, name in files:
        if path[-1] != '/':
            path += '/'
        new_files.append(path + name)
    files = new_files
    del new_files

    # CREATE DESTINATION FOLDER
    prefix = '/eeg/'
    folders = files[0][len(prefix):].split('/')
    files = [file[len(prefix):] for file in files]
    dest_folder = os.path.join(os.getcwd(), 'data', 'epidb', folders[0], folders[1])

    # CHECK IF DESTINATION FOLDER EXISTS
    if not os.path.exists(dest_folder):
        # IF FOLDER DOEST NOT EXIST, CREATE IT AND DOWNLOAD FILES
        os.makedirs(dest_folder, exist_ok=True)
        download_all_files_from_admission(adm_id)
    else:
        # IF FOLDER EXISTS, CHECK IF FILES ARE IN THE FOLDER
        files_not_found = []
        print("Checking if files are in disk!")
        for file in files:
            if not os.path.exists(os.path.join(os.getcwd(), 'data', 'epidb', file)):
                files_not_found.append(file)

        # IF FILES ARE NOT FOUND, TRY DOWNLOAD THEM
        if len(files_not_found) > 0:
            print(f"There are {len(files_not_found)} files not found in disk! Trying to download them!")
            try_files_not_found(files_not_found)

        # FREE MEMORY
        del files_not_found

    del folders, prefix, files, path, name  # FREE MEMORY

    # BIN FILES
    binfiles = []
    for dir in os.listdir(dest_folder):
        for file in os.listdir(os.path.join(dest_folder, dir)):
            if file.endswith('.head'):
                filename = os.path.join(dest_folder, dir, file[:-5])
                headfile_path = os.path.join(dest_folder, dir, file)
                binfiles.append(bin_file(filename, headfile_path))

    del dir, dest_folder, headfile_path, filename, file  # FREE MEMORY

    features_array = []
    features2d_array = None
    columnsNames = []
    sublegend_array = []
    timevector = []
    # Lists of features (only computing the chosen ones)
    for feature_idx, feature in enumerate(features):
        print("\n" + "-" * 50 + f"\nComputing feature {feature}" + "\n" + "-" * 50 + "\n")

        # ---------------------------------------------
        #               DATA PROCESSING
        # ---------------------------------------------
        datasets = process_files(binfiles, window)
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
    target = get_target_labels(adm_id, timevector, int(SPH), int(SOP))
    print(f"Features array shape: {features_array.shape}")
    print(f"Features2D array shape: {features2d_array.shape}")
    print(f"Target shape: {target.shape}")
    print(f"Timevector shape: {len(timevector)}")

    # SAVE
    np.savez(
            model_dir,
            data=features_array,
            timevector=timevector,
            target=target,
            data2d=features2d_array,
            columns=columnsNames,
            allow_pickle=False,
    )

    new_notification = Notification(
            consumed=False,
            description=f"Feature Extraction for EPIDB Admission {adm_id} completed.",
            study=study,
            user=User.objects.get(id=userid),
    )
    new_notification.save()

    study.completed = True
    study.save()

    return None


def get_target_labels(admission, timevector, SPH, SOP):
    """
    Function to compute the target labels for the EEG recordings of an Admission from EPIDB database
    :param admission: admission id from the EPIDB database
    :param timevector: vector with the timestamps of the EEG recordings
    :param SPH: time in minutes for the SPH interval
    :param SOP: time in minutes for the SOP interval
    :return: np.array with the target labels for the EEG recordings (1 if the EEG recording is in the SOP interval, 2 if it is in the SPH interval, 3 if it is in the seizure interval, 0 otherwise)
    """
    adm = Admission.objects.get(id=admission)
    recordings = Recording.objects.filter(admission=adm)
    seizures = Seizure.objects.filter(recording__in=recordings)

    annotated_seizures = seizures.annotate(
            onset=Coalesce(F('eeg_onset'), F('clin_onset'), F('first_eeg_change'), F('first_clin_sign')),
            offset=Coalesce(F('eeg_offset'), F('clin_offset'))
    ).order_by('onset')

    onsets = annotated_seizures.values_list('onset', flat=True)
    offsets = annotated_seizures.values_list('offset', flat=True)

    df = pd.DataFrame({'onset': onsets, 'offset': offsets})
    df = df.dropna()
    onsets = df['onset']
    offsets = df['offset']

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
