import ast
import time
from datetime import datetime

from celery import shared_task

from app.models import *
from epilab.classification import classification
from epilab.extractFeatures import extractFeatures
from epilab.selredFeatures import selredFeatures
from epilab.normalization import normalizeStudy


@shared_task(name="main")
def main(q):
    task = q[0]
    us = User.objects.get(pk=q[1])  # User

    if "extract" in task:
        config = q[2]

        patient = config[0]
        sampFreq = config[1]
        channels = config[2]
        filter = config[3]
        filteroptions = config[4]
        window = config[5][0]
        step = config[5][1]
        features = config[6]
        featsoptions = config[7]
        dir = config[8]
        study = config[9]
        SPH = config[10]
        SOP = config[11]

        if task == "extract_features":
            study = Study.objects.get(idstudy=study)
            study.completed = False
            study.save()

            # CREATE EXTRACTION STUDY
            new_extraction = Extraction(
                    study=study,
                    channels=channels,
                    filter=filter,
                    windowsize=window,
                    windowstep=step,
                    feats=features,
                    featsoptions=featsoptions,
                    SPH = int(SPH),
                    SOP = int(SOP),
            )
            if filter != "none":
                new_extraction.filter_cutoff = filteroptions[0]
                new_extraction.filter_order = filteroptions[1]
            new_extraction.save()
            # ADD FEATURES TO EXTRACTION
            for feat in features:
                feature = Feature.objects.get(name=feat)
                new_extraction.features.add(feature)
            # ADD CHANNELS TO EXTRACTION
            for ch in channels:
                try:  # CHECK IF CHANNEL EXISTS IN DATABASE AND ADD IT TO THE EXTRACTION
                    channel = Channel.objects.get(val=ch)
                    new_extraction.channs.add(channel)
                except Channel.DoesNotExist:  # IF CHANNEL DOES NOT EXIST, CREATE IT AND ADD IT TO THE EXTRACTION
                    new_channel = Channel(val=ch)
                    new_channel.save()
                    new_extraction.channs.add(new_channel)
            subfeats = extractFeatures(
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
            )

            new_extraction.subfeats = str([subfeats[i] for i in features])
            new_extraction.save()

            new_notification = Notification(
                    datenot=datetime.now(),
                    consumed=False,
                    description="Feature Extraction completed.",
                    study=study,
                    user=us,
            )
            new_notification.save()

            study.completed = True
            study.save()
            pass
        if task == "update_extract_features":
            study = Extraction.objects.get(study__idstudy=study)
            study.study.completed = False
            study.study.save()
            if (
                    all(x in channels for x in ast.literal_eval(study.channels))
                    and all(x in features for x in ast.literal_eval(study.feats))
                    and int(study.windowsize) == int(window)
                    and int(study.windowstep) == int(step)
                    and filter == study.filter
                    and filteroptions == [study.filter_cutoff, study.filter_order]
            ):
                if set(channels) != set(ast.literal_eval(study.channels)) and set(
                        features
                ) != set(ast.literal_eval(study.feats)):
                    new_channels = [
                        x for x in channels if x not in ast.literal_eval(study.channels)
                    ]
                    new_feats = [
                        x for x in features if x not in ast.literal_eval(study.feats)
                    ]
                    print("ADDING CHANNELS AND FEATURES", new_channels, new_feats)

                    updateflag = "ADDING CHANNELS"
                    c = ast.literal_eval(study.channels)
                    for i in new_channels:
                        c.append(i)
                    study.channels = c
                    features = ast.literal_eval(study.feats)
                    channels = new_channels
                    subfeats = extractFeatures(
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
                            updateflag,
                    )

                    study.save()

                    updateflag = "ADDING FEATURES"
                    f = ast.literal_eval(study.feats)
                    for i in new_feats:
                        f.append(i)
                    study.feats = f
                    features = new_feats
                    subfeats = extractFeatures(
                            patient,
                            sampFreq,
                            c,
                            filter,
                            filteroptions,
                            window,
                            step,
                            features,
                            featsoptions,
                            dir,
                            updateflag,
                    )
                    subfeats_old = ast.literal_eval(study.subfeats)
                    for i in features:
                        subfeats_old.append(subfeats[i])
                    print("\n\n", subfeats_old, features)
                    study.subfeats = subfeats_old

                    study.save()
                    updateflag = "ADDING CHANNELS AND FEATURES"
                elif set(channels) != set(ast.literal_eval(study.channels)):
                    new_channels = [
                        x for x in channels if x not in ast.literal_eval(study.channels)
                    ]
                    updateflag = "ADDING CHANNELS"
                    print(updateflag, new_channels)
                    c = ast.literal_eval(study.channels)
                    for i in new_channels:
                        c.append(i)
                    study.channels = c
                    features = ast.literal_eval(study.feats)
                    channels = new_channels
                    study.save()
                elif set(features) != set(ast.literal_eval(study.feats)):
                    new_feats = [
                        x for x in features if x not in ast.literal_eval(study.feats)
                    ]
                    updateflag = "ADDING FEATURES"
                    print(updateflag, new_feats)
                    f = ast.literal_eval(study.feats)
                    for i in new_feats:
                        f.append(i)
                    study.feats = f
                    features = new_feats
                    study.save()
                else:
                    study.study.completed = True
                    study.study.save()
                    return
            else:
                updateflag = "REDOING THE STUDY"
                study.channels = channels
                study.filter = filter
                study.filter_cutoff = filteroptions[0]
                study.filter_order = filteroptions[1]
                study.windowsize = int(window)
                study.windowstep = int(step)
                study.feats = features
                study.featsoptions = featsoptions
                study.save()

            if "ADDING CHANNELS AND FEATURES" not in updateflag:
                subfeats = extractFeatures(
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
                        updateflag,
                )
                if "FEATURES" in updateflag:
                    subfeats_old = ast.literal_eval(study.subfeats)
                    for i in features:
                        subfeats_old.append(subfeats[i])
                    print("\n\n", subfeats_old, features)
                    study.subfeats = subfeats_old
            elif "REDOING" in updateflag:
                subfeats = extractFeatures(
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
                        updateflag,
                )
                study.subfeats = [subfeats[i] for i in features]

            study.save()

            new_notification = Notification(
                    datenot=datetime.now(),
                    consumed=False,
                    description="Feature Extraction Study update completed.",
                    study=study.study,
                    user=us,
            )
            new_notification.save()

            study.study.completed = True
            study.study.save()
            pass

    if "normalize" in task:
        config = q[2]

        extraction_study = config[0]
        method = config[1]
        dir = config[2]
        study = config[3]

        if task == "normalize_study":
            # Update the study status to indicate the study is being processed
            study = Study.objects.get(idstudy=study)
            study.completed = False
            study.save()

            extraction_study = Extraction.objects.get(study__idstudy=int(extraction_study))

            # NEW NORMALIZATION STUDY
            new_normalization = Normalization(
                    method=NormalizationMethod.objects.get(pk=method),
                    study=study,
                    extraction_study=extraction_study,
            )
            new_normalization.save()

            # NORMALIZE STUDY
            model_dir = normalizeStudy(extraction_study, method, dir)

            # SAVE MODEL DIRECTORY
            new_normalization.model_dir = model_dir
            new_normalization.save()

            # CREATE NOTIFICATION
            new_notification = Notification(
                    consumed=False,
                    description="Normalization Study completed.",
                    study=study,
                    user=us,
            )
            new_notification.save()

            # Update the study status to indicate the study is completed
            study.completed = True
            study.save()
            pass

    if "selred" in task:
        config = q[2]

        from_studyId = config[0]
        feats = config[1]
        method = config[2]
        selection = method[0] if method[0] != "" else None
        reduction = method[1] if method[1] != "" else None
        methodoptions = config[3]
        dir = config[4]
        study = config[5]

        if task == "selred_features":
            study = Study.objects.get(idstudy=study)
            study.completed = False
            study.save()

            from_study_1 = Study.objects.get(pk=from_studyId)
            if from_study_1.type == Study.Type.EXTRACT:
                from_study = Extraction.objects.get(study__idstudy=int(from_studyId))

                # NEW SELECTION REDUCTION STUDY
                new_selred = SelectionReduction(
                        feats=feats,
                        selection_method=selection,
                        reduction_method=reduction,
                        methodoptions=methodoptions,
                        study=study,
                        extraction_study=from_study,
                )
                new_selred.save()

                for opt in methodoptions:
                    try:
                        option = Options.objects.get(name=opt, value=methodoptions[opt])
                        new_selred.methodoptions2.add(option)
                    except Options.DoesNotExist:
                        option = Options(name=opt, value=methodoptions[opt])
                        option.save()
                        new_selred.methodoptions2.add(option)

                # SELECTION REDUCTION
                model_dir = selredFeatures(from_study, feats, method, methodoptions, dir)

                # SAVE MODEL DIRECTORY
                new_selred.model_dir = model_dir
                new_selred.save()
            else:
                from_study = Normalization.objects.get(study__idstudy=int(from_studyId))

                # NEW SELECTION REDUCTION STUDY
                new_selred = SelectionReduction(
                        feats=feats,
                        selection_method=selection,
                        reduction_method=reduction,
                        methodoptions=methodoptions,
                        study=study,
                        normalization_study=from_study,
                )
                new_selred.save()

                for opt in methodoptions:
                    try:
                        option = Options.objects.get(name=opt, value=methodoptions[opt])
                        new_selred.methodoptions2.add(option)
                    except Options.DoesNotExist:
                        option = Options(name=opt, value=methodoptions[opt])
                        option.save()
                        new_selred.methodoptions2.add(option)

                # SELECTION REDUCTION
                model_dir = selredFeatures(from_study, feats, method, methodoptions, dir)

                # SAVE MODEL DIRECTORY
                new_selred.model_dir = model_dir
                new_selred.save()

            # CREATE NOTIFICATION
            new_notification = Notification(
                    consumed=False,
                    description=f"Feature Selection/ Dimensionality Reduction {new_selred.study.idstudy} completed.",
                    study=study,
                    user=us,
            )
            new_notification.save()

            # Update the study status to indicate the study is completed
            study.completed = True
            study.save()
            pass
        else:
            study = SelectionReduction.objects.get(study__pk=study)
            study.study.completed = False
            study.study.save()

            time.sleep(5)
            # TODO: Implement Here - Change in Study SelRed

            new_notification = Notification(
                    datenot=datetime.now(),
                    consumed=False,
                    description="Feature Selection/Dimensionality Reduction Study update completed.",
                    study=study.study,
                    user=us,
            )
            new_notification.save()

            study.study.completed = True
            study.study.save()
            pass

    if "classify" in task:
        config = q[2]

        from_studyId = config[0]
        feats = config[1]
        method = config[2]
        methodoptions = config[3]
        dir = config[4]
        study = config[5]

        if task == "classify_study":
            study = Study.objects.get(idstudy=study)
            from_study = Study.objects.get(pk=from_studyId)

            #CREATE NEW CLASSIFICATION
            new_classif = Classification(
                    method=method,
                    methodoptions=methodoptions,
                    study=study,
                    feats=feats,
            )
            new_classif.save()
            if from_study.type == Study.Type.EXTRACT:
                from_study = Extraction.objects.get(study__idstudy=int(from_studyId))
                new_classif.extraction_study = from_study
            elif from_study.type == Study.Type.NORM:
                from_study = Normalization.objects.get(study__idstudy=int(from_studyId))
                new_classif.normalization_study = from_study
            else:
                from_study = SelectionReduction.objects.get(study__idstudy=int(from_studyId))
                new_classif.selection_reduction_study = from_study
            new_classif.save()

            study.completed = False
            study.save()

            classification(new_classif ,from_study, feats, method, methodoptions, dir)

            new_notification = Notification(
                    consumed=False,
                    description=f"{new_classif} completed.",
                    study=study,
                    user=us,
            )
            new_notification.save()

            study.completed = True
            study.save()
            pass
        else:
            study = Classification.objects.get(study__idstudy=study)
            study.study.completed = False
            study.study.save()

            time.sleep(5)

            new_notification = Notification(
                    datenot=datetime.now(),
                    consumed=False,
                    description="Classification Study update completed.",
                    study=study.study,
                    user=us,
            )
            new_notification.save()

            study.study.completed = True
            study.study.save()
            pass
