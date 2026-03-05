import numpy as np

def hjorth_parameters(data):
    
    # Activity = variance
    variance = np.var(data, axis=0)
    squared_standard_deviation_amplitude = variance
    
    first_derivative = np.diff(data, axis=0) 
    squared_standard_deviation_first_derivative = np.var(first_derivative, axis=0) 
    
    second_derivative = np.diff(first_derivative, axis=0)
    squared_standard_deviation_second_derivative = np.var(second_derivative, axis=0) 
    
    # Mobility
    dm = squared_standard_deviation_first_derivative/squared_standard_deviation_amplitude
    mobility = np.sqrt(dm)
    
    # Complexity
    num_c = squared_standard_deviation_second_derivative*squared_standard_deviation_amplitude
    den_c = np.square(squared_standard_deviation_first_derivative)
    complexity = np.sqrt(num_c/den_c)
    
    return mobility, complexity
