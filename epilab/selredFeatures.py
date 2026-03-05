import sys
import pandas as pd
import numpy as np
import pickle
import ast
from joblib import dump, load

from sklearn.decomposition import PCA
from sklearn.feature_selection import RFE
from sklearn.svm import SVC

import mrmr

from app.models import *
from epilab import *


def selredFeatures(from_study, feats, method, methodoptions, dir):
    print("\n" + "-" * 50 + f"\nSELECTION/REDUCTION\n" + "-" * 50 + "\n")
    file = np.load(f"{from_study.study.directory}.npz", allow_pickle=True)
    
    # GET DATA FROM STUDY
    if Study.objects.get(pk=from_study.study.idstudy).type == Study.Type.EXTRACT: # IF THE STUDY IS OF TYPE EXTRACT
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
    else:                                                                           # IF THE STUDY IS OF OTHER TYPE
        train_data = file["train_data"]
        test_data = file["test_data"]

        train_targets = file["train_targets"]
        test_targets = file["test_targets"]

        train_timevector = file["train_timevector"]
        test_timevector = file["test_timevector"]

        columns = file['columns']

        model = load(from_study.model_dir)

    # PROCESS TARGET VECTORS TO ONLY VALUES 1 (SPH INTERVAL) AND 0 (NON-SPH INTERVAL)
    train_targets = np.array([1 if x == 1 else 0 for x in train_targets])
    test_targets = np.array([1 if x == 1 else 0 for x in test_targets])

    # SELECT ONLY DATA USER WANTS
    train_data = pd.DataFrame(data=train_data, columns=columns)[feats].to_numpy()
    test_data = pd.DataFrame(data=test_data, columns=columns)[feats].to_numpy()
    columns = np.array(feats)
    model.append(columns)

    # TODO: Implement more Selection/Reduction Algorithms
    # --------------------------
    #       SELECTION
    # --------------------------
    if "RFE" in method:  # Recursive Feature Elimination
        print("\n" + "-" * 50 + f"\nRFE TRANSFORMATION\n" + "-" * 50 + "\n")
        RFEnfeat = int(methodoptions["RFEnfeat"])
        RFEKernel = methodoptions["RFEKernel"]
        RFEStep = int(methodoptions["RFEstep"])
        RFEc = float(methodoptions["RFE_C"])
        
        # SVC Model - use linear kernel for coef_ attribute or probability=True
        if RFEKernel == 'linear':
            svc_model = SVC(kernel=RFEKernel, C=RFEc)
        else:
            # For non-linear kernels, use probability=True to enable feature importance estimation
            svc_model = SVC(kernel=RFEKernel, C=RFEc, probability=True)
        
        svc_model.fit(train_data, train_targets)
        print(f"RFE SVC Model: {svc_model}")

        # RFE MODEL
        rfe = RFE(
                estimator=svc_model,
                n_features_to_select=RFEnfeat,
                step=RFEStep,
        )

        # FIT THE DATA AND TRANSFORM IT
        train_data = rfe.fit_transform(X=train_data, y=train_targets)
        test_data = rfe.transform(test_data)
        print("RFE Transformation: ", train_data.shape)

        # SAVE THE MODEL
        model.append(rfe)

        # SELECTED COLUMNS
        if not isinstance(columns, np.ndarray):
            columns = np.array(columns)

        columns = columns[rfe.get_support()]


    elif "MRMR" in method:  # Minimum Redundancy Maximum Relevance
        print("\n" + "-" * 50 + f"\nMRMR TRANSFORMATION\n" + "-" * 50 + "\n")
        MRMR_k = int(methodoptions["MRMRk"])

        # Transform into DataFrama
        X = pd.DataFrame(train_data, index=train_timevector, columns=columns)
        y = pd.Series(train_targets, index=train_timevector)

        # MRMR TRANSFORMATION
        mrmr_selector = mrmr.mrmr_classif(X, y, K=MRMR_k)
        model.append(mrmr_selector)

        # APPLY MRMR TO THE DATA
        train_data = X[mrmr_selector].to_numpy()
        test_data = pd.DataFrame(test_data, index=test_timevector, columns=columns)[mrmr_selector].to_numpy()

        # SELECTED COLUMNS
        columns = np.array(mrmr_selector)

    # --------------------------
    #       REDUCTION
    # --------------------------
    if "PCA" in method:  # Principal Component Analysis
        print("\n" + "-" * 50 + f"\nPCA ANALYSIS\n" + "-" * 50 + "\n")
        nfeat = train_data.shape[1]
        if methodoptions["PCAnComponents"] == "kaiser":
            nfeat = kaiser_dimension(train_data)
            print(f"Kaiser: {nfeat}")
        elif methodoptions["PCAnComponents"] == "explainedVariance":
            threshold = float(methodoptions["thresholdPCA"])
            nfeat = explained_variance(train_data, threshold)
            print(f"Explained Variance: {nfeat}")
        elif methodoptions["PCAnComponents"] == "manual":
            nfeat = int(methodoptions["pcadim"])
            print(f"Manual: {nfeat}")
        elif methodoptions["PCAnComponents"] == "scree":
            nfeat = screeRule(train_data, epsilon=float(methodoptions["epsilonPCA"]))
            print(f"Scree Rule: {nfeat}")

        # CREATE PCA MODEL AND FIT DATA
        pca = PCA(n_components=nfeat)
        pca.fit(train_data)

        # PRINCIPAL COMPONENTS COLUMNS
        columns = np.array([f"PC{i + 1}" for i in range(nfeat)])

        # SAVE THE MODEL
        model.append(pca)

        # APPLY PCA TO THE DATA
        train_data = pca.transform(train_data)
        test_data = pca.transform(test_data)
        print("PCA Transformation: ", train_data.shape)

    # MODEL SAVE
    model_dir = f"{dir}_model.joblib"
    dump(model, model_dir)

    # SAVE THE FINAL DATA ARRAY
    np.savez(
            dir,
            train_data=train_data,
            train_targets=train_targets,
            train_timevector=train_timevector,
            test_data=test_data,
            test_targets=test_targets,
            test_timevector=test_timevector,
            columns=columns,
            allow_pickle=True,
    )
    print("-" * 50)
    print(f"Model saved at: {model_dir}")
    print(f"Data saved at: {dir}")
    print("Train Data shape: ", train_data.shape)
    print("Test Data shape: ", test_data.shape)
    print("Columns shape: ", columns.shape)

    print("\n" + "-" * 50 + f"\nEND OF SELECTION/REDUCTION\n" + "-" * 50 + "\n")
    return model_dir


