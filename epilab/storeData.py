from app.models import *
from epilab.binfile import *

from pathlib import Path
import datetime


def handle_uploaded_file(f):
    if 'evts' in f.name:
        with open('data/events/'+f.name, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
    else:
        with open('data/raw/tmp/'+f.name, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)


def storeInformation(f, user):
    file = bin_file(f.name[:-5], f)
    patient, created = Patient.objects.get_or_create(
        idpat=file.patID, idrecord=file.recID, user=user)
    info, created = Information.objects.get_or_create(
        patient=patient,
        filename=file.filename,
        startts=file.startTs,
        stopts=file.stopTs,
        durationts=file.durationTs,
        nsamples=file.numSamples,
        sampfreq=file.sampleFreq,
        conversionfactor=file.conversionFactor,
        nchannels=file.numChannels,
        elecnames=file.elecNames,
        sampbytes=file.sampleBytes
    )
    if created:
        info.headfile = f
        info.save()
    return created


def storeEvent(file):
    handle_uploaded_file(file)
    events = read_evts_file(file)
    patient, created = Patient.objects.get_or_create(idpat=file.name[:-5])
    for index, row in events.iterrows():
        new_event = Event(
            type=events.at[index, 'evt_type'],
            eeg_onset=events.at[index, 'eeg_onset'],
            eeg_onset_sec=events.at[index, 'eeg_onset_sec'],
            clin_onset=events.at[index, 'clin_onset'],
            clin_onset_sec=events.at[index, 'clin_onset_sec'],
            eeg_offset=events.at[index, 'eeg_offset'],
            eeg_offset_sec=events.at[index, 'eeg_offset_sec'],
            clin_offset=events.at[index, 'clin_offset'],
            clin_offset_sec=events.at[index, 'clin_offset_sec'],
            pattern=events.at[index, 'pattern'],
            classification=events.at[index, 'classification'],
            vigilance=events.at[index, 'vigilance'],
            medicament=events.at[index, 'medicament'],
            dosage=events.at[index, 'dosage'],
            asystoly=events.at[index, 'asystoly'],
            bradycardia=events.at[index, 'bradycardia'],
            tachycardia=events.at[index, 'tachycardia'],
            extrasystoles=events.at[index, 'extrasystoles'],
            patient=patient,
        )
        if not Event.objects.filter(patient=patient).filter(eeg_onset=events.at[index, 'eeg_onset']):
            new_event.save()


def read_evts_file(f):
    evtsFile_path = open('data/events/'+f.name, "rb")
    dataEvts = pd.read_table(evtsFile_path, index_col=False)
    dateFormat = '%Y-%m-%d %H:%M:%S.%f'

    for index, row in dataEvts.iterrows():
        dataEvts.at[index, 'eeg_onset'] = datetime.datetime.strptime(
            row["eeg_onset"], dateFormat)
        dataEvts.at[index, 'clin_onset'] = datetime.datetime.strptime(
            row["clin_onset"], dateFormat)
        dataEvts.at[index, 'eeg_offset'] = datetime.datetime.strptime(
            row["eeg_offset"], dateFormat)
        dataEvts.at[index, 'clin_offset'] = datetime.datetime.strptime(
            row["clin_offset"], dateFormat)
        dataEvts.at[index, 'eeg_onset_sec'] = int(row["eeg_onset_sec"])
        dataEvts.at[index, 'clin_onset_sec'] = int(row["clin_onset_sec"])
        dataEvts.at[index, 'eeg_offset_sec'] = int(row["eeg_offset_sec"])
        dataEvts.at[index, 'clin_offset_sec'] = int(row["clin_offset_sec"])

    return dataEvts
