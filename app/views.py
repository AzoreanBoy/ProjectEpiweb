from django.http import Http404, HttpResponse, JsonResponse
from django.template.loader import get_template
from django.template import Context
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse_lazy
from django.core import serializers
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Min
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from .decorators import *
from .models import *
from .forms import *
from epilab import main, filters
from epilab.storeData import *
from epilab.binfile import bin_file
from epilab import epidbfunctions

from datetime import datetime, timedelta, timezone
from pathlib import Path
import time
import random
import platform
import threading
import queue
import json
import ast
import pickle
import pandas as pd
import scipy.io
from scipy import signal
import traceback
import warnings
import numpy as np
import os

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

def test(request):
    if request.method == "POST":
        dataset = request.POST["datasource"]
        if request.POST["invasive"] == "invasive":
            if dataset == "epidb":
                message = "EpiDB Dataset Chosen"
                patients = PatientEPI.objects.all()
                patient = [i.patientcode for i in patients]
            else:
                message = "Personal Dataset Chosen"
                patients = Patient.objects.filter(user=request.user)
                shared = Patient.objects.filter(
                        idpat__in=hasaccess.objects.filter(user=request.user).values(
                                "patient"
                        )
                )
                patients = (patients | shared).order_by("-idpat")
                patient = [i.idpat for i in patients]
        elif request.POST["invasive"] == "noninvasive":
            if dataset == "epidb":
                message = "EpiDB Dataset Chosen"
                patients = PatientEPI.objects.all()
                patient = [i.patientcode for i in patients]
            else:
                message = "Personal Dataset Chosen"
                patients = Patient.objects.filter(user=request.user)
                shared = Patient.objects.filter(
                        idpat__in=hasaccess.objects.filter(user=request.user).values(
                                "patient"
                        )
                )
                patients = (patients | shared).order_by("-idpat")
                patient = [i.idpat for i in patients]
        return JsonResponse({"patient": patient, "message": message})
    return render(request, "app/test.html", {"patients": PatientEPI.objects.all()})


# Homepage for Unauthenticated Users
def landing(request):
    return render(request, "app/landing.html")


# Login Work


@unauthenticatedUser
def loginUser(request):
    form = CustomUserCreationForm()
    context = {"form": form}
    if request.method == "POST":
        if "usernamelogin" in request.POST:
            us = request.POST["usernamelogin"]
            pa = request.POST["password"]

            user = authenticate(request, username=us, password=pa)

            if user is not None:
                login(request, user)
                return redirect("index")
            else:
                messages.warning(request, "Username or password are incorrect.")
        else:
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.save()
                messages.success(
                        request, "New account " + user.username + " created successfully."
                )
            else:
                messages.error(request, form.errors)
    return render(request, "app/login.html", context)


# Logout

def logoutUser(request):
    logout(request)
    return redirect("landing")


# it ensures that the user is logged in. If it is not logged in it will redirect to the landing function.
@login_required(login_url="landing")
def index(request):
    userstudies = Study.objects.filter(user=request.user)
    onqueue = len(userstudies.filter(completed=None))
    completed = len(userstudies.filter(completed=True))
    processing = len(userstudies.filter(completed=False))
    patients = Patient.objects.filter(user=request.user)
    shared = Patient.objects.filter(
            idpat__in=hasaccess.objects.filter(user=request.user).values("patient")
    )
    patients = patients | shared
    npatients = patients.count()
    nevents = patients.values("event").count()
    recent = userstudies.order_by("-datestudy")[0:6]
    totalstudies = len(Study.objects.filter(user=request.user))
    extract = len(Extraction.objects.filter(study__user=request.user))
    selred = len(SelectionReduction.objects.filter(study__user=request.user))
    classif = len(Classification.objects.filter(study__user=request.user))
    extfeat = ExternalFeature.objects.filter(user=request.user).order_by("-upload_date")
    return render(
            request,
            "app/home.html",
            {
                "onqueue"     : onqueue,
                "completed"   : completed,
                "processing"  : processing,
                "npatients"   : npatients,
                "nevents"     : nevents,
                "total"       : processing + completed + onqueue,
                "totalstudies": totalstudies,
                "extract"     : extract,
                "selred"      : selred,
                "class"       : classif,
                "recent"      : recent,
                "extfeat"     : extfeat,
            },
    )


# Notifications


def notifications(request):
    """
    Gets all the notifications that are marked with the paramenter consumed=false (not read yet by the user)
    and sends them to the user.
    :param request:
    :return: JsonResponse({
        notlist: list with the notifications themselves,
        onqueue: number of studies in the queue,
        completed: number of studies completed,
        processing: number of studies beeing processed,
        total: processing+completed+onqueue,
    })
    """
    notifs = (
        Notification.objects.filter(consumed=False)
        .filter(user=request.user)
        .values("idnot", "description", "datenot")
    )
    userstudies = Study.objects.filter(user=request.user)
    onqueue = len(userstudies.filter(completed=None))
    completed = len(userstudies.filter(completed=True))
    processing = len(userstudies.filter(completed=False))
    return JsonResponse(
            {
                "notlist"   : json.dumps(list(notifs), cls=DateTimeEncoder),
                "onqueue"   : onqueue,
                "completed" : completed,
                "processing": processing,
                "total"     : processing + completed + onqueue,
            }
    )


def clearnotifications(request):
    """
    The function clears all Notifications of the user.

    It updates the consumed parameter of the notifications from false(not read yet) to true (user already read the notification).
    :param request:
    :return: Empty JsonResponse
    """
    notifs = Notification.objects.filter(consumed=False).filter(user=request.user)
    for n in notifs:
        n.consumed = True
        n.save()
    return JsonResponse({})


def confirmUpload(request):
    tmpdir = os.path.join("data", "raw", "tmp")
    data_files = os.listdir(tmpdir)
    for df in data_files:
        if df.lower().endswith(".data"):
            rec = df.split("_")[0]
            filename = df.split(".")[0]

            patient = Patient.objects.get(idrecord=rec)
            user = patient.user
            idpat = patient.idpat
            info = Information.objects.get(filename=str(filename))
            os.rename(
                    os.path.join(tmpdir, str(df)),
                    os.path.join(
                            "data", "raw", "user_" + str(user.username), str(idpat), str(df)
                    ),
            )
            if not info.datafile:
                info.datafile = df
                info.save()
    return redirect("datav2", "rawdata")


@csrf_protect
def cancelUpload(request):
    time.sleep(5)
    todelete = Patient.objects.latest("uploadtime")
    infostodel = Information.objects.filter(patient=todelete)
    for i in infostodel:
        i.delete()
    todelete.delete()
    messages.warning(request, "Your upload operation has been cancelled.")
    return redirect("datav2", "upload")


def cleartmpfiles():
    tmpdir = os.path.join("data", "raw", "tmp")
    for f in os.listdir(tmpdir):
        if f.lower().endswith(".data"):
            os.remove(os.path.join(tmpdir, f))


def datav2(request, option):
    if request.method == "POST":
        file = request.FILES.get("file")
        if file and file.name.lower().endswith(".head"):
            created = storeInformation(file, request.user)
            if created:
                message = "success"
            else:
                message = "error"
                messages.warning(
                        request,
                        "Your upload operation has been cancelled. You already have a patient uploaded with the same id.",
                )
        elif file and file.name.lower().endswith(".data"):
            handle_uploaded_file(file)
            message = "success"
        elif file and file.name.lower().endswith(".evts"):
            storeEvent(file)
            message = "success"
        return JsonResponse({"message": message})
    cleartmpfiles()

    patients = Patient.objects.filter(user=request.user)
    shared = Patient.objects.filter(
            idpat__in=hasaccess.objects.filter(user=request.user).values("patient")
    )
    patients = (patients | shared).order_by("-idpat")

    patients = [i.idpat for i in patients]
    nfiles = {}
    nsamples = {}
    channels = {}
    nfiles = {}
    begin = {}
    end = {}
    duration = {}
    sampfreq = {}
    predictors = {}

    for pid in patients:
        nfiles[pid] = Information.objects.filter(patient=pid).count()
        nsamples[pid] = sum(
                [
                    int(i)
                    for i in Information.objects.filter(patient=pid).values_list(
                        "nsamples", flat=True
                )
                ]
        )
        channels[pid] = ast.literal_eval(
                Information.objects.filter(patient=pid)
                .values_list("elecnames", flat=True)
                .distinct()
                .last()
        )
        nfiles[pid] = Information.objects.filter(patient=pid).aggregate(
                Max("filename")
        )["filename__max"]
        end[pid] = (
            Information.objects.filter(filename=nfiles[pid])
            .values("stopts")
            .last()["stopts"]
        )
        begin[pid] = (
            Information.objects.filter(
                    filename=Information.objects.filter(patient=pid).aggregate(
                            Min("filename")
                    )["filename__min"]
            )
            .values("startts")
            .last()["startts"]
        )
        duration[pid] = str(
                datetime.strptime(end[pid], "%Y-%m-%d %H:%M:%S")
                - datetime.strptime(begin[pid], "%Y-%m-%d %H:%M:%S")
        )
        sampfreq[pid] = (
            Information.objects.filter(patient=pid)
            .values_list("sampfreq", flat=True)
            .distinct()
            .last()
        )
        predictors[pid] = Classification.objects.filter(study__patient=pid)

    studies = Study.objects.filter(user=request.user)
    shared = Study.objects.filter(
            idstudy__in=hasaccess.objects.filter(user=request.user).values("study")
    )
    studies = (studies | shared).order_by("-datestudy")

    form = UploadFilesForm()

    externalfeat = ExternalFeature.objects.filter(user=request.user).order_by("name")

    if option == "rawdata":
        template = "app/data.html"
    elif option == "upload":
        template = "app/dataUpload.html"
    elif option == "studies":
        template = "app/dataStudies.html"
    elif option == "features":
        template = "app/manageFeatures.html"

    return render(
            request,
            template,
            {
                "patients": patients,
                "nfiles"  : nfiles,
                "nsamples": nsamples,
                "channels": channels,
                "nfiles"  : nfiles,
                "begin"   : begin,
                "end"     : end,
                "duration": duration,
                "sampfreq": sampfreq,
                "studies" : studies,
                "models"  : predictors,
                "form"    : form,
                "extfeat" : externalfeat,
            },
    )