# HELPER FUNCTIONS
# ------ PCA n_components ------
def kaiser_dimension(data: np.ndarray) -> int:
    """
    Calculate the number of components using the Kaiser criterion.
    The Kaiser criterion states that the number of components to be retained is the number of eigenvalues greater than 1.
    Args:
        data (np.ndarray): The data to be analyzed. The data must be a 2D array of (n_samples, n_features).

    Returns:
        nkaiser (int): The number of components to be retained.
    """
    kaiser = PCA(n_components=data.shape[1])
    kaiser.fit(data)
    try:
        nkaiser: int = next(
                i for i, num in enumerate(kaiser.explained_variance_) if num < 1
        )
    except StopIteration:
        nkaiser = data.shape[1]
    return nkaiser  # TODO: Check if it should be +1


def explained_variance(data: np.ndarray, threshold: float) -> int:
    """
    Calculate the number of components using the explained variance threshold.
    The explained variance threshold is the percentage of variance that the components explain.
    Args:
        data (np.ndarray): The data to be analyzed. The data must be a 2D array of (n_samples, n_features).
        threshold (float): The threshold to be used. The threshold must be between 0 and 1.

    Returns:
        nExplainedVariance (int): The number of components to be retained.
    """
    # CHECK IF THRESHOLD IS BETWEEN 0 AND 1
    if threshold > 1 or threshold < 0:
        raise ValueError("Threshold must be between 0 and 1.")

    # INICIALIZE PCA AND FIT DATA
    pca = PCA(n_components=data.shape[1])
    pca.fit(data)

    # CALCULATE CUMULATIVE EXPLAINED VARIANCE
    explainedVariance = np.cumsum(pca.explained_variance_ratio_)

    # CHECK THE NUMBER OF COMPONENTS THAT EXPLAINS THE THRESHOLD
    nExplainedVariance: int = next(
            i for i, num in enumerate(explainedVariance) if num > threshold
    )
    return nExplainedVariance + 1


# TODO: Check if it should be +1 or not
def screeRule(data: np.ndarray, epsilon: float = 0.01) -> int:
    """
    Calculate the number of components using the Scree rule.
    The Scree rule states that the number of components to be retained is the number of components where the difference
    between the eigenvalues is less than epsilon, in other words, the number of components where the curve starts to
    flatten.
    Args:
        data (np.ndarray): The data to be analyzed. The data must be a 2D array of (n_samples, n_features).
        epsilon (float): The threshold to be used. The threshold must be greater than 0.

    Returns:
        screeRule_nfeat (int): The number of components to be retained.
    """
    scree = PCA(n_components=data.shape[1])
    scree.fit(data)
    dy = np.diff(scree.explained_variance_)
    try:
        screeRule_nfeat = next(i for i, num in enumerate(dy) if np.abs(num) < epsilon)
        return screeRule_nfeat + 1
    except StopIteration:
        return data.shape[1]
