import numpy as np
import statsmodels.api as sm


# TODO: concluir metodos do ARModCoeff
def ARModCoeff(signal, order, method):
    if method == 'burg':
        coeffs = arburg(signal, order)

    elif method == 'cov':
        coeffs = arcov(signal, order)

    elif method == 'mcov':
        coeffs = armcov(signal, order)

    elif method == 'yule':
        coeffs = aryule(signal, order)

    elif method == 'lpc':
        pass

    return coeffs


def burg(signal, order):
    """
    Returns the coefficients for Autoregressive model using the burg method
    :param signal: matrix with the channels on the columns and the rows as the time signal
    :param order: integer scalar equal or greater than 1

    """
    # Input valiation
    assert signal.size != 0, "Input signal cannot be empty"
    assert isinstance(order, (int, np.integer)) and order > 0, "Order must be non-negative"

    N = signal.shape[0]
    Nchan = signal.shape[1]

    # By convention all polynomials are row vectors
    Aout = np.zeros((Nchan, order + 1), dtype=signal.dtype)

    for ichan in range(Nchan):
        # Inicialization
        efp = signal[1:, ichan]
        ebp = signal[:-1, ichan]
        ef = np.zeros(N - 1, dtype=signal.dtype)

        # Inicial error
        E = np.real(np.dot(signal[:, ichan], signal[:, ichan])) / N

        a = np.zeros(order + 1, dtype=signal.dtype)
        a[0] = 1

        for m in range(1, order + 1):
            # Calculate the next order reflexion (PARCOR) coefficient
            k = (-2 * np.dot(np.conj(ebp[:N - m]), efp[:N - m])) / (
                    np.sum(np.real(efp[:N - m] * efp[:N - m])) + np.sum(np.real(ebp[:N - m] * ebp[:N - m])))

            ef[:N - m - 1] = efp[1:N - m] + k * ebp[1:N - m]
            ebp[:N - m - 1] = ebp[:N - m - 1] + np.conj(k.T) * efp[:N - m - 1]
            efp[:N - m - 1] = ef[:N - m - 1]

            # Update AR Coef
            a[1:m + 1] = a[1:m + 1] + k * np.conj(a[m:0:-1])

            # Update the prediction error
            E *= (1 - np.abs(k) ** 2)

        Aout[ichan] = a
    return Aout


def arburg(signal, order):
    coeffs = np.zeros((order, 1))  # Dummy Column
    # Iteration through the channels to compute de AR coefficients
    for i in range(signal.shape[1]):
        rho, _ = sm.regression.linear_model.burg(signal[:, i], order=order)
        coeffs = np.hstack((coeffs, rho.reshape((order, 1))))
    coeffs = coeffs[:, 1:]  # Eliminate the dummy Column
    return coeffs


def arcov(signal, order):
    """
    Returns the coefficients for an Autoregressive Model using the covariance method
    :param signal: matrix with the channels on the columns and the rows as the time signal
    :param order: integer scalar equal or greater than 1
    """
    pass


def armcov(signal, order):
    """
       Returns the coefficients for an Autoregressive Model using the modified covariance method
       :param signal: matrix with the channels on the columns and the rows as the time signal
       :param order: integer scalar equal or greater than 1
    """
    pass


def aryule(signal, order):
    coeffs = np.zeros((order, 1))  # Dummy Column
    # Iteration through the channels to compute de AR coefficients
    for i in range(signal.shape[1]):
        rho, _ = sm.regression.linear_model.yule_walker(signal[:, i], order=order)
        coeffs = np.hstack((coeffs, rho.reshape((order, 1))))
    coeffs = coeffs[:, 1:]  # Eliminate the dummy Column
    return coeffs

# https://www.statsmodels.org/dev/generated/statsmodels.regression.linear_model.burg.html#statsmodels.regression.linear_model.burg
# Ver o site accima com alguns dos metodos que é preciso
