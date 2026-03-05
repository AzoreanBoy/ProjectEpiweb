import os
import numpy as np
import pickle


def postprocessing(true_labels:np.ndarray, predictions:np.ndarray, SOP:int, SPH:int, extraction_window:int, threshold:float=0.5) -> np.ndarray:
    """
    Calculate the firing power of predictions over a sliding window.
    Parameters:
    - true_labels (np.ndarray): Array of true labels (binary values).
    - predictions (np.ndarray): Array of predicted labels (binary values).
    - SOP (int): Start of prediction window in minutes.
    - SPH (int): Start of post-prediction window in minutes.
    - extraction_window (int): Size of the extraction window in seconds.
    Returns:
    - np.ndarray: Array of firing power values for each position in the input arrays.
    """
    # ENSURE THAT THE INPUTS ARE NUMPY ARRAYS
    predictions = np.array(predictions)
    true_labels = np.array(true_labels)

    # CHECK IF BOTH ARRAYS HAVE THE SAME LENGTH
    if len(predictions) != len(true_labels):
        raise ValueError("Prediction and true_labels must be of the same length.")

    # GUARANTEE THAT THE INPUTS ARE INTEGERS AND BINARY - THIS MAY CHANGE IN THE FUTURE WHEN USING MULTI-CLASS PREDICTIONS
    if not np.all(np.isin(predictions, [0, 1])):
        raise ValueError("Predictions must be binary.")

    # CALCULATE THE SLIDING WINDOW
    sliding_window = ((SOP + SPH) *60) // extraction_window

    # COMPUTE THE FIRING POWER
    firing_power = firing_power_algorithm(true_labels, predictions, SOP, SPH, extraction_window)

    # COMPUTE THE ALARMS
    alarms = alarm_algorithm(firing_power, sliding_window, threshold)

    # COMPUTE THE ALARMS BASED ON TRUE LABELS
    alarms_true = alarm_algorithm(true_labels, sliding_window, threshold)

    # COMPUTE THE METRICS
    alarm_metrics = calculate_alarms_metrics(true_labels, predictions, alarms, alarms_true)

    return alarm_metrics


def firing_power_algorithm(true_labels: np.ndarray, predictions: np.ndarray, SOP: int, SPH: int,
                           extraction_window: int) -> np.ndarray:
    """
        Calculate the firing power of predictions over a sliding window.
        Parameters:
        - true_labels (np.ndarray): Array of true labels (binary values).
        - predictions (np.ndarray): Array of predicted labels (binary values).
        - SOP (int): Seizure Occurrence Period in minutes.
        - SPH (int): Seizure Prediction Horizon in minutes.
        - extraction_window (int): Size of the extraction window in seconds.
        Returns:
        - np.ndarray: Array of firing power values for each position in the input arrays.
        """


    # ENSURE THAT THE INPUTS ARE NUMPY ARRAYS
    predictions = np.array(predictions)
    true_labels = np.array(true_labels)

    # CHECK IF BOTH ARRAYS HAVE THE SAME LENGTH
    if len(predictions) != len(true_labels):
        raise ValueError("Prediction and true_labels must be of the same length.")

    # GUARANTEE THAT THE INPUTS ARE INTEGERS AND BINARY
    if not np.all(np.isin(predictions, [0, 1])):
        raise ValueError("Predictions must be binary.")

    # CALCULATE THE SLIDING WINDOW
    sliding_window = ((SOP + SPH) * 60) // extraction_window

    # CREATE A LIST TO STORE THE RESULTS
    firing_power = np.zeros_like(true_labels, dtype=float)

    # ITERATE OVER THE PREDICTIONS
    for i in range(len(predictions)):
        # CHECK IF THE CURRENT INDEX IS SMALLER THAN THE SLIDING WINDOW
        if i < sliding_window:
            # IF SO, SET THE FIRING POWER TO 0
            firing_power[i] = 0
        else:
            # OTHERWISE, CALCULATE THE FIRING POWER
            firing_power[i] = np.sum(predictions[i - sliding_window + 1: i + 1]) / sliding_window

    return firing_power

def alarm_algorithm(firing_power: np.ndarray, refractory: int, threshold: float = 0.5) -> np.ndarray:
    """
    Calculate the alarm signal based on the firing power and a threshold.
    Parameters:
    - firing_power (np.ndarray): Array of firing power values.
    - threshold (float): Threshold value for the alarm signal. Default is 0,5.
    Returns:
    - np.ndarray: Array of alarm signals.
    """
    # CHECK IF THE FIRING POWER IS A NUMPY ARRAY
    if not isinstance(firing_power, np.ndarray):
        raise ValueError("Firing power must be a numpy array.")

    # CHECK IF THE THRESHOLD IS A FLOAT
    if not isinstance(threshold, float):
        raise ValueError("Threshold must be a float.")

    # CHECK IF THE REFRACTORY PERIOD IS AN INTEGER
    if not isinstance(refractory, int):
        raise ValueError("Refractory period must be an integer.")

    # CREATE A LIST TO STORE THE RESULTS
    alarms = np.zeros_like(firing_power, dtype=bool)

    # CREATE A VARIABLE TO STORE THE INDEX OF THE LAST ALARM (INITIALLY SET TO -REFRACTORY)
    last_alarm = -refractory

    # ITERATE THROUGH THE FIRING POWER VALUES STARTING FROM THE SECOND SAMPLE
    for i in range(1, len(firing_power)):
        # CHECK FOR AN ASCENDING CROSSING: PREVIOUS VALUE BELOW THRESHOLD, CURRENT VALUE AT/ABOVE THRESHOLD
        if firing_power[i - 1] < threshold and firing_power[i] >= threshold:
            # CHECK IF THE REFRACTORY PERIOD HAS PASSED SINCE THE LAST ALARM
            if (i - last_alarm) >= refractory:
                alarms[i] = True
                last_alarm = i  # UPDATE THE INDEX OF THE LAST ALARM

    return alarms.astype(int) # CONVERT BOOLEAN ARRAY TO INTEGER ARRAY AND RETURN IT

def calculate_alarms_metrics(true_labels: np.ndarray, predictions: np.ndarray, alarms: np.ndarray, alarms_true: np.ndarray):
    """
    Calculate evaluation metrics for the alarm system.
    Parameters:
    - true_labels (np.ndarray): Array of true labels (binary values).
    - predictions (np.ndarray): Array of predicted labels (binary values).
    - alarms (np.ndarray): Array of alarm signals (binary values).
    - alarms_true (np.ndarray): Array of true alarm signals (binary values).
    Returns:
    - dict: Dictionary containing the evaluation metrics.
    """
    # CHECK IF ALL INPUTS ARE NUMPY ARRAYS
    for arr in [true_labels, predictions, alarms, alarms_true]:
        if not isinstance(arr, np.ndarray):
            raise ValueError("All inputs must be numpy arrays.")

    # CALCULATE TRUE POSITIVES, FALSE POSITIVES, FALSE NEGATIVES
    TP = np.sum((predictions == 1) & (true_labels == 1))
    FP = np.sum((predictions == 1) & (true_labels == 0))
    FN = np.sum((predictions == 0) & (true_labels == 1))

    # CALCULATE ADDITIONAL METRICS
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    fpr_per_hour = FP / (len(true_labels) / 3600)

    # STORE METRICS IN A DICTIONARY
    metrics = {
        "true_positives": TP,
        "false_positives": FP,
        "false_negatives": FN,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "fpr_per_hour": fpr_per_hour,
    }

    return metrics