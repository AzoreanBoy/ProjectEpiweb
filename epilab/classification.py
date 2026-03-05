import sys
import pandas as pd
import numpy as np
import pickle
import ast
from joblib import dump, load

from sklearn.svm import SVC
from sklearn import metrics

from imblearn.under_sampling import RandomUnderSampler

from app.models import *
from epilab import *
from epilab.postprocessing import postprocessing


def classification(classification_study ,from_study, feats, method, methodoptions, dir):
    print("\n" + "-" * 50 + f"\nCLASSIFICATION\n" + "-" * 50 + "\n")
    file = np.load(f"{from_study.study.directory}.npz", allow_pickle=True)
    if Study.objects.get(pk=from_study.study.idstudy).type == Study.Type.EXTRACT:
        # DATA SPLITING
        data = file["data2d"]
        targets = file["target"]
        timevector = file["timevector"]

        # DATA SPLITING INTO TRAINING AND TESTING
        splitpoint = from_study.split_point

        train_data = data[:splitpoint]
        test_data = data[splitpoint:]

        train_targets = targets[:splitpoint]
        test_targets = targets[splitpoint:]

        train_timevector = timevector[:splitpoint]
        test_timevector = timevector[splitpoint:]

        columns = file['columns']

        # MODEL
        model = []
    elif Study.objects.get(pk=from_study.study.idstudy).type == Study.Type.NORM:
        train_data = file["train_data"]
        test_data = file["test_data"]

        train_targets = file["train_targets"]
        test_targets = file["test_targets"]

        train_timevector = file["train_timevector"]
        test_timevector = file["test_timevector"]

        columns = file['columns']

        model = load(from_study.model_dir)
    else:
        train_data = file["train_data"]
        test_data = file["test_data"]

        train_targets = file["train_targets"]
        test_targets = file["test_targets"]

        train_timevector = file["train_timevector"]
        test_timevector = file["test_timevector"]

        columns = file["columns"]

        model = load(from_study.model_dir)

    nclasses = int(methodoptions["nclasses"])
    if nclasses == 2:
        # PROCESS TARGET VECTORS TO ONLY VALUES 1 (SPH INTERVAL) AND 0 (NON-SPH INTERVAL)
        train_targets = np.array([1 if x == 1 else 0 for x in train_targets])
        test_targets = np.array([1 if x == 1 else 0 for x in test_targets])

    # SELECT ONLY DATA USER WANTS
    train_data = pd.DataFrame(data=train_data, columns=columns)[feats].to_numpy()
    test_data = pd.DataFrame(data=test_data, columns=columns)[feats].to_numpy()
    columns = feats
    model.append(columns)

    # --------------------------------
    #       UNDER/OVER SAMPLING
    # --------------------------------
    # DEFAULT WILL BE UNDER SAMPLING
    train_data, train_targets = RandomUnderSampler(random_state=0).fit_resample(train_data, train_targets)

    # TODO: Implement more Classification Algorithms
    # --------------------------
    #       CLASSIFICATION
    # --------------------------
    if "SVM" in method:
        print("\n" + "-" * 50 + f"\nSVM CLASSIFICATION\n" + "-" * 50 + "\n")
        clf = None
        # nclasses = int(methodoptions["nclasses"])
        kernel = methodoptions["SVMKernel"]
        params = {"kernel": kernel,
                  "C": float(methodoptions["SVMC"]),}

        if kernel == 'linear':
            # PARAMETERS
            #params['C'] = float(methodoptions["SVMC"])
            if methodoptions["use_maxiter"]:
                params['max_iter'] = int(methodoptions["SVMmaxIter"])

        elif kernel == 'rbf':
            # PARAMETERS
            #params['C'] = float(methodoptions["SVMC"])
            if methodoptions["use_maxiter"]:
                params['max_iter'] = int(methodoptions["SVMmaxIter"])
            if methodoptions["use_gamma"]:
                params['gamma'] = float(methodoptions["SVMgamma"])

        elif kernel == 'poly':
            # PARAMETERS
            #params['C'] = float(methodoptions["SVMC"])
            if methodoptions["use_maxiter"]:
                params['max_iter'] = int(methodoptions["SVMmaxIter"])
            if methodoptions["use_gamma"]:
                params['gamma'] = float(methodoptions["SVMgamma"])
            if methodoptions["use_coef0"]:
                params['coef0'] = float(methodoptions["SVMcoef0"])
            if methodoptions["use_degree"]:
                params['degree'] = int(methodoptions["SVMdegree"])

        elif kernel == 'sigmoid':
            # PARAMETERS
            #params['C'] = float(methodoptions["SVMC"])
            if methodoptions["use_maxiter"]:
                params['max_iter'] = int(methodoptions["SVMmaxIter"])
            if methodoptions["use_gamma"]:
                params['gamma'] = float(methodoptions["SVMgamma"])
            if methodoptions["use_coef0"]:
                params['coef0'] = float(methodoptions["SVMcoef0"])

        print("PARAMETERS: ", params)
        # CLASSIFIER
        clf = SVC(**params)

        # FIT THE MODEL
        clf.fit(X=train_data, y=train_targets)
        predictions = clf.predict(test_data)

        # SAVE THE MODEL
        model.append(clf)

    # JOBLIB MODEL SAVING
    model_dir = f"{dir}_model.joblib"
    dump(model, model_dir)

    # SAVE PREDICTION AND TRUE LABELS
    np.savez(
            dir,
            test_data=test_data,
            true_labels=test_targets,
            prediction=predictions,
    )

    print("\n" + "-" * 50 + f"\nCLASSIFICATION METRICS\n" + "-" * 50 + "\n")
    # METRICS
    
        # CALCULATE METRICS
    accuracy = metrics.accuracy_score(y_pred=predictions, y_true=test_targets)
    f1_score = metrics.f1_score(y_pred=predictions, y_true=test_targets)
    f2_score = metrics.fbeta_score(y_pred=predictions, y_true=test_targets, beta=2)
    precision = metrics.precision_score(y_pred=predictions, y_true=test_targets)
    recall = metrics.recall_score(y_pred=predictions, y_true=test_targets)
    #fpr = metrics.roc_curve(y_pred=predictions, y_true=test_targets)
    
        # SAVE METRICS IN DATABASE
    classification_study.accuracy = accuracy
    classification_study.f1_score = f1_score
    classification_study.f2_score = f2_score
    classification_study.precision = precision
    classification_study.recall = recall
    #classification_study.fpr = fpr
    classification_study.save()   # SAVE METRICS IN DATABASE
    
        # PRINT METRICS
    print(f"\n{metrics.classification_report(y_pred=predictions, y_true=test_targets)}")
    print(f"Accuracy: {accuracy}")
    print(f"F1 Score: {f1_score}")
    print(f"F2 Score: {f2_score}")
    print(f"Precision: {precision}")
    print(f"Recall: {recall}")
    print(f"\n\nConfusion Matrix:\n\n")
    print(f"\n{metrics.confusion_matrix(y_pred=predictions, y_true=test_targets)}")
    
    # ALARM SYSTEM
    print("\n" + "-" * 50 + f"\nALARM SYSTEM\n" + "-" * 50 + "\n")
    # FIRING POWER ALGORITHM
    SOP = classification_study.origin_extraction_study.SOP
    SPH = classification_study.origin_extraction_study.SPH
    print(f"SOP: {SOP} minutes and of type {type(SOP)}")
    print(f"SPH: {SPH} minutes and of type {type(SPH)}")
    extraction_window = int(classification_study.origin_extraction_study.windowsize)
    print(f"Extraction Window: {extraction_window} seconds and of type {type(extraction_window)}")
    threshold = 0.5 # Default threshold value but should be changed in the future to be user defined
    
    alarm_metrics = postprocessing(test_targets, predictions, SOP, SPH, extraction_window, threshold)

    # SAVE METRICS IN DATABASE
    classification_study.alarm_sensitivity = alarm_metrics['recall']
    classification_study.alarm_fpr = alarm_metrics['fpr_per_hour']
    classification_study.save()

    print(f"\nAlarm Sensitivity: {alarm_metrics['recall']}")
    print(f"Alarm False Positive Rate/hour: {alarm_metrics['fpr_per_hour']}")
    # print(f"\n\nAlarm Confusion Matrix:\n\n")
    # print(f"\n{alarm_metrics['confusion_matrix']}")
    

    print("\n" + "-" * 50 + f"\nEND OF CLASSIFICATION\n" + "-" * 50 + "\n")
    return model_dir
