import numpy as np
import pandas as pd
import datetime


class bin_file:

    def __init__(self, filename, headFile_path):

        self.filename = filename
        self.headFile_path = headFile_path
        self.dataFile_path = filename + ".data"

        self.read_head_file(headFile_path)

        durationTs = datetime.timedelta(
            seconds=self.durationInSecs)  # dd HH:MM:SS
        stopTs = self.startTs + durationTs  # yyyy-mm-dd HH:MM:SS

        self.durationTs = durationTs
        self.stopTs = stopTs

    def read_head_file(self, headFile_path):
        ''' Read data from .head file '''

        dataHead = pd.read_table(headFile_path, sep="=", header=None, names=[
            "Index", "Values"], index_col=0)
        dateFormat = '%Y-%m-%d %H:%M:%S.%f'

        startTs = datetime.datetime.strptime(
            dataHead.loc["start_ts", "Values"], dateFormat)
        dataHead.loc["start_ts", "Values"] = startTs

        numSamples = int(dataHead.loc["num_samples", "Values"])
        dataHead.loc["num_samples", "Values"] = numSamples

        sampleFreq = int(dataHead.loc["sample_freq", "Values"])
        dataHead.loc["sample_freq", "Values"] = sampleFreq

        conversionFactor = float(dataHead.loc["conversion_factor", "Values"])
        dataHead.loc["conversion_factor", "Values"] = conversionFactor

        numChannels = int(dataHead.loc["num_channels", "Values"])
        dataHead.loc["num_channels", "Values"] = numChannels

        elecNames = dataHead.loc["elec_names", "Values"][1:-1].split(',')
        dataHead.loc["elec_names", "Values"] = elecNames

        patID = int(dataHead.loc["pat_id", "Values"])
        dataHead.loc["pat_id", "Values"] = patID

        admID = int(dataHead.loc["adm_id", "Values"])
        dataHead.loc["adm_id", "Values"] = admID

        recID = int(dataHead.loc["rec_id", "Values"])
        dataHead.loc["rec_id", "Values"] = recID

        durationInSecs = int(float(dataHead.loc["duration_in_sec", "Values"]))
        dataHead.loc["duration_in_sec", "Values"] = durationInSecs

        # sampleBytes = int(dataHead.loc["sample_bytes", "Values"])
        # dataHead.loc["sample_bytes", "Values"] = sampleBytes

        if "sample_bytes" in dataHead.index:
            sampleBytes = int(dataHead.loc["sample_bytes", "Values"])
        elif "sample_byte" in dataHead.index:
            sampleBytes = int(dataHead.loc["sample_byte", "Values"])
        else:
            raise KeyError("Neither 'sample_bytes' nor 'sample_byte' found in header file.")

        dataHead.loc["sample_bytes", "Values"] = sampleBytes

        self.startTs = startTs
        self.numSamples = numSamples
        self.sampleFreq = sampleFreq
        self.conversionFactor = conversionFactor
        self.numChannels = numChannels
        self.elecNames = elecNames
        self.patID = patID
        self.recID = recID
        self.durationInSecs = durationInSecs
        self.sampleBytes = sampleBytes

        return dataHead

    def read_data_file(self):
        """ Read data from .data file """

        f = open(self.dataFile_path, "rb")

        # Modelar para o caso do sample rate
        if self.sampleBytes == 2:
            rawByteToInt = np.fromfile(f, dtype=np.int16)
        elif self.sampleBytes == 4:
            rawByteToInt = np.fromfile(f, dtype=np.int32)
        elif self.sampleBytes == 8:
            rawByteToInt = np.fromfile(f, dtype=np.int64)

        signalData = rawByteToInt * self.conversionFactor
        signalData = signalData.reshape((self.numChannels, -1), order="F")

        signalData_df = pd.DataFrame(data=signalData.T, columns=self.elecNames)
        # signalData_df = signalData_df.T

        timeRange = pd.date_range(
            start=self.startTs,
            end=self.stopTs,
            periods=int(self.numSamples),
        )
        signalData_df.index = timeRange

        return signalData_df
