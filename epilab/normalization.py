# GENERAL MODULES
import numpy as np
import pickle
from joblib import dump

# SCIKIT-LEARN MODULES
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# EPIWEB MODULES
from epilab import *
from app.models import *


def normalizeStudy(extraction, method, dir):
    # DATA LOADING
    file = np.load(extraction.study.directory + ".npz", allow_pickle=True)

    data = file["data2d"]
    targets = file["target"]
    timevector = file["timevector"]

    # DATA SPLITING INTO TRAINING AND TESTING
    splitpoint = extraction.split_point

    data_train = data[:splitpoint]
    data_test = data[splitpoint:]

    target_train = targets[:splitpoint]
    target_test = targets[splitpoint:]

    timevector_train = timevector[:splitpoint]
    timevector_test = timevector[splitpoint:]

    # NORMALIZATION
    print("Normalizing data with method: " + method)
    if method == "Z-Score":
        # CREATE SCALER
        scaler = StandardScaler()

        # FIT AND NORMALIZE DATA
        data_train_normalized = scaler.fit_transform(data_train)

        # SCALER VALUES
        scalers = np.vstack([scaler.scale_, scaler.mean_])

    elif method == "[0,1]":
        # CREATE SCALER
        scaler = MinMaxScaler(feature_range=(0, 1))

        # FIT AND NORMALIZE DATA
        data_train_normalized = scaler.fit_transform(data_train)

        # SCALER VALUES
        scalers = np.vstack([scaler.scale_, scaler.min_])

    elif method == "[-1,1]":
        # CREATE SCALER
        scaler = MinMaxScaler(feature_range=(-1, 1))

        # FIT AND NORMALIZE DATA
        data_train_normalized = scaler.fit_transform(data_train)

        # SCALER VALUES
        scalers = np.vstack([scaler.scale_, scaler.min_])

    # SAVE SCALER
    model = [scaler]
    dump(model, f"{dir}_model.joblib")
    np.save(f"{dir}_model.npy", scalers, allow_pickle=True)
    print(f"Model saved in {dir}_model.joblib")

    # APPLY SCALER TO TEST DATA
    data_test_normalized = scaler.transform(data_test)

    # SAVE NORMALIZED DATA
    np.savez(
        dir, # SAVE IN THE SAME DIRECTORY
        # TRAINING DATA
        train_data=data_train_normalized,
        train_timevector=timevector_train,
        train_targets=target_train,
        # TESTING DATA
        test_data=data_test_normalized,
        test_timevector=timevector_test,
        test_targets=target_test,
        # OTHER DATA
        columns=file["columns"],
        allow_pickle=True, # ALLOW PICKLE TO SAVE OBJECTS
    )

    print(f"Data normalized with {method} method")
    return f"{dir}_model.joblib"  # Return the path to the model file