def patient(request, idpat):
    if request.method == "POST":
        if "comment" in request.POST:
            comment = request.POST["comment"]
            new_comment = Comment(
                    content=comment,
                    user=request.user,
                    datecom=datetime.now(),
                    patient=Patient.objects.get(idpat=idpat),
            )
            new_comment.save()
            return redirect("patient", idpat)

        elif "todeleteid" in request.POST:
            return deleteComment(request)

        elif "shareuser" in request.POST:
            sharewith = request.POST["shareuser"]
            if sharewith == request.user.username:
                messages.warning(request, "There's no need to share with yourself.")
            else:
                try:
                    new_sharing = hasaccess(
                            user=User.objects.get(username=sharewith),
                            patient=Patient.objects.get(pk=idpat),
                    )
                    new_sharing.save()
                    new_notification = Notification(
                            datenot=datetime.now(),
                            consumed=False,
                            description="User "
                                        + request.user.username
                                        + " shared one of his patient data with you.",
                            user=User.objects.get(username=sharewith),
                    )
                    new_notification.save()
                    messages.info(
                            request,
                            "You have successfully shared your patient data with "
                            + sharewith
                            + ".",
                    )
                except IntegrityError as ie:
                    messages.warning(
                            request, "You have already shared with " + sharewith + "."
                    )
                except ObjectDoesNotExist as odne:
                    messages.warning(request, "User " + sharewith + " does not exist.")
                except Exception as e:
                    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                    message = template.format(type(e).__name__, e.args)
                    print(message)

    idpat = int(idpat)
    patient = Patient.objects.get(idpat=idpat)

    patients = Patient.objects.filter(user=request.user)
    shared = Patient.objects.filter(
            idpat__in=hasaccess.objects.filter(user=request.user).values("patient")
    )
    patients = patients | shared
    patientsid = [i.idpat for i in patients]

    nfiles = Information.objects.filter(patient=idpat).count()
    nsamples = sum(
            [
                int(i)
                for i in Information.objects.filter(patient=idpat).values_list(
                    "nsamples", flat=True
            )
            ]
    )
    channels = ast.literal_eval(
            Information.objects.filter(patient=idpat)
            .values_list("elecnames", flat=True)
            .distinct()
            .last()
    )
    nfiles = Information.objects.filter(patient=idpat).aggregate(Max("filename"))[
        "filename__max"
    ]
    end = Information.objects.filter(filename=nfiles).values("stopts").last()["stopts"]
    begin = (
        Information.objects.filter(
                filename=Information.objects.filter(patient=idpat).aggregate(
                        Min("filename")
                )["filename__min"]
        )
        .values("startts")
        .last()["startts"]
    )
    duration = str(
            datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
            - datetime.strptime(begin, "%Y-%m-%d %H:%M:%S")
    )
    sampfreq = (
        Information.objects.filter(patient=idpat)
        .values_list("sampfreq", flat=True)
        .distinct()
        .last()
    )

    listfiles = Information.objects.filter(patient=idpat).values_list("filename")

    # EXTRACTION STUDIES
    extraction = Extraction.objects.filter(study__user=request.user).filter(
            study__patient=idpat
    )
    extractionshared = Extraction.objects.filter(
            study__pk__in=hasaccess.objects.filter(user=request.user)
            .filter(study__patient=idpat)
            .values("study")
    )

    # NORMALIZATION STUDIES
    normalization = Normalization.objects.filter(study__user=request.user).filter(
            study__patient=idpat)
    normalizationshared = Normalization.objects.filter(
            study__pk__in=hasaccess.objects.filter(user=request.user)
            .filter(study__patient=idpat)
            .values("study")
    )

    # SELECTION REDUCTION STUDIES
    selred = SelectionReduction.objects.filter(study__user=request.user).filter(
            study__patient=idpat
    )
    selredshared = SelectionReduction.objects.filter(
            study__pk__in=hasaccess.objects.filter(user=request.user)
            .filter(study__patient=idpat)
            .values("study")
    )

    classification = Classification.objects.filter(study__user=request.user).filter(
            study__patient=idpat
    )
    classificationshared = Classification.objects.filter(
            study__pk__in=hasaccess.objects.filter(user=request.user)
            .filter(study__patient=idpat)
            .values("study")
    )

    previous = (
        patientsid[patientsid.index(idpat) - 1] if idpat > 1 else patients.last().idpat
    )
    next = (
        patientsid[patientsid.index(idpat) + 1]
        if idpat < patients.last().idpat
        else patients[0].idpat
    )

    comments = Comment.objects.filter(patient=patient).order_by("-datecom")
    sharingwith = hasaccess.objects.filter(patient__pk=idpat)

    events = Event.objects.filter(patient=idpat)
    evtsduration = [
        str(timedelta(seconds=(int(i.eeg_offset_sec) - int(i.eeg_onset_sec))))
        for i in events
    ]

    return render(
            request,
            "app/patientv2.html",
            {
                "patient"              : patient,
                "nfiles"               : nfiles,
                "nsamples"             : nsamples,
                "channels"             : channels,
                "nfiles"               : nfiles,
                "begin"                : begin,
                "end"                  : end,
                "duration"             : duration,
                "sampfreq"             : sampfreq,
                "listfiles"            : listfiles,
                "extractionstudies"    : extraction | extractionshared,
                "normalizationstudies" : normalization | normalizationshared,
                "selectionstudies"     : selred | selredshared,
                "classificationstudies": classification | classificationshared,
                "previous"             : previous,
                "next"                 : next,
                "comments"             : comments,
                "sharing"              : sharingwith,
                "events"               : zip(events, evtsduration),
            },
    )


# PLOT FUNCTIONS


