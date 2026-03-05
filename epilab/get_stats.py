
import numpy as np
from scipy import stats

def statistical_moments(data):
    # Mean
    mean = np.mean(data, axis=0) 
    # Variance
    variance = np.var(data, axis=0)
    # Skewness
    skewness = stats.skew(data, axis=0)
    # Kurtosis
    kurt = stats.kurtosis(data, axis=0)
        
    return mean, variance, skewness, kurt
    