# TODO: Request last window
def plotRaw(request, idpat, step, window):
    step = int(step)
    if request.method == "POST":
        if "filter" in request.POST:
            return filterplot(request)
        else:
            print("\n\n", request.POST)
            if "time" in request.POST:
                try:
                    requestedTime = datetime.strptime(
                            request.POST["time"], "%Y-%m-%dT%H:%M:%S"
                    )
                except ValueError:
                    requestedTime = datetime.strptime(
                            request.POST["time"], "%Y-%m-%dT%H:%M"
                    )
            if "event" in request.POST:
                try:
                    requestedTime = datetime.strptime(
                            request.POST["event"], "%Y-%m-%d %H:%M:%S.%f"
                    )
                except ValueError:
                    requestedTime = datetime.strptime(
                            request.POST["event"], "%Y-%m-%d %H:%M:%S"
                    )
            print(requestedTime)
            window = getWindow(idpat, step, requestedTime)
    else:
        window = int(window)

    [df, begin, close, elecnames] = getDataPlot(idpat, window, step)

    evts = []
    events = Event.objects.filter(patient=idpat)
    for i in range(len(events)):
        tmp = {"begin": events[i].eeg_onset, "end": events[i].eeg_offset}
        evts.append(tmp)

    return render(
            request,
            "app/plotRaw.html",
            {
                "signal"    : df.T.values.tolist(),
                "signaltime": [str(i) for i in df.index],
                "channels"  : elecnames,
                "begin"     : (begin + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S"),
                "close"     : (close - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S"),
                "windowprev": window - 1,
                "windownext": window + 1,
                "patid"     : idpat,
                "step"      : step,
                "window"    : window,
                "sampfreq"  : int(Information.objects.filter(patient=idpat)[0].sampfreq),
                "events"    : events,
                "evts"      : evts,
            },
    )


def plotRawAsync(request, idpat):
    step = int(request.POST["step"])
    if "option" in request.POST:
        requestedTime = datetime.strptime(request.POST["time"], "%Y-%m-%d %H:%M:%S")
        print("\n Changing view -> step: ", step, "; requestedTime: ", requestedTime)
        window = getWindow(idpat, step, requestedTime)
        print("\twindow: ", window)
    else:
        window = int(request.POST["window"])
        print(
                "\n Calculating prev and next windows -> step: ", step, "; window: ", window
        )

    [df, begin, close, elecnames] = getDataPlot(idpat, window, step)
    print("Sending data... with ", df.isna().sum().sum(), "nan")
    return JsonResponse(
            {
                "signal"    : df.T.values.tolist(),
                "signaltime": [str(i) for i in df.index],
                "begin"     : (begin + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S"),
                "close"     : (close - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S"),
                "window"    : window,
            }
    )


def plotEvent(request, idevent, step):
    step = int(step)
    event = Event.objects.get(pk=idevent)
    idpat = event.patient.idpat
    time = event.eeg_onset
    try:
        requestedTime = datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        requestedTime = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
    window = getWindow(idpat, step, requestedTime)
    return plotRaw(request, idpat, step, window)


def getWindow(idpat, step, requestedTime):
    files = Information.objects.filter(patient=idpat).order_by("startts")
    sampfreq = int(Information.objects.filter(patient=idpat)[0].sampfreq)
    window = 0
    windowstart = datetime.strptime(files[0].startts, "%Y-%m-%d %H:%M:%S")
    windowend = datetime.strptime(files[0].startts, "%Y-%m-%d %H:%M:%S") + timedelta(
            seconds=(step / sampfreq)
    )
    while True:
        if windowstart <= requestedTime < windowend:
            break
        windowstart = windowend
        windowend = windowstart + timedelta(seconds=(step / sampfreq))
        window += 1
    return window


def getDataPlot(idpat, window, step, flag=False):
    print("Getting data ->  window: ", window, "; step: ", step)
    resampling = {
        921600  : "5S",
        4608000 : "20S",
        11059200: "40S",
        22118400: "80S",
    }

    files = Information.objects.filter(patient=idpat).order_by("startts")
    if not files:
        return [], [], [], []

    sampfreq = int(Information.objects.filter(patient=idpat)[0].sampfreq)
    nsamplesBegin = step * window
    nsamplesEnd = nsamplesBegin + step

    requestedFiles = []
    start = 0
    for f in files:
        start += int(f.nsamples)
        if nsamplesBegin < start < nsamplesEnd:
            requestedFiles.append(f)
        elif start >= nsamplesEnd:
            requestedFiles.append(f)
            break

    df = pd.DataFrame()
    for requestedFile in requestedFiles:
        f = open(requestedFile.headfile.path[:-5] + ".data", "rb")

        # TODO: Use BIN class
        rawByteToInt = np.fromfile(f, dtype=np.int16)
        signalData = rawByteToInt * float(float(requestedFile.conversionfactor))

        signalData = signalData.reshape((int(requestedFile.nchannels), -1), order="F")

        signalData_df = pd.DataFrame(data=signalData)
        signalData_df = signalData_df.T

        timeRange = pd.date_range(
                start=requestedFile.startts,
                end=requestedFile.stopts,
                periods=int(requestedFile.nsamples),
        )
        signalData_df.index = timeRange

        downSamp = 0
        if step > 76800:
            downSamp = (
                resampling[step]
                if step in resampling
                else resampling[min(resampling.keys(), key=lambda k: abs(k - step))]
            )
            signalData_df = signalData_df.resample(downSamp).first().replace(np.nan, 0)
        elif flag:
            downSamp = "30ms"
            signalData_df = signalData_df.resample(downSamp).first().replace(np.nan, 0)

        df = pd.concat([df, signalData_df], axis=0)

    elecnames = ast.literal_eval(files[0].elecnames)
    begin = datetime.strptime(files[0].startts, "%Y-%m-%d %H:%M:%S")
    close = datetime.strptime(files.last().stopts, "%Y-%m-%d %H:%M:%S")
    start = begin + timedelta(seconds=window * (step / sampfreq))
    end = start + timedelta(seconds=(step / sampfreq))
    try:
        df = df[start:end]
    except KeyError:
        df = df[start.strftime("%Y-%m-%d %H:%M:%S"): end.strftime("%Y-%m-%d %H:%M:%S")]

    print(
            "Data obtained -> window: ",
            window,
            "; step: ",
            step,
            "; downsampled: ",
            downSamp,
    )
    return df, begin, close, elecnames


def filterplot(request):
    filter = request.POST["filter"]
    sampfreq = int(request.POST["sampfreq"])

    data = [list(ast.literal_eval(i)) for i in request.POST.getlist("data[][]")]

    config = [float(i) for i in request.POST.getlist("config[]")]

    if filter == "lowpass":
        conf = ["lowpass", config[0], config[1], sampfreq]
    elif filter == "highpass":
        conf = ["highpass", config[0], config[1], sampfreq]
    else:
        conf = ["notch", config[0], sampfreq]

    # * filteredData -> list of lists
    filteredData = [
        filters.filtering(dataChannel, conf).tolist() for dataChannel in data
    ]
    print(len(filteredData), len(filteredData[0]))
    return JsonResponse({"data": filteredData})


# STUDY FUNCTIONS
def createStudy(request, idpat):
    if request.method == "POST":
        if "patid" in request.POST:
            return createStudyAsync(request)
        elif "setname" in request.POST:
            return extractingFeatures(request)
        elif "datasource" in request.POST:
            return chooseDataset(request)
    # try:
    patients = Patient.objects.filter(user=request.user)
    shared = Patient.objects.filter(
            idpat__in=hasaccess.objects.filter(user=request.user).values("patient")
    )
    patients = (patients | shared).order_by("-idpat")
    patients = [i.idpat for i in patients]
    if idpat == "0" and len(patients) > 0:
        idpat = list(patients)[0]
    # patient = Patient.objects.get(idpat=idpat)
    # except:
    #     messages.warning(
    #             request,
    #             "Something went wrong.\n You may not have any raw data imported to start creating studies or the dataset you are requesting does not exist.",
    #     )
    #     return redirect("index")

    context = {
        "patients": patients,
        "patid"  : 0,
    }

    if len(patients) > 0:
        context.update({
            "patid": idpat,
        })

        patient = Patient.objects.get(idpat=idpat)

        [df, tmp, tmp2, elecnames] = getDataPlot(idpat, 0, 1260, True)

        nfiles = {}
        nsamples = {}
        channels = {}
        nfiles = {}
        begin = {}
        end = {}
        duration = {}
        sampfreq = {}

        for pid in patients:
            nfiles[pid] = Information.objects.filter(patient=pid).count()
            nsamples[pid] = sum(
                    [
                        int(i)
                        for i in Information.objects.filter(patient=pid).values_list(
                            "nsamples", flat=True
                    )
                    ]
            )
            channels[pid] = ast.literal_eval(
                    Information.objects.filter(patient=pid)
                    .values_list("elecnames", flat=True)
                    .distinct()
                    .last()
            )
            nfiles[pid] = Information.objects.filter(patient=pid).aggregate(
                    Max("filename")
            )["filename__max"]
            end[pid] = (
                Information.objects.filter(filename=nfiles[pid])
                .values("stopts")
                .last()["stopts"]
            )
            begin[pid] = (
                Information.objects.filter(
                        filename=Information.objects.filter(patient=pid).aggregate(
                                Min("filename")
                        )["filename__min"]
                )
                .values("startts")
                .last()["startts"]
            )
            duration[pid] = str(
                    datetime.strptime(end[pid], "%Y-%m-%d %H:%M:%S")
                    - datetime.strptime(begin[pid], "%Y-%m-%d %H:%M:%S")
            )
            sampfreq[pid] = (
                Information.objects.filter(patient=pid)
                .values_list("sampfreq", flat=True)
                .distinct()
                .last()
            )

        extractions = Extraction.objects.filter(study__patient=idpat)

        context.update(
            {
                "nfiles": nfiles,
                "nsamples": nsamples,
                "channels": channels,
                "nfiles": nfiles,
                "begin": begin,
                "end": end,
                "duration": duration,
                "sampfreq": sampfreq,
                "signal": df.T.values.tolist(),
                "signaltime": [str(i) for i in df.index],
                "elecnames": elecnames,
                "extracts": extractions,
            }
        )

    extunifeat = ExternalFeature.objects.filter(user=request.user).filter(type="uni")
    extmultifeat = ExternalFeature.objects.filter(user=request.user).filter(
            type="multi"
    )
    extecgfeat = ExternalFeature.objects.filter(user=request.user).filter(type="ecg")

    context.update(
        {
            "unifeat": extunifeat,
            "multifeat": extmultifeat,
            "ecgfeat": extecgfeat,
        }
    )

    return render(
        request,
        "app/createStudy.html",
        context,
    )

    # return render(
    #         request,
    #         "app/createStudy.html",
    #         {
    #             "patid"     : idpat,
    #             "patients"  : patients,
    #             "nfiles"    : nfiles,
    #             "nsamples"  : nsamples,
    #             "channels"  : channels,
    #             "nfiles"    : nfiles,
    #             "begin"     : begin,
    #             "end"       : end,
    #             "duration"  : duration,
    #             "sampfreq"  : sampfreq,
    #             "signal"    : df.T.values.tolist(),
    #             "signaltime": [str(i) for i in df.index],
    #             "elecnames" : elecnames,
    #             "extracts"  : extractions,
    #             "unifeat"   : extunifeat,
    #             "multifeat" : extmultifeat,
    #             "ecgfeat"   : extecgfeat,
    #         },
    # )


def createStudyAsync(request):
    # print("Patient changed")
    dataset = request.POST["dataset"]
    idpat = request.POST["patid"]
    if dataset == "epidb":
        admission = Admission.objects.get(id=idpat)
        nfiles = epidbfunctions.get_admission_files(admission.id).count()
        channels = epidbfunctions.get_channels_list(admission.id)
        nchannels = len(channels)
        start_time = (
            Recording.objects.filter(admission=admission)
            .order_by("begin_time")
            .first()
            .begin_time
        )
        end_time = (
            Recording.objects.filter(admission=admission)
            .order_by("begin_time")
            .last()
            .end_time
        )
        duration = str(end_time - start_time)
        sample_rate = (
            Recording.objects.filter(admission=admission).first().sample_rate
        )

        return JsonResponse({
            "datasource" : "epidb",
            "admission"  : admission.id,
            "nfiles"     : nfiles,
            "channels"   : channels,
            "nchannels"  : nchannels,
            "start_time" : str(start_time),
            "end_time"   : str(end_time),
            "duration"   : duration,
            "sample_rate": sample_rate,
            "nsamples"   : "-",
        })

    else:
        # PATIENT INFO
        patient = Patient.objects.get(idpat=idpat)
        nfiles = Information.objects.filter(patient=idpat).count()
        nchannels = len(ast.literal_eval(Information.objects.filter(patient=idpat)[0].elecnames))
        start_time = Information.objects.filter(patient=idpat).order_by('filename').first().startts
        end_time = Information.objects.filter(patient=8902).order_by('filename').last().stopts
        duration = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S") - datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        sample_rate = Information.objects.filter(patient=idpat)[0].sampfreq

        # PREVIOUS EXTRACTIONS
        extractions = Extraction.objects.filter(study__patient=idpat)
        names = [i.study.name for i in extractions]
        res = [i.study.user.username for i in extractions]
        ids = [i.study.idstudy for i in extractions]
        try:
            [df, tmp, tmp2, elecnames] = getDataPlot(idpat, 0, 1260, True)
            return JsonResponse(
                    {
                        "signal"     : df.T.values.tolist(),
                        "signaltime" : [str(i) for i in df.index],
                        "elecnames"  : elecnames,
                        "dataset"    : "epiweb",
                        "patient"    : idpat,
                        "nfiles"     : nfiles,
                        "nchannels"  : nchannels,
                        "start_time" : start_time,
                        "end_time"   : end_time,
                        "duration"   : duration,
                        "sample_rate": sample_rate,
                        "nsamples"   : "NaN",
                    }
            )
        except Exception:
            print(traceback.format_exc())
            return JsonResponse(
                    {
                        "names"      : names,
                        "res"        : res,
                        "ids"        : ids,
                        "dataset"    : "epiweb",
                        "patient"    : idpat,
                        "nfiles"     : nfiles,
                        "nchannels"  : nchannels,
                        "start_time" : start_time,
                        "end_time"   : end_time,
                        "duration"   : duration,
                        "sample_rate": sample_rate,
                        "nsamples"   : "NaN",
                    }
            )


def chooseDataset(request):
    dataset = request.POST["datasource"]
    if dataset == "epidb":
        # print("EPIDB chosen")
        admissions = Admission.objects.all().order_by("-adm_date")
        adms = [adm.id for adm in admissions]
        admission = admissions.first()
        nfiles = epidbfunctions.get_admission_files(admission.id).count()
        channels = epidbfunctions.get_channels_list(admission.id)
        nchannels = len(channels)
        start_time = (
            Recording.objects.filter(admission=admission)
            .order_by("begin_time")
            .first()
            .begin_time
        )
        end_time = (
            Recording.objects.filter(admission=admission)
            .order_by("begin_time")
            .last()
            .end_time
        )
        duration = str(end_time - start_time)
        sample_rate = (
            Recording.objects.filter(admission=admission).first().sample_rate
        )

        return JsonResponse(
                {
                    "datasource" : "epidb",
                    "admissions" : adms,
                    "admission"  : admission.id,
                    "nfiles"     : nfiles,
                    "channels"   : channels,
                    "nchannels"  : nchannels,
                    "start_time" : str(start_time),
                    "end_time"   : str(end_time),
                    "duration"   : duration,
                    "sample_rate": sample_rate,
                }
        )

    else:
        # print("EPIWEB chosen")
        patients = Patient.objects.filter(user=request.user)
        shared = Patient.objects.filter(
                idpat__in=hasaccess.objects.filter(user=request.user).values("patient")
        )
        patients = (patients | shared).order_by("-idpat")
        patients = [i.idpat for i in patients]
        nfiles = Information.objects.filter(patient=patients[0]).count()
        channels = ast.literal_eval(
                Information.objects.filter(patient=patients[0]).first().elecnames
        )
        nchannels = len(channels)
        start_time = (
            Information.objects.filter(patient=patients[0])
            .order_by("filename")
            .first()
            .startts
        )
        end_time = (
            Information.objects.filter(patient=patients[0])
            .order_by("filename")
            .last()
            .stopts
        )
        print(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"))
        print(datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"))
        duration = str(
                datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S") - datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"))
        print("Duration: " + duration)
        sample_rate = Information.objects.filter(patient=patients[0]).first().sampfreq

    return JsonResponse(
            {
                "datasource" : "epiweb",
                "patients"   : patients,
                "patient"    : patients[0],
                "nfiles"     : nfiles,
                "channels"   : channels,
                "nchannels"  : nchannels,
                "start_time" : str(start_time),
                "end_time"   : str(end_time),
                "duration"   : duration,
                "sample_rate": sample_rate,
            }
    )


def extractingFeatures(request):
    patient = request.POST["patient"]  # OR ADMISSION IF EPIDB
    sampfreq = request.POST["sampfreq"]
    channels = [i for i in request.POST.getlist("channels[]")]
    filter = request.POST["filter"]
    filteroptions = [
        ast.literal_eval(i) for i in request.POST.getlist("filteroptions[]")
    ]
    windowing = [ast.literal_eval(i) for i in request.POST.getlist("windowing[]")]
    feats = [i for i in request.POST.getlist("feats[]")]
    featsoptions = {
        k: v
        for x in [i for i in json.loads(request.POST["featsoptions[][]"], object_pairs_hook=dict)]
        for k, v in x.items()
    }
    SPH = request.POST["SPH"]
    SOP = request.POST["SOP"]

    # NAME AND DIRECTORY OF THE STUDY
    givenname = (
        datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if len(request.POST["setname"]) == 0
        else request.POST["setname"].replace(" ", "_")
    )
    dir = os.path.join(
            "data",
            "features",
            f"user_{request.user.username}",
            f"featextraction_{givenname}",
    )
    # VERIFY IF THE DIRECTORY EXISTS AND CREATE IT IF NOT
    os.makedirs(
            os.path.join("data", "features", f"user_{request.user.username}"), exist_ok=True
    )

    if request.POST['database'] == 'epidb':
        print("Extraction Feature for EPIDB Admission")

        # CREATE THE STUDY
        new_study = Study(
                name=givenname,
                directory=dir,
                type=Study.Type.EXTRACT,
                user=request.user,
                admission_EPIDB=int(patient),
        )
        new_study.save()

        # UPDATE THE DIRECTORY OF THE STUDY TO INCLUDE THE STUDY ID
        new_dir = os.path.join(
                "data",
                "features",
                f"user_{request.user.username}",
                f"featextraction_{new_study.idstudy}_{givenname}",
        )
        new_study.directory = new_dir
        new_study.save()

        print("\n\nExtracting Features:")
        print(
                "\nEPIDB Admission:\n",
                patient,
                "\nChannels:\n",
                channels,
                "\nFilter:\n",
                filter,
                "\nFilteroptions:\n",
                filteroptions,
                "\nWindowing:\n",
                windowing,
                "\nFeats:\n",
                feats,
                "\nFeats Options:\n",
                featsoptions,
                "\nName:\n",
                givenname,
                "\n",
        )

        # SEND IT TO THE QUEUE
        epidbfunctions.extract_epidb_features.delay(
                request.user.id,
                patient,
                sampfreq,
                channels,
                filter,
                filteroptions,
                windowing[0],
                windowing[1],
                feats,
                featsoptions,
                new_study.directory,
                new_study.idstudy,
                SPH,
                SOP,
        )
        return redirect("index")
    else:
        print("EPIWEB")
        # CREATE THE STUDY
        new_study = Study(
                name=givenname,
                directory=dir,
                type=Study.Type.EXTRACT,
                user=request.user,
                patient=Patient.objects.get(idpat=patient),
        )
        new_study.save()

        # UPDATE THEDIRECTORY OF THE STUDY TO INCLUDE THE STUDY ID
        new_dir = os.path.join(
                "data",
                "features",
                f"user_{request.user.username}",
                f"featextraction_{new_study.idstudy}_{givenname}",
        )
        new_study.directory = new_dir
        new_study.save()

        print("\n\nExtracting Features:")
        print(
                "\nPatient:\n",
                patient,
                "\nSampfreq:\n",
                sampfreq,
                "\nChannels:\n",
                channels,
                "\nFilter:\n",
                filter,
                "\nFilteroptions:\n",
                filteroptions,
                "\nWindowing:\n",
                windowing,
                "\nFeats:\n",
                feats,
                "\nFeats Options:\n",
                featsoptions,
                "\nName:\n",
                givenname,
                "\n",
        )

        # SEND IT TO THE QUEUE
        main.main.delay(
                [
                    "extract_features",
                    request.user.id,
                    [
                        patient,
                        sampfreq,
                        channels,
                        filter,
                        filteroptions,
                        windowing,
                        feats,
                        featsoptions,
                        new_study.directory,
                        new_study.idstudy,
                        SPH,
                        SOP,
                    ],
                ]
        )
        return redirect('index')


#TODO: Correct Function to Work properly with EPIDB origin studies
@studyAcessAllowed
def extractionStudyPage(request, studyId):
    if request.method == "POST":
        if "comment" in request.POST:
            comment = request.POST["comment"]
            study = Study.objects.get(idstudy=studyId)
            new_comment = Comment(
                    content=comment, user=request.user, datecom=datetime.now(), study=study
            )
            new_comment.save()
            return redirect("extractionStudy", studyId=study.idstudy)
        elif "shareuser" in request.POST:
            sharewith = request.POST["shareuser"]
            if sharewith == request.user.username:
                messages.warning(
                        request, "There's no need to share a study with yourself."
                )
            else:
                try:
                    new_sharing = hasaccess(
                            user=User.objects.get(username=sharewith),
                            study=Study.objects.get(pk=studyId),
                    )
                    new_sharing.save()
                    new_notification = Notification(
                            datenot=datetime.now(),
                            consumed=False,
                            description="User "
                                        + request.user.username
                                        + " shared one of his studies with you.",
                            user=User.objects.get(username=sharewith),
                    )
                    new_notification.save()
                    messages.info(
                            request,
                            "You have successfully shared your study with "
                            + sharewith
                            + ".",
                    )
                except IntegrityError as ie:
                    messages.warning(
                            request, "You have already shared with " + sharewith + "."
                    )
                except ObjectDoesNotExist as odne:
                    messages.warning(request, "User " + sharewith + " does not exist.")
                except Exception as e:
                    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                    message = template.format(type(e).__name__, e.args)
                    print(message)
        elif "todeleteid" in request.POST:
            return deleteComment(request)
        else:
            print("\n\nEDITING THE STUDY\n")
            study = Extraction.objects.get(study__idstudy=studyId)
            patient = int(request.POST["patient"])
            sampfreq = (
                Information.objects.filter(patient=patient)
                .values_list("sampfreq", flat=True)
                .distinct()
                .last()
            )
            channels = [i for i in request.POST.getlist("channels[]")]
            filter = request.POST["filter"]
            filteroptions = [
                ast.literal_eval(i) for i in request.POST.getlist("filteroptions[]")
            ]
            windowing = [
                ast.literal_eval(i) for i in request.POST.getlist("windowing[]")
            ]
            feats = [i for i in request.POST.getlist("feats[]")]
            featsoptions = {
                k: v
                for x in [i for i in json.loads(request.POST["featsoptions[][]"], object_pairs_hook=dict)]
                for k, v in x.items()
            }
            givenname = (
                datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                if len(request.POST["setname"]) == 0
                else request.POST["setname"]
            )
            dir = os.path.join(
                    "data",
                    "features",
                    f"user_{request.user.username}",
                    f"featextraction_{study.study.idstudy}_{givenname}",
            )
            os.rename(
                    os.path.join(
                            "data",
                            "features",
                            f"user_{request.user.username}",
                            f"featextraction_{study.study.idstudy}_{study.study.name}.npy",
                    ),
                    dir + ".npy",
            )

            study.study.name = givenname
            study.study.directory = dir
            study.study.save()

            print("\n\n-> Updating Extraction Study:")
            print(
                    "\nPatient:\n",
                    patient,
                    "\nSampfreq:\n",
                    sampfreq,
                    "\nChannels:\n",
                    channels,
                    "\nFilter:\n",
                    filter,
                    "\nFilteroptions:\n",
                    filteroptions,
                    "\nWindowing:\n",
                    windowing,
                    "\nFeats:\n",
                    feats,
                    "\nFeats Options:\n",
                    featsoptions,
                    "\nName:\n",
                    givenname,
                    "\n",
            )

            main.main.delay(
                    [
                        "update_extract_features",
                        request.user.id,
                        [
                            patient,
                            sampfreq,
                            channels,
                            filter,
                            filteroptions,
                            windowing,
                            feats,
                            featsoptions,
                            study.study.directory,
                            study.study.idstudy,
                        ],
                    ]
            )

    studyId = int(studyId)
    try:
        study = Extraction.objects.get(study__pk=studyId)
    except:
        messages.warning(
                request,
                "Something went wrong.\n A study with that ID does not exist or it is on queue.",
        )
        return redirect("index")

    studies = Extraction.objects.filter(study__user=request.user)
    shared = Extraction.objects.filter(
            study__idstudy__in=hasaccess.objects.filter(user=request.user).values("study")
    )
    studies = (studies | shared).order_by("study_id")
    studiesid = [i.study.idstudy for i in studies]

    channels = ast.literal_eval(study.channels)
    feats = [i.name for i in study.features.all()]
    featsoptions = study.featsoptions
    filteroptions = [str(study.filter_cutoff), str(study.filter_order)]

    try:
        previous = (
            studiesid[studiesid.index(studyId) - 1]
            if studyId > 1
            else studies.last().study.idstudy
        )
        next = (
            studiesid[studiesid.index(studyId) + 1]
            if studyId < studies.last().study.idstudy
            else studies[0].study.idstudy
        )
    except:
        previous = studyId
        next = studyId

    comments = Comment.objects.filter(study__idstudy=studyId).order_by("-datecom")
    sharingwith = hasaccess.objects.filter(study__idstudy=studyId).order_by("-since")

    normstudies = Normalization.objects.filter(extraction_study__pk=studyId).filter(
            study__user=request.user
    )
    normshared = Normalization.objects.filter(extraction_study__pk=studyId).filter(
            study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
    )

    selredstudies = SelectionReduction.objects.filter(
            extraction_study__pk=studyId
    ).filter(study__user=request.user)
    selredshared = SelectionReduction.objects.filter(
            extraction_study__pk=studyId
    ).filter(study__pk__in=hasaccess.objects.filter(user=request.user).values("study"))

    classifstudies = Classification.objects.filter(extraction_study__pk=studyId).filter(
            study__user=request.user
    )
    classifshared = Classification.objects.filter(extraction_study__pk=studyId).filter(
            study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
    )

    file = study.study.directory
    try:
        nfeats = np.load(file + ".npz", allow_pickle=True)["data2d"].shape[1]
        nsamples = np.load(file + ".npz", allow_pickle=True)["data2d"].shape[0]
    except Exception:
        print(traceback.print_exc())
        nfeats = float("NaN")
        nsamples = float("NaN")
        
    if study.study.patient is not None:
        patientchannels = ast.literal_eval(
                Information.objects.filter(patient=study.study.patient)
                .values_list("elecnames", flat=True)
                .distinct()
                .last()
        )
    else:
        patientchannels = epidbfunctions.get_channels_list(study.study.admission_EPIDB) if study.study.admission_EPIDB is not None else []

    return render(
            request,
            "app/extractionStudy.html",
            {
                "study"                : study,
                "channels"             : channels,
                "feats"                : feats,
                "featsoptions"         : featsoptions,
                "filteroptions"        : filteroptions,
                "previous"             : previous,
                "next"                 : next,
                "sharing"              : sharingwith,
                "comments"             : comments,
                "normstudies"          : normstudies | normshared,
                "selectionstudies"     : selredstudies | selredshared,
                "classificationstudies": classifstudies | classifshared,
                "nfeats"               : nfeats,
                "nsamples"             : nsamples,
                "patientchannels"      : patientchannels,
            },
    )


def plotFeature(request, studyId, stepminutes, window):
    stepminutes = float(stepminutes)
    try:
        extractstudy = Extraction.objects.get(study__pk=studyId)
        data = np.load((extractstudy.study.directory) + ".npz", allow_pickle=True)[
            "data"
        ]
    except:
        messages.warning(
                request, "Something went wrong.\n The file from that study may be missing."
        )
        return redirect("index")

    timeRange = pd.date_range(
            start=Information.objects.filter(patient=extractstudy.study.patient)[0].startts,
            end=Information.objects.filter(patient=extractstudy.study.patient)[4].stopts,
            periods=data[0].shape[2],
    )
    step = len(
            [
                timeRange.to_list().index(i)
                for i in timeRange
                if i <= timeRange[0] + timedelta(minutes=stepminutes)
            ]
    )

    if request.method == "POST" and "time" in request.POST:  # Jump to selected time
        print(request.POST["time"])
        try:
            requestedTime = datetime.strptime(request.POST["time"], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            requestedTime = datetime.strptime(request.POST["time"], "%Y-%m-%dT%H:%M")
        window = 0
        windowstart = timeRange[0]
        windowend = timeRange[step - 1]
        while True:
            if windowstart <= requestedTime < windowend:
                break
            window += 1
            windowstart = windowend
            windowend = windowstart + timeRange[(window + 1) * step]
    else:
        window = int(window)

    [datalist, timeRangeList] = getFeatureDataPlot(data, window, step, timeRange)

    return render(
            request,
            "app/plotFeature.html",
            {
                "study"     : extractstudy,
                "signal"    : datalist,
                "signaltime": timeRangeList,
                "begin"     : (timeRange[0]).strftime("%Y-%m-%dT%H:%M:%S"),
                "close"     : (timeRange[-1]).strftime("%Y-%m-%dT%H:%M:%S"),
                "window"    : window,
                "windowprev": window - 1,
                "windownext": window + 1,
                "step"      : stepminutes,
                "info"      : [
                    ast.literal_eval(extractstudy.feats),
                    ast.literal_eval(extractstudy.subfeats),
                    ast.literal_eval(extractstudy.channels),
                ],
            },
    )


def plotFeatureAsync(request, studyId):
    stepminutes = float(request.POST["step"])
    extractstudy = Extraction.objects.get(study__pk=studyId)
    data = np.load((extractstudy.study.directory) + ".npz", allow_pickle=True)["data"]

    timeRange = pd.date_range(
            start=Information.objects.filter(patient=extractstudy.study.patient)[0].startts,
            end=Information.objects.filter(patient=extractstudy.study.patient)[4].stopts,
            periods=data[0].shape[2],
    )
    step = len(
            [
                timeRange.to_list().index(i)
                for i in timeRange
                if i <= timeRange[0] + timedelta(minutes=stepminutes)
            ]
    )
    if "option" in request.POST:
        requestedTime = datetime.strptime(request.POST["time"], "%Y-%m-%d %H:%M:%S")
        print(
                "\n Changing view -> step: ",
                step,
                " (-> ",
                stepminutes,
                " minutes); requestedTime: ",
                requestedTime,
        )
        window = 0
        windowstart = timeRange[0]
        windowend = timeRange[step - 1]
        while True:
            if windowstart <= requestedTime < windowend:
                break
            window += 1
            windowstart = windowend
            print("\n\n\n", windowstart, timeRange[(window + 1) * step], "\n")
            windowend = windowstart + timeRange[(window + 1) * step]
        print("\twindow: ", window)
    else:
        window = int(request.POST["window"])
        print(
                "\n Calculating prev and next windows -> step: ",
                step,
                " (-> ",
                stepminutes,
                " minutes); window: ",
                window,
        )

    [datalist, timeRangeList] = getFeatureDataPlot(data, window, step, timeRange)

    return JsonResponse(
            {
                "signal"    : datalist,
                "signaltime": timeRangeList,
                "begin"     : (timeRange[0]).strftime("%Y-%m-%dT%H:%M:%S"),
                "close"     : (timeRange[-1]).strftime("%Y-%m-%dT%H:%M:%S"),
                "window"    : window,
            }
    )


def getFeatureDataPlot(data, window, step, timeRange):
    datalist = []
    for i in data:
        feat = []
        for j in i:
            option = []
            for channel in j:
                option.append(channel[window * step: (window + 1) * step].tolist())
            feat.append(option)
        datalist.append(feat)
    timeRangeList = [str(i) for i in timeRange[window * step: (window + 1) * step]]
    return datalist, timeRangeList


def train_test_split(request, studyId: int):
    if request.method == "POST":
        if "studyId" in request.POST:
            return train_test_splitAsync(request)
        elif 'splitpoint' in request.POST:
            return splitingData(request)
    try:
        studies = Study.objects.filter(user=request.user).filter(completed=True)
        shared = Study.objects.filter(
                idstudy__in=hasaccess.objects.filter(user=request.user).values("study")
        ).filter(completed=True)
        studies = (
            (studies | shared).filter(type=Study.Type.EXTRACT).order_by("-datestudy")
        )
        if studyId == 0:
            studyId = studies[0].idstudy
        extractstudy = Extraction.objects.get(study__pk=studyId)
    except:
        messages.warning(
                request,
                "Something went wrong.\n You may not have any extracted features dataset to begin or the study you are requesting does not exist.",
        )
        return redirect("index")

    sfile = extractstudy.study.directory

    times = np.load(f"{sfile}.npz", allow_pickle=True)["timevector"]
    times = [datetime.timestamp(i) for i in times]
    targets = np.load(f"{sfile}.npz", allow_pickle=True)[
        "target"
    ].tolist()

    times0, times1, times2, times3 = process_data_for_spliting(times, targets)

    schannels = len(ast.literal_eval(extractstudy.channels))
    sfeatures = len([i.name for i in extractstudy.features.all()])
    sfilter = extractstudy.filter
    swindowsize = extractstudy.windowsize
    swindowstep = extractstudy.windowstep

    try:
        data = np.load(sfile + ".npz", allow_pickle=True)["data2d"]
        snsamples = data.shape[0]
        snfeatures = data.shape[1]
        del data
    except Exception:
        print(traceback.print_exc())
        snsamples = "NaN"
        snfeatures = "NaN"

    previousSplit = extractstudy.split_point if extractstudy.split_point is not None else "NaN"

    return render(
            request,
            "app/train_test.html",
            {
                "studyId"       : studyId,
                "studies"       : studies,
                "extractstudy"  : extractstudy,
                "times"         : times,
                "targets"       : targets,
                "times_target_0": times0,
                "times_target_1": times1,
                "times_target_2": times2,
                "times_target_3": times3,

                # INFO
                "schannels"     : schannels,
                "sfeatures"     : sfeatures,
                "sfilter"       : sfilter,
                "swindowsize"   : swindowsize,
                "swindowstep"   : swindowstep,
                "snfeatures"    : snfeatures,
                "snsamples"     : snsamples,
                "splitpoint"    : previousSplit,
            },
    )


def process_data_for_spliting(timestamps, targets):
    times_target_0 = []
    times_target_1 = []
    times_target_2 = []
    times_target_3 = []
    for i in range(len(targets)):
        if targets[i] == 0:
            times_target_0.append(timestamps[i])
        elif targets[i] == 1:
            times_target_1.append(timestamps[i])
        elif targets[i] == 2:
            times_target_2.append(timestamps[i])
        elif targets[i] == 3:
            times_target_3.append(timestamps[i])

    # DOWNSAMPLE
    times_target_0 = downsampling(times_target_0)

    return times_target_0, times_target_1, times_target_2, times_target_3


def downsampling(data: np.ndarray) -> np.ndarray:
    npoints = len(data)
    if npoints < 4000:
        k = npoints
    elif 4000 <= npoints <= 15000:
        k = npoints // 2
    elif 15000 <= npoints <= 30000:
        k = npoints // 6
    else:
        k = npoints // 8
    return random.sample(data, k)


def train_test_splitAsync(request):
    studyId = request.POST["studyId"]
    current_extraction = Extraction.objects.get(study__pk=studyId)
    try:
        times = np.load(f"{current_extraction.study.directory}.npz", allow_pickle=True)["timevector"]
        times = [datetime.timestamp(i) for i in times]
        targets = np.load(f"{current_extraction.study.directory}.npz", allow_pickle=True)["target"].tolist()

        times0, times1, times2, times3 = process_data_for_spliting(times, targets)
    except Exception:
        print(traceback.print_exc())

    schannels = len(ast.literal_eval(current_extraction.channels))
    sfeatures = len([i.name for i in current_extraction.features.all()])
    sfilter = current_extraction.filter
    swindowsize = current_extraction.windowsize
    swindowstep = current_extraction.windowstep
    sfile = current_extraction.study.directory

    previousSplit = current_extraction.split_point if current_extraction.split_point is not None else "NaN"

    try:
        data = np.load(sfile + ".npz", allow_pickle=True)["data2d"]
        snsamples = data.shape[0]
        snfeatures = data.shape[1]
    except Exception:
        print(traceback.print_exc())
        snsamples = "NaN"
        snfeatures = "NaN"

    return JsonResponse(
            {
                "studyId"       : studyId,
                "times"         : times,
                "targets"       : targets,
                "times_target_0": times0,
                "times_target_1": times1,
                "times_target_2": times2,
                "times_target_3": times3,
                "schannels"     : schannels,
                "sfeatures"     : sfeatures,
                "sfilter"       : sfilter,
                "swindowsize"   : swindowsize,
                "swindowstep"   : swindowstep,
                "snfeatures"    : snfeatures,
                "sfile"         : sfile,
                "snsamples"     : snsamples,
                "splitpoint"    : previousSplit,
            }

    )


def splitingData(request):
    # PERFORM SPLIT
    studyId = int(request.POST["study"])
    splitpoint = int(request.POST["splitpoint"])

    current_extraction = Extraction.objects.get(study__pk=studyId)

    # SAVE SPLIT POINT IN THE DATABASE
    current_extraction.split_point = splitpoint
    current_extraction.save()
    return JsonResponse({"status": "success"})


def createNormalization(request, studyId):
    """Create a new normalization study"""
    if request.method == "POST":
        if "studyId" in request.POST:
            return createNormalizationAsync(request)
        elif "setname" in request.POST:
            return normalizing(request)
    try:
        studies = Study.objects.filter(user=request.user).filter(completed=True)
        shared = Study.objects.filter(
                idstudy__in=hasaccess.objects.filter(user=request.user).values("study")
        ).filter(completed=True)
        studies = (
            (studies | shared).filter(type=Study.Type.EXTRACT).order_by("-datestudy").exclude(
                    extraction__split_point=None)
        )
        if studyId == 0:
            studyId = studies.first().idstudy
        extractstudy = Extraction.objects.get(study__pk=studyId)
    except:
        messages.warning(
                request,
                "Something went wrong.\n You may not have any extracted features dataset to begin or the study you are requesting does not exist.",
        )
        return redirect("index")
        # return redirect("createStudy", idpat="0")

    # PREVIOUS NORMALIZATION STUDIES
    normstudies = Normalization.objects.filter(extraction_study__pk=studyId).filter(
            study__user=request.user
    )
    normshared = Normalization.objects.filter(extraction_study__pk=studyId).filter(
            study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
    )
    normprevious = normstudies | normshared

    current_extraction = Extraction.objects.get(study__pk=studyId)
    schannels = ast.literal_eval(current_extraction.channels)
    sfeatures = [i.name for i in current_extraction.features.all()]
    sfilter = current_extraction.filter
    swindowsize = current_extraction.windowsize
    swindowstep = current_extraction.windowstep
    # snfeatures = sum([len(i) for i in ast.literal_eval(current_extraction.subfeats)]) * len(schannels)
    sfile = current_extraction.study.directory
    try:
        data = np.load(sfile + ".npz", allow_pickle=True)["data2d"]
        snsamples = data.shape[0]
        snfeatures = data.shape[1]
    except Exception:
        print(traceback.print_exc())
        snsamples = "NaN"
        snfeatures = "NaN"

    try:
        data = np.load((extractstudy.study.directory) + ".npz", allow_pickle=True)[
            "data"
        ]
        info = [
            ast.literal_eval(extractstudy.feats),
            ast.literal_eval(extractstudy.subfeats),
            ast.literal_eval(extractstudy.channels),
        ]
        stepminutes = 10
        timeRange = pd.date_range(
                start=Information.objects.filter(patient=extractstudy.study.patient)[
                    0
                ].startts,
                end=Information.objects.filter(patient=extractstudy.study.patient)[
                    4
                ].stopts,
                periods=data[0].shape[2],
        )
        step = len(
                [
                    timeRange.to_list().index(i)
                    for i in timeRange
                    if i <= timeRange[0] + timedelta(minutes=stepminutes)
                ]
        )
        [datalist, timeRangeList] = getFeatureDataPlot(data, 0, step, timeRange)

        return render(
                request,
                "app/createStudyNormalization.html",
                {
                    "studyId"    : studyId,
                    "studies"    : studies,
                    "previous"   : normprevious,
                    "schannels"  : schannels,
                    "sfeatures"  : sfeatures,
                    "sfilter"    : sfilter,
                    "swindowsize": swindowsize,
                    "swindowstep": swindowstep,
                    "snfeatures" : snfeatures,
                    "sfile"      : sfile,
                    "snsamples"  : snsamples,
                    "info"       : info,
                    "signal"     : datalist,
                    "signaltime" : timeRangeList,
                },
        )
    except Exception:
        print(traceback.format_exc())
        return render(
                request,
                "app/createStudyNormalization.html",
                {
                    "studyId"    : studyId,
                    "studies"    : studies,
                    "previous"   : normprevious,
                    "schannels"  : schannels,
                    "sfeatures"  : sfeatures,
                    "sfilter"    : sfilter,
                    "swindowsize": swindowsize,
                    "swindowstep": swindowstep,
                    "snfeatures" : snfeatures,
                    "sfile"      : sfile,
                    "snsamples"  : snsamples,
                },
        )


def createNormalizationAsync(request):
    studyId = request.POST["studyId"]
    current_extraction = Extraction.objects.get(study__pk=studyId)

    # PREVIOUS NORMALIZATION STUDIES
    normstudies = Normalization.objects.filter(extraction_study__pk=studyId).filter(
            study__user=request.user
    )
    normshared = Normalization.objects.filter(extraction_study__pk=studyId).filter(
            study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
    )
    normprevious = normstudies | normshared

    names = [i.study.name for i in normprevious]
    res = [i.study.user.username for i in normprevious]
    ids = [i.study.idstudy for i in normprevious]

    schannels = ast.literal_eval(current_extraction.channels)
    sfeatures = [i.name for i in current_extraction.features.all()]
    sfilter = current_extraction.filter
    swindowsize = current_extraction.windowsize
    swindowstep = current_extraction.windowstep
    sfile = current_extraction.study.directory
    try:
        data = np.load(sfile + ".npz", allow_pickle=True)["data2d"]
        snsamples = data.shape[0]
        snfeatures = data.shape[1]
    except Exception:
        print(traceback.print_exc())
        snsamples = "NaN"
        snfeatures = "NaN"

    try:
        data = np.load(sfile + ".npz", allow_pickle=True)["data"]
        info = [
            ast.literal_eval(current_extraction.feats),
            ast.literal_eval(current_extraction.subfeats),
            ast.literal_eval(current_extraction.channels),
        ]
        timeRange = pd.date_range(
                start=Information.objects.filter(patient=current_extraction.study.patient)[
                    0
                ].startts,
                end=Information.objects.filter(patient=current_extraction.study.patient)[
                    4
                ].stopts,
                periods=data[0].shape[2],
        )
        step = len(
                [
                    timeRange.to_list().index(i)
                    for i in timeRange
                    if i <= timeRange[0] + timedelta(minutes=10)
                ]
        )
        [datalist, timeRangeList] = getFeatureDataPlot(data, 0, step, timeRange)

        return JsonResponse(
                {
                    "studyId"    : studyId,
                    "names"      : names,
                    "res"        : res,
                    "ids"        : ids,
                    "schannels"  : schannels,
                    "sfeatures"  : sfeatures,
                    "sfilter"    : sfilter,
                    "swindowsize": swindowsize,
                    "swindowstep": swindowstep,
                    "snfeatures" : snfeatures,
                    "sfile"      : sfile,
                    "snsamples"  : snsamples,
                    "info"       : info,
                    "signal"     : datalist,
                    "signaltime" : timeRangeList,
                }
        )

    except Exception:
        print(traceback.print_exc())
        return JsonResponse(
                {
                    "studyId"    : studyId,
                    "names"      : names,
                    "res"        : res,
                    "ids"        : ids,
                    "schannels"  : schannels,
                    "sfeatures"  : sfeatures,
                    "sfilter"    : sfilter,
                    "swindowsize": swindowsize,
                    "swindowstep": swindowstep,
                    "snfeatures" : snfeatures,
                    "sfile"      : sfile,
                    "snsamples"  : snsamples,
                }
        )


def normalizing(request):
    studyId = request.POST["study"]
    method = request.POST["method"]
    givenname = (
        datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if len(request.POST["setname"]) == 0
        else request.POST["setname"].replace(" ", "_")
    )
    dir = os.path.join(
            "data",
            "features",
            f"user_{request.user.username}",
            f"normalization_{givenname}",
    )
    # VERIFY IF THE DIRECTORY EXISTS AND CREATE IT IF NOT
    os.makedirs(
            os.path.join("data", "features", f"user_{request.user.username}"), exist_ok=True
    )

    # CREATE THE STUDY OF TYPE NORMALIZATION
    new_study = Study(
            name=givenname,
            directory=dir,
            type=Study.Type.NORM,
            user=request.user,
            patient=Study.objects.get(pk=studyId).patient,
    )
    new_study.save()

    # UPDATE THE DIRECTORY OF THE STUDY TO INCLUDE THE STUDY ID
    new_dir = os.path.join(
            "data",
            "features",
            f"user_{request.user.username}",
            f"normalization_{new_study.idstudy}_{givenname}",
    )
    new_study.directory = new_dir
    new_study.save()

    print("\n\nNORMALIZING THE STUDY\n")
    print(
            f"\nFrom (extraction study): \n{studyId}\n"
            f"\nMethod: \n{method}\n"
            f"\nName: \n{new_study.name}\n"
            f"\nDirectory: \n{new_study.directory}\n"
    )

    # SEND IT TO THE QUEUE
    main.main.delay(
            [
                "normalize_study",
                request.user.id,
                [studyId, method, new_study.directory, new_study.idstudy],
            ]
    )

    return redirect("index")


@studyAcessAllowed
def normalizationStudyPage(request, studyId):
    try:
        normstudy = Normalization.objects.get(study__pk=studyId)
    except:
        messages.warning(
                request,
                "Something went wrong.\n A study with that ID does not exist or it is on queue.",
        )
        return redirect("index")

    if request.method == "POST":
        if "comment" in request.POST:
            comment = request.POST["comment"]
            study = normstudy.study
            new_comment = Comment(
                    content=comment, user=request.user, datecom=datetime.now(), study=study
            )
            new_comment.save()
            return redirect("normalizationStudy", studyId=study.idstudy)
        elif "todeleteid" in request.POST:
            return deleteComment(request)
        elif "shareuser" in request.POST:
            sharewith = request.POST["shareuser"]
            if sharewith == request.user.username:
                messages.warning(
                        request, "There's no need to share a study with yourself."
                )
            else:
                try:
                    new_sharing = hasaccess(
                            user=User.objects.get(username=sharewith),
                            study=Study.objects.get(pk=studyId),
                    )
                    new_sharing.save()
                    new_notification = Notification(
                            datenot=datetime.now(),
                            consumed=False,
                            description="User "
                                        + request.user.username
                                        + " shared one of his studies with you.",
                            user=User.objects.get(username=sharewith),
                    )
                    new_notification.save()
                    messages.info(
                            request,
                            "You have successfully shared your study with "
                            + sharewith
                            + ".",
                    )
                except IntegrityError as ie:
                    messages.warning(
                            request, "You have already shared with " + sharewith + "."
                    )
                except ObjectDoesNotExist as odne:
                    messages.warning(request, "User " + sharewith + " does not exist.")
                except Exception as e:
                    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                    message = template.format(type(e).__name__, e.args)
                    print(message)
        elif "setname" in request.POST:
            # RENAME THE STUDY
            newName = (
                datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                if len(request.POST["setname"]) == 0
                else request.POST["setname"].replace(" ", "_")
            )
            # NEW DIRECTORY
            dir = os.path.join(
                    "data",
                    "features",
                    f"user_{request.user.username}",
                    f"normalization_{normstudy.study.idstudy}_{newName}",
            )
            # RENAME THE FILES
            os.rename(
                    os.path.join(
                            "data",
                            "features",
                            f"user_{request.user.username}",
                            f"normalization_{normstudy.study.idstudy}_{normstudy.study.name}.npy",
                    ),
                    dir + ".npy",
            )
            # RENAME THE SCALERS
            os.rename(
                    os.path.join(
                            "data",
                            "features",
                            f"user_{request.user.username}",
                            f"normalization_{normstudy.study.idstudy}_{normstudy.study.name}_scalers.npy",
                    ),
                    dir + "_scalers.npy",
            )
            # SAVE THE NEW INFORMATIONS
            normstudy.study.name = newName
            normstudy.study.directory = dir
            normstudy.study.save()
            normstudy.model_dir = f"{dir}_scalers"
            normstudy.save()

    studies = Normalization.objects.filter(study__user=request.user)
    shared = Normalization.objects.filter(
            study__idstudy__in=hasaccess.objects.filter(user=request.user).values("study")
    )
    studies = (studies | shared).order_by("study_id")
    studiesid = [i.study.idstudy for i in studies]

    try:
        previous = (
            studiesid[studiesid.index(studyId) - 1]
            if studyId > 1
            else studies.last().study.idstudy
        )
        next = (
            studiesid[studiesid.index(studyId) + 1]
            if studyId < studies.last().study.idstudy
            else studies[0].study.idstudy
        )
    except:
        previous = studyId
        next = previous

    sharingwith = hasaccess.objects.filter(study__idstudy=studyId)
    comments = Comment.objects.filter(study__idstudy=studyId).order_by("-datecom")

    extractstudy = Normalization.objects.get(study__pk=studyId).extraction_study

    # FORWARD STUDIES
    selredstudies = SelectionReduction.objects.filter(
            extraction_study__pk=studyId
    ).filter(study__user=request.user)
    selredshared = SelectionReduction.objects.filter(
            extraction_study__pk=studyId
    ).filter(study__pk__in=hasaccess.objects.filter(user=request.user).values("study"))

    classifstudies = Classification.objects.filter(extraction_study__pk=studyId).filter(
            study__user=request.user
    )
    classifshared = Classification.objects.filter(extraction_study__pk=studyId).filter(
            study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
    )

    return render(
            request,
            "app/normalizationStudy.html",
            {
                "studyId"              : studyId,
                "study"                : normstudy,
                "extractstudy"         : extractstudy,
                "previous"             : previous,
                "next"                 : next,
                "sharing"              : sharingwith,
                "comments"             : comments,
                "selectionstudies"     : selredstudies | selredshared,
                "classificationstudies": classifstudies | classifshared,
            },
    )


def createSelRed(request, studyId):
    if request.method == "POST":
        if "studyId" in request.POST:
            return createSelRedAsync(request)
        elif "setname" in request.POST:
            return selectingreducing(request)

    # GET THE LIST OF STUDIES (EXTRACTIONS AND NORMALIZATIONS)
    try:
        studies = Study.objects.filter(user=request.user).filter(completed=True)
        shared = Study.objects.filter(
                idstudy__in=hasaccess.objects.filter(user=request.user).values("study")
        ).filter(completed=True)
        studies = (
            (studies | shared)
            .filter(Q(type=Study.Type.EXTRACT, extraction__split_point__isnull=False) | Q(type=Study.Type.NORM))
            .order_by("-datestudy")
        )

        # GET THE FIRST STUDY IF THE STUDY ID IS 0
        if studyId == "0":
            studyId = studies[0].idstudy
        studyinfo = Study.objects.get(idstudy=studyId)
    except:
        messages.warning(
                request,
                "Something went wrong.\n You may not have any extracted features dataset to begin or the study you are requesting does not exist.",
        )
        return redirect("index")
        # return redirect("createNormalizationStudy", studyId=0)

    # GET THE PREVIOUS SELECTION REDUCTION STUDIES
    if studyinfo.type == Study.Type.EXTRACT:  # EXTRACTION STUDY
        selredstudies = SelectionReduction.objects.filter(
                extraction_study__pk=studyId
        ).filter(study__user=request.user)
        selredshared = SelectionReduction.objects.filter(
                extraction_study__pk=studyId
        ).filter(
                study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
        )
        selredprevious = selredstudies | selredshared

        current_study = Extraction.objects.get(study__pk=studyId)
        sfile = current_study.study.directory

    else:  # NORMALIZATION STUDY
        selredstudies = SelectionReduction.objects.filter(
                normalization_study__pk=studyId
        ).filter(study__user=request.user)
        selredshared = SelectionReduction.objects.filter(
                normalization_study__pk=studyId
        ).filter(
                study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
        )
        selredprevious = selredstudies | selredshared

        current_study = Normalization.objects.get(study__pk=studyId).extraction_study
        sfile = Normalization.objects.get(study__pk=studyId).extraction_study.study.directory

    # CURRENT STUDY INFORMATION
    schannels = ast.literal_eval(current_study.channels)
    sfeatures = ast.literal_eval(current_study.feats)
    sfilter = current_study.filter
    swindowsize = current_study.windowsize
    swindowstep = current_study.windowstep
    snfeatures = np.load(f"{sfile}.npz", allow_pickle=True)["columns"].shape[0]
    columns = np.load(f"{sfile}.npz", allow_pickle=True)["columns"]

    # TO BUILD THE PLOT
    try:
        data = np.load(f"{sfile}.npz", allow_pickle=True)['data']  # Load the data in 4D
        snsamples = data[0].shape[2]  # Number of samples
        info = [
            ast.literal_eval(current_study.feats),
            ast.literal_eval(current_study.subfeats),
            ast.literal_eval(current_study.channels),
        ]
        stepminutes = 10
        timeRange = pd.date_range(
                start=Information.objects.filter(patient=current_study.study.patient)[
                    0
                ].startts,
                end=Information.objects.filter(patient=current_study.study.patient)[
                    4
                ].stopts,
                periods=data.shape[0],
        )
        step = len(
                [
                    timeRange.to_list().index(i)
                    for i in timeRange
                    if i <= timeRange[0] + timedelta(minutes=stepminutes)
                ]
        )
        [datalist, timeRangeList] = getFeatureDataPlot(data, 0, step, timeRange)

        return render(
                request,
                "app/createStudySelRed.html",
                {
                    "studies"    : studies,
                    "previous"   : selredprevious,
                    "studyId"    : int(studyId),
                    "info"       : info,
                    "schannels"  : schannels,
                    "sfeatures"  : sfeatures,
                    "sfilter"    : sfilter,
                    "swindowsize": swindowsize,
                    "swindowstep": swindowstep,
                    "snsamples"  : snsamples,
                    "snfeatures" : snfeatures,
                    "signal"     : datalist,
                    "signaltime" : timeRangeList,
                    "columns"    : columns,
                },
        )
    except Exception:
        print(traceback.format_exc())
        return render(
                request,
                "app/createStudySelRed.html",
                {
                    "studies"    : studies,
                    "previous"   : selredprevious,
                    "studyId"    : int(studyId),
                    "schannels"  : schannels,
                    "sfeatures"  : sfeatures,
                    "sfilter"    : sfilter,
                    "swindowsize": swindowsize,
                    "swindowstep": swindowstep,
                    "snsamples"  : "NaN",
                    "snfeatures" : snfeatures,
                    "columns"    : columns,
                },
        )


def createSelRedAsync(request):
    studyId = request.POST["studyId"]
    study = Study.objects.get(idstudy=studyId)
    if study.type == Study.Type.EXTRACT:
        current_study = Extraction.objects.get(study__pk=studyId)

        sfile = current_study.study.directory

        # PREVIOUS EXTRACTION STUDIES
        selredstudies = SelectionReduction.objects.filter(
                extraction_study__pk=studyId
        ).filter(study__user=request.user)
        selredshared = SelectionReduction.objects.filter(
                extraction_study__pk=studyId
        ).filter(
                study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
        )

    else:
        current_study = Normalization.objects.get(study__pk=studyId).extraction_study

        sfile = Normalization.objects.get(study__pk=studyId).extraction_study.study.directory

        # PREVIOUS NORMALIZATION STUDIES
        selredstudies = SelectionReduction.objects.filter(
                normalization_study__pk=studyId
        ).filter(study__user=request.user)
        selredshared = SelectionReduction.objects.filter(
                normalization_study__pk=studyId
        ).filter(
                study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
        )

    previous = selredstudies | selredshared
    names = [i.study.name for i in previous]
    res = [i.study.user.username for i in previous]
    ids = [i.study.idstudy for i in previous]

    schannels = ast.literal_eval(current_study.channels)
    sfeatures = ast.literal_eval(current_study.feats)
    sfilter = current_study.filter
    swindowsize = current_study.windowsize
    swindowstep = current_study.windowstep

    columns = list(np.load(f"{sfile}.npz", allow_pickle=True)["columns"])

    try:
        data = np.load(sfile + ".npz", allow_pickle=True)['data2d']
        snsamples = data.shape[0]
        snfeatures = data.shape[1]
    except Exception:
        print(traceback.print_exc())
        snsamples = "NaN"
        snfeatures = "NaN"

    stepminutes = 10
    try:
        data = np.load(f"{sfile}.npz", allow_pickle=True)['data']
        info = [
            ast.literal_eval(current_study.feats),
            ast.literal_eval(current_study.subfeats),
            ast.literal_eval(current_study.channels),
        ]
        timeRange = pd.date_range(
                start=Information.objects.filter(patient=current_study.study.patient)[
                    0
                ].startts,
                end=Information.objects.filter(patient=current_study.study.patient)[
                    4
                ].stopts,
                periods=data[0].shape[2],
        )
        step = len(
                [
                    timeRange.to_list().index(i)
                    for i in timeRange
                    if i <= timeRange[0] + timedelta(minutes=stepminutes)
                ]
        )
        [datalist, timeRangeList] = getFeatureDataPlot(data, 0, step, timeRange)
        return JsonResponse(
                {
                    "studyId"    : int(studyId),
                    "type"       : study.type,
                    "info"       : info,
                    "names"      : names,
                    "res"        : res,
                    "ids"        : ids,
                    "schannels"  : schannels,
                    "sfeatures"  : sfeatures,
                    "sfilter"    : sfilter,
                    "swindowsize": swindowsize,
                    "swindowstep": swindowstep,
                    "snfeatures" : snfeatures,
                    "sfile"      : sfile,
                    "snsamples"  : snsamples,
                    "signal"     : datalist,
                    "signaltime" : timeRangeList,
                    "columns"    : columns,
                }
        )
    except Exception:
        print(traceback.format_exc())
        info = [
            ast.literal_eval(current_study.feats),
            [],
            ast.literal_eval(current_study.channels),
        ]
        return JsonResponse(
                {
                    "studyId"    : int(studyId),
                    "type"       : study.type,
                    "info"       : info,
                    "names"      : names,
                    "res"        : res,
                    "ids"        : ids,
                    "schannels"  : schannels,
                    "sfeatures"  : sfeatures,
                    "sfilter"    : sfilter,
                    "swindowsize": swindowsize,
                    "swindowstep": swindowstep,
                    "snfeatures" : snfeatures,
                    "sfile"      : sfile,
                    "snsamples"  : snsamples,
                    "columns"    : columns,
                }
        )


def selectingreducing(request):
    study = request.POST["study"]
    datafeat = [i for i in request.POST.getlist("datafeat[]")]
    methods = [i for i in request.POST.getlist("methods[]")]
    methodsoptions = {
        k: v
        for x in [i for i in json.loads(request.POST["methodsoptions[][]"])]
        for k, v in x.items()
    }
    givenname = (
        datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if len(request.POST["setname"]) == 0
        else request.POST["setname"].replace(" ", "_")
    )
    dir = os.path.join(
            "data",
            "features",
            f"user_{request.user.username}",
            f"selectionreduction_{givenname}",
    )
    # VERIFY IF THE DIRECTORY EXISTS AND CREATE IT IF NOT
    os.makedirs(
            os.path.join("data", "features", f"user_{request.user.username}"), exist_ok=True
    )

    new_study = Study(
            name=givenname,
            directory=dir,
            type=Study.Type.SELRED,
            user=request.user,
            patient=Study.objects.get(pk=study).patient,
    )
    new_study.save()

    # CHANGE THE NAME OF THE DIRECTORY TO INCLUDE THE STUDY ID
    new_dir = os.path.join(
            "data",
            "features",
            f"user_{request.user.username}",
            f"selectionreduction_{new_study.idstudy}_{givenname}",
    )
    new_study.directory = new_dir
    new_study.save()

    print("\n\nSelecting Features | Reducing Dimension:")
    print(
            "From (extraction / normalization study):\n",
            study,
            "\nFeatures:\n",
            datafeat,
            "\nMethods:\n",
            methods,
            "\nMethodsoptions:\n",
            methodsoptions,
    )

    main.main.delay(
            [
                "selred_features",
                request.user.id,
                [
                    study,
                    datafeat,
                    methods,
                    methodsoptions,
                    new_study.directory,
                    new_study.idstudy,
                ],
            ]
    )
    return render(request, "app/home.html")


@studyAcessAllowed
def selredStudyPage(request, studyId):
    # GET THE STUDY ASSOCIATED WITH THE REQUEST
    studyId = int(studyId)
    try:
        selredstudy = SelectionReduction.objects.get(study__pk=studyId)
    except:
        messages.warning(
                request,
                "Something went wrong.\n A study with that ID does not exist or it is on queue.",
        )
        return redirect("index")

    if request.method == "POST":
        if "comment" in request.POST:
            comment = request.POST["comment"]
            study = selredstudy.study
            new_comment = Comment(
                    content=comment, user=request.user, datecom=datetime.now(), study=study
            )
            new_comment.save()
            return redirect("selredStudy", studyId=study.idstudy)
        elif "shareuser" in request.POST:
            sharewith = request.POST["shareuser"]
            if sharewith == request.user.username:
                messages.warning(
                        request, "There's no need to share a study with yourself."
                )
            else:
                try:
                    new_sharing = hasaccess(
                            user=User.objects.get(username=sharewith),
                            study=Study.objects.get(pk=studyId),
                    )
                    new_sharing.save()
                    new_notification = Notification(
                            datenot=datetime.now(),
                            consumed=False,
                            description="User "
                                        + request.user.username
                                        + " shared one of his studies with you.",
                            user=User.objects.get(username=sharewith),
                    )
                    new_notification.save()
                    messages.info(
                            request,
                            "You have successfully shared your study with "
                            + sharewith
                            + ".",
                    )
                except IntegrityError as ie:
                    messages.warning(
                            request, "You have already shared with " + sharewith + "."
                    )
                except ObjectDoesNotExist as odne:
                    messages.warning(request, "User " + sharewith + " does not exist.")
                except Exception as e:
                    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                    message = template.format(type(e).__name__, e.args)
                    print(message)
        elif "todeleteid" in request.POST:
            return deleteComment(request)
        else:
            print("\n\nEDITING THE STUDY\n")
            extractstudy = request.POST["study"]
            datafeat = [i for i in request.POST.getlist("datafeat[]")]
            methods = [i for i in request.POST.getlist("channels[]")]
            methodsoptions = {
                k: v
                for x in [i for i in json.loads(request.POST["methodsoptions[][]"])]
                for k, v in x.items()
            }
            givenname = (
                datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                if len(request.POST["setname"]) == 0
                else request.POST["setname"]
            )
            dir = os.path.join(
                    "data", "features", "selectionreduction_{}".format(givenname)
            )

            selredstudy.study.name = givenname
            selredstudy.study.directory = dir
            selredstudy.study.save()

            print("\n\n-> Updating SelectionReduction Study:")
            print(
                    "From (extraction study):\n",
                    extractstudy,
                    "\nFeatures:\n",
                    datafeat,
                    "\nMethods:\n",
                    methods,
                    "\nMethodsoptions:\n",
                    methodsoptions,
            )

            main.main.delay(
                    [
                        "update_selred_features",
                        request.user.id,
                        [
                            extractstudy,
                            datafeat,
                            methods,
                            methodsoptions,
                            dir,
                            selredstudy.study.idstudy,
                        ],
                    ]
            )

    studies = SelectionReduction.objects.filter(study__user=request.user)
    shared = SelectionReduction.objects.filter(
            study__idstudy__in=hasaccess.objects.filter(user=request.user).values("study")
    )
    studies = (studies | shared).order_by("study_id")
    studiesid = [i.study.idstudy for i in studies]

    try:
        previous = (
            studiesid[studiesid.index(studyId) - 1]
            if studyId > 1
            else studies.last().study.idstudy
        )
        next = (
            studiesid[studiesid.index(studyId) + 1]
            if studyId < studies.last().study.idstudy
            else studies[0].study.idstudy
        )
    except:
        previous = studyId
        next = studyId

    # ORIGIN STUDY (EXTRACTION OR NORMALIZATION)
    from_study = selredstudy.from_study

    # # TODO: Study parametres and results
    fromfeats = ast.literal_eval(selredstudy.feats)
    selection_method = selredstudy.selection_method
    reduction_method = selredstudy.reduction_method

    methodsoptions = dict(selredstudy.methodoptions2.values_list('name', 'value'))

    file = selredstudy.study.directory
    try:
        train_data = np.load(file + ".npz", allow_pickle=True)['train_data']
        train_data_info = train_data.shape

        test_data = np.load(file + ".npz", allow_pickle=True)['test_data']
        test_data_info = test_data.shape

    except:
        train_data_info = (float("NaN"), float("NaN"))
        test_data_info = (float("NaN"), float("NaN"))

    comments = Comment.objects.filter(study__idstudy=studyId).order_by("-datecom")
    sharingwith = hasaccess.objects.filter(study__idstudy=studyId)

    classifstudies = Classification.objects.filter(
            selection_reduction_study__pk=studyId
    ).filter(study__user=request.user)
    classifshared = Classification.objects.filter(
            selection_reduction_study__pk=studyId
    ).filter(study__pk__in=hasaccess.objects.filter(user=request.user).values("study"))

    classif_using = classifstudies | classifshared

    return render(
            request,
            "app/selredStudy.html",
            {
                "id"                   : studyId,
                "study"                : selredstudy,
                "from_study"           : from_study,
                "previous"             : previous,
                "next"                 : next,
                "sharing"              : sharingwith,
                "comments"             : comments,
                "classificationstudies": classif_using,
                "fromfeats"            : fromfeats,
                "selection_method"     : selection_method,
                "reduction_method"     : reduction_method,
                "methodoptions"        : methodsoptions,
                "train_data_info"      : train_data_info,
                "test_data_info"       : test_data_info,
            },
    )


def createClassification(request, studyId):
    if request.method == "POST":
        if "studyId" in request.POST:
            return createClassificationAsync(request)
        elif "setname" in request.POST:
            return classifying(request)

    # GET THE LIST OF STUDIES (EXTRACTIONS, NORMALIZATIONS AND SELECTION/REDUCTION)
    try:
        studies = Study.objects.filter(user=request.user).filter(completed=True)
        shared = Study.objects.filter(
                idstudy__in=hasaccess.objects.filter(user=request.user).values("study")
        ).filter(completed=True)
        studies = (
            (studies | shared)
            .filter(Q(type=Study.Type.EXTRACT, extraction__split_point__isnull=False) | Q(type=Study.Type.NORM) | Q(
                    type=Study.Type.SELRED))
            .order_by("-datestudy")
        )
        if studyId == "0":
            studyId = studies.first().idstudy
        studyinfo = Study.objects.get(pk=studyId)
    except:
        messages.warning(
                request,
                "Something went wrong.\n You may not have any dataset to begin or the study you are requesting does not exist.",
        )
        return redirect("index")
        # return redirect("createStudySelRed", studyId="0")

    # GET THE PREVIOUS STUDIES
    if studyinfo.type == Study.Type.EXTRACT:
        classifstudies = Classification.objects.filter(
                extraction_study__pk=studyId
        ).filter(study__user=request.user)
        classifshared = Classification.objects.filter(
                extraction_study__pk=studyId
        ).filter(
                study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
        )
        classifprevious = classifstudies | classifshared
    elif studyinfo.type == Study.Type.NORM:
        classifstudies = Classification.objects.filter(
                normalization_study__pk=studyId
        ).filter(study__user=request.user)
        classifshared = Classification.objects.filter(
                normalization_study__pk=studyId
        ).filter(
                study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
        )
        classifprevious = classifstudies | classifshared
    else:
        classifstudies = Classification.objects.filter(
                selection_reduction_study__pk=studyId
        ).filter(study__user=request.user)
        classifshared = Classification.objects.filter(
                selection_reduction_study__pk=studyId
        ).filter(
                study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
        )
        classifprevious = classifstudies | classifshared

    context = {
        "studyId" : int(studyId),
        "studies" : studies,
        "previous": classifprevious,
    }

    # GET THE STUDY INFORMATION
    if studyinfo.type == Study.Type.EXTRACT:
        study = Extraction.objects.get(study__pk=studyId)

        # INFO
        sfilter = study.filter
        swindowsize = study.windowsize
        swindowstep = study.windowstep
        schannels = len(ast.literal_eval(study.channels))

        sfile = study.study.directory
        try:
            data = np.load(sfile + ".npz", allow_pickle=True)['data2d']
            snsamples = study.split_point
            snsamples_test = data.shape[0] - snsamples
            snfeatures = data.shape[1]
            columns = np.load(f"{sfile}.npz", allow_pickle=True)["columns"].tolist()
        except:
            snsamples = "NaN"
            snfeatures = "NaN"
            snsamples_test = "NaN"
            columns = []

        context.update({
            "study"         : study,
            "snfeatures"    : snfeatures,
            "snsamples"     : snsamples,
            "snsamples_test": snsamples_test,
            "sfilter"       : sfilter,
            "swindowsize"   : swindowsize,
            "swindowstep"   : swindowstep,
            "schannels"     : schannels,
            "columns"       : columns,
        })
    elif studyinfo.type == Study.Type.NORM:
        study = Normalization.objects.get(study__pk=studyId)

        # INFO
        smethod = [study.method]
        sfile = study.study.directory
        try:
            data = np.load(sfile + ".npz", allow_pickle=True)['train_data']
            snsamples = data.shape[0]
            snfeatures = data.shape[1]
            snsamples_test = np.load(sfile + ".npz", allow_pickle=True)['test_data'].shape[0]
            columns = np.load(f"{sfile}.npz", allow_pickle=True)["columns"].tolist()
        except:
            snsamples = "NaN"
            snfeatures = "NaN"
            snsamples_test = "NaN"
            columns = []

        context.update({
            "study"         : study,
            "snfeatures"    : snfeatures,
            "snsamples"     : snsamples,
            "snsamples_test": snsamples_test,
            "smethod"       : smethod,
            "columns"       : columns,
        })
    else:
        study = SelectionReduction.objects.get(study__pk=studyId)

        # INFO
        smethod = [method for method in [study.selection_method, study.reduction_method] if method is not None]
        sfile = study.study.directory
        try:
            data = np.load(sfile + ".npz", allow_pickle=True)['train_data']
            snsamples = data.shape[0]
            snfeatures = data.shape[1]
            snsamples_test = np.load(sfile + ".npz", allow_pickle=True)['test_data'].shape[0]
            columns = np.load(f"{sfile}.npz", allow_pickle=True)["columns"].tolist()
        except:
            snsamples = "NaN"
            snfeatures = "NaN"
            snsamples_test = "NaN"
            columns = []

        context.update({
            "study"         : study,
            "snfeatures"    : snfeatures,
            "snsamples"     : snsamples,
            "snsamples_test": snsamples_test,
            "smethod"       : smethod,
            "columns"       : columns,
        })

    return render(request,
                  "app/createStudyClassification.html",
                  context)


def createClassificationAsync(request):
    studyId = request.POST["studyId"]
    studyinfo = Study.objects.get(pk=studyId)
    context = {
        "studyId": int(studyId),
    }

    if studyinfo.type == Study.Type.EXTRACT:
        # EXTRACTION STUDY INFO
        study = Extraction.objects.get(study__pk=studyId)
        sfilter = study.filter
        swindowsize = study.windowsize
        swindowstep = study.windowstep
        schannels = len(ast.literal_eval(study.channels))

        sfile = study.study.directory
        try:
            data = np.load(sfile + ".npz", allow_pickle=True)['data2d']
            columns = np.load(f"{sfile}.npz", allow_pickle=True)["columns"].tolist()
            snsamples = study.split_point
            snsamples_test = data.shape[0] - snsamples
            snfeatures = data.shape[1]
        except:
            snsamples = "NaN"
            snfeatures = "NaN"
            snsamples_test = "NaN"
            columns = []

        context.update({
            "snfeatures"    : snfeatures,
            "snsamples"     : snsamples,
            "snsamples_test": snsamples_test,
            "sfilter"       : sfilter,
            "swindowsize"   : swindowsize,
            "swindowstep"   : swindowstep,
            "schannels"     : schannels,
            "columns"       : columns,
        })

        # PREVIOUS
        classifstudies = Classification.objects.filter(
                extraction_study__pk=studyId
        ).filter(study__user=request.user)
        classifshared = Classification.objects.filter(
                extraction_study__pk=studyId
        ).filter(
                study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
        )
    elif studyinfo.type == Study.Type.NORM:
        # NORMALIZATION STUDY INFO
        study = Normalization.objects.get(study__pk=studyId)

        smethod = [study.method.name]
        sfile = study.study.directory
        try:
            data = np.load(sfile + ".npz", allow_pickle=True)['train_data']
            snsamples = data.shape[0]
            snfeatures = data.shape[1]
            snsamples_test = np.load(sfile + ".npz", allow_pickle=True)['test_data'].shape[0]
            columns = np.load(f"{sfile}.npz", allow_pickle=True)["columns"].tolist()
        except:
            snsamples = "NaN"
            snfeatures = "NaN"
            snsamples_test = "NaN"
            columns = []

        context.update({
            "snfeatures"    : snfeatures,
            "snsamples"     : snsamples,
            "snsamples_test": snsamples_test,
            "smethod"       : smethod,
            "columns"       : columns,
        })

        # PREVIOUS
        classifstudies = Classification.objects.filter(
                normalization_study__pk=studyId
        ).filter(study__user=request.user)
        classifshared = Classification.objects.filter(
                normalization_study__pk=studyId
        ).filter(
                study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
        )
    else:
        # SELECTION REDUCTION STUDY INFO
        study = SelectionReduction.objects.get(study__pk=studyId)

        smethod = [method for method in [study.selection_method, study.reduction_method] if method is not None]
        sfile = study.study.directory
        try:
            data = np.load(sfile + ".npz", allow_pickle=True)['train_data']
            snsamples = data.shape[0]
            snfeatures = data.shape[1]
            snsamples_test = np.load(sfile + ".npz", allow_pickle=True)['test_data'].shape[0]
            columns = np.load(f"{sfile}.npz", allow_pickle=True)["columns"].tolist()
        except:
            snsamples = "NaN"
            snfeatures = "NaN"
            snsamples_test = "NaN"
            columns = []

        context.update({
            "snfeatures"    : snfeatures,
            "snsamples"     : snsamples,
            "snsamples_test": snsamples_test,
            "smethod"       : smethod,
            "columns"       : columns,
        })
        # PREVIOUS
        classifstudies = Classification.objects.filter(
                selection_reduction_study__pk=studyId
        ).filter(study__user=request.user)
        classifshared = Classification.objects.filter(
                selection_reduction_study__pk=studyId
        ).filter(
                study__pk__in=hasaccess.objects.filter(user=request.user).values("study")
        )

    names = [i.study.name for i in (classifstudies | classifshared)]
    res = [i.study.user.username for i in (classifstudies | classifshared)]
    ids = [i.study.idstudy for i in (classifstudies | classifshared)]

    context.update({
        "names": names,
        "res"  : res,
        "ids"  : ids,
    })
    return JsonResponse(context)


def classifying(request):
    study = request.POST["study"]
    data = [i for i in request.POST.getlist("data[]")]
    method = request.POST["method"]
    methodoptions = {
        k: v
        for x in [i for i in json.loads(request.POST["methodoptions[][]"])]
        for k, v in x.items()
    }
    givenname = (
        datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if len(request.POST["setname"]) == 0
        else request.POST["setname"].replace(" ", "_")
    )
    dir = os.path.join(
            "data",
            "results",
            f"user_{request.user.username}",
            f"classification_{givenname}")

    # VERIFY IF DIRECTORY EXISTS
    os.makedirs(os.path.join("data", "results", f"user_{request.user.username}"), exist_ok=True)

    # CREATE THE STUDY
    new_study = Study(
            name=givenname,
            directory=dir,
            type=Study.Type.CLASSIF,
            user=request.user,
            patient=Study.objects.get(pk=study).patient,
    )
    new_study.save()

    # CHANGE THE NAME OF DIRECTORY TO INCLIDE THE STUDY ID
    new_dir = os.path.join(
            "data",
            "results",
            f"user_{request.user.username}",
            f"classification_{new_study.idstudy}_{givenname}"
    )

    new_study.directory = new_dir
    new_study.save()

    print("\n\nClassifying:")
    print(
            "From:\n",
            study,
            "\nData:\n",
            data,
            "\nMethod:\n",
            method,
            "\nMethodoptions:\n",
            methodoptions,
    )

    main.main.delay(
            [
                "classify_study",
                request.user.id,
                [
                    study,
                    data,
                    method,
                    methodoptions,
                    new_study.directory,
                    new_study.idstudy
                ],
            ]
    )
    return redirect("index")


@studyAcessAllowed
def classificationStudyPage(request, studyId):
    if request.method == "POST":
        if "comment" in request.POST:
            comment = request.POST["comment"]
            study = Study.objects.get(idstudy=studyId)
            new_comment = Comment(
                    content=comment, user=request.user, datecom=datetime.now(), study=study
            )
            new_comment.save()
            return redirect("classificationStudy", studyId=study.idstudy)
        elif "shareuser" in request.POST:
            sharewith = request.POST["shareuser"]
            if sharewith == request.user.username:
                messages.warning(
                        request, "There's no need to share a study with yourself."
                )
            else:
                try:
                    new_sharing = hasaccess(
                            user=User.objects.get(username=sharewith),
                            study=Study.objects.get(pk=studyId),
                    )
                    new_sharing.save()
                    new_notification = Notification(
                            datenot=datetime.now(),
                            consumed=False,
                            description="User "
                                        + request.user.username
                                        + " shared one of his studies with you.",
                            user=User.objects.get(username=sharewith),
                    )
                    new_notification.save()
                    messages.info(
                            request,
                            "You have successfully shared your study with "
                            + sharewith
                            + ".",
                    )
                except IntegrityError as ie:
                    messages.warning(
                            request, "You have already shared with " + sharewith + "."
                    )
                except ObjectDoesNotExist as odne:
                    messages.warning(request, "User " + sharewith + " does not exist.")
                except Exception as e:
                    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                    message = template.format(type(e).__name__, e.args)
                    print(message)
        elif "todeleteid" in request.POST:
            return deleteComment(request)
        else:
            print("\n\nEDITING THE STUDY\n")
            classifstudy = Classification.objects.get(study__idstudy=studyId)

            from_study = request.POST["study"]
            data = [i for i in request.POST.getlist("data[]")]
            method = [i for i in request.POST.getlist("method")]
            methodoptions = {
                k: v
                for x in [i for i in json.loads(request.POST["methodoptions[][]"])]
                for k, v in x.items()
            }
            givenname = (
                datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                if len(request.POST["setname"]) == 0
                else request.POST["setname"]
            )
            dir = os.path.join("data", "results", "classification_{}".format(givenname))

            classifstudy.study.name = givenname
            classifstudy.study.directory = dir
            classifstudy.study.save()

            print("\n\n-> Updating Classifcation Study:")
            print(
                    "From:\n",
                    from_study,
                    "\nData:\n",
                    data,
                    "\nMethod:\n",
                    method,
                    "\nMethodoptions:\n",
                    methodoptions,
            )

            main.main.delay(
                    [
                        "update_classify",
                        request.user.id,
                        [
                            from_study,
                            data,
                            method,
                            methodoptions,
                            dir,
                            classifstudy.study.idstudy,
                        ],
                    ]
            )

    studyId = int(studyId)
    try:
        classifstudy = Classification.objects.get(study__pk=studyId)
    except:
        messages.warning(
                request,
                "Something went wrong.\n A study with that ID does not exist or it is on queue.",
        )
        return redirect("index")

    studies = Classification.objects.filter(study__user=request.user)
    shared = Classification.objects.filter(
            study__idstudy__in=hasaccess.objects.filter(user=request.user).values("study")
    )
    studies = (studies | shared).order_by("study_id")
    studiesid = [i.study.idstudy for i in studies]

    previous = (
        studiesid[studiesid.index(studyId) - 1]
        if studyId > 1
        else studies.last().study.idstudy
    )
    next = (
        studiesid[studiesid.index(studyId) + 1]
        if studyId < studies.last().study.idstudy
        else studies[0].study.idstudy
    )

    from_studyInfo = []
    from_study = Classification.objects.get(study__pk=studyId).from_study

    # try:
    #     sm = [from_study.selection_method, from_study.reduction_method]
    #     # from_studyInfo = [
    #     #     ast.literal_eval(from_study.feats),
    #     #     ast.literal_eval(from_study.subfeats),
    #     #     ast.literal_eval(from_study.channels),
    #     # ]
    # except:
    #     from_study = Classification.objects.get(
    #             study__pk=studyId
    #     ).selection_reduction_study
    #     # from_studyInfo = [ast.literal_eval(from_study.feats)]

    # TODO: Study parametres and results
    fromfeats = ast.literal_eval(classifstudy.feats)
    methodsoptions = ast.literal_eval(classifstudy.methodoptions)
    nclasses = methodsoptions['nclasses']


    file = classifstudy.study.directory
    print(f"File: {file}")
    try:
        data = np.load(file + ".npz", allow_pickle=True)['test_data']
        print(data.shape)
        info = list(data.shape)
    except:
        info = [float("NaN"), float("NaN"), float("NaN"), float("NaN")]

    comments = Comment.objects.filter(study__idstudy=studyId).order_by("-datecom")
    sharingwith = hasaccess.objects.filter(study__idstudy=studyId)

    return render(
            request,
            "app/classificationStudy.html",
            {
                "id"            : studyId,
                "study"         : classifstudy,
                "from_study"    : from_study,
                "from_studyInfo": from_studyInfo,
                "previous"      : previous,
                "next"          : next,
                "sharing"       : sharingwith,
                "comments"      : comments,
                "nsamples"      : info[0],
                "nfeats"        : info[1],
                "nclasses"      : nclasses,
                "fromfeats"     : fromfeats,
                "methodoptions" : methodsoptions,
            },
    )


# POST PROCESSING
def postprocessing(request, studyId):
    return render(request, "app/postprocessing.html")


def deleteComment(request):
    commentId = request.POST["todeleteid"]
    todelete = Comment.objects.get(idcom=commentId)
    todelete.delete()
    return JsonResponse({"id": commentId})


def checkTask(request, tid):
    noti = get_object_or_404(Notification.objects.select_related("study"), pk=tid)
    noti.consumed = True
    noti.save()
        
    try:
        noti = Notification.objects.get(pk=tid)
        noti.consumed = True
        noti.save()
    except:
        print("Notification not found.")
        return redirect("index")

    if "uploaded" in noti.description:
        return redirect("data")
    elif "Extraction" in noti.description:
        return redirect("extractionStudy", studyId=noti.study.idstudy)
    elif "Normalization" in noti.description:
        return redirect("normalizationStudy", studyId=noti.study.idstudy)
    elif "Selection" in noti.description:
        return redirect("selredStudy", studyId=noti.study.idstudy)
    elif "Classification" in noti.description:
        print(f"Notification for Classification {noti.study.idstudy}")
        return redirect("classificationStudy", studyId=noti.study.idstudy)
        #return classificationStudyPage(request, noti.study.idstudy)
    elif "patient data" in noti.description:
        return redirect("datav2", "rawdata")
    elif "studies" in noti.description:
        return redirect("datav2", "studies")
    else:
        return redirect("index")


def checkTaskResult(request, id):
    return None


def handler404(request, exception):
    print(exception)
    return render(request, "app/404.html", status=404)


def handler500(request):
    return render(request, "app/500.html")


class DateTimeEncoder(json.JSONEncoder):
    def default(firstwindow, z):
        if isinstance(z, datetime):
            return z.strftime("%d/%m/%Y, %H:%M")
        else:
            return super().default(z)


@studyAcessAllowed
def studyPage(request, studyId):
    """
    View to render the study page. It will render the page according to the study type.
    """
    studyId = int(studyId)
    try:
        study = Study.objects.get(pk=studyId)
    except:
        messages.warning(
                request, "Something went wrong.\n A study with that ID does not exist."
        )
        return redirect("index")

    if study.type == Study.Type.EXTRACT:
        return redirect("extractionStudy", studyId=studyId)
    elif study.type == Study.Type.NORM:
        return redirect("normalizationStudy", studyId=studyId)
    elif study.type == Study.Type.SELRED:
        return redirect("selredStudy", studyId=studyId)
    elif study.type == Study.Type.CLASSIF:
        return redirect("classificationStudy", studyId=studyId)

    return redirect("index")


# Views to Upload new External Features
@login_required(login_url="landing")
def uploadExternalFeature(request):
    if request.method == "POST":
        form = UploadExternalFeatureForm(request.POST, request.FILES)
        print(request.POST["type"])
        if form.is_valid():
            print("Formulário Válido")
            file = request.FILES["file"]

            file_name = f"[{request.user.id}]{request.POST['function_name']}.py"
            print(file_name)

            # Gravar o Ficheiro
            with open("data/externalfeatures/" + file_name, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            # Guardar a feature na base de dados
            feat = ExternalFeature(
                    user=request.user,
                    name=request.POST["name"],
                    function_name=request.POST["function_name"],
                    type=request.POST["type"],
                    path=os.path.join("data", "externalfeatures", file_name),
            )
            feat.save()
            return redirect("index")
    else:
        form = UploadExternalFeatureForm()
    return render(request, "app/uploadFeature.html", {"form": form})
