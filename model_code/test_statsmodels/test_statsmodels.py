import numpy as np
import os
os.environ['use_cmo'] = 'True'
import argparse
import statsmodels.api as sm
from sklearn.metrics import mean_squared_error
from xquant.model import log_metrics


def parse_args():
    parser = argparse.ArgumentParser(description="Statsmodels example")
    parser.add_argument(
        "--inverse-method",
        type=str,
        default="pinv",
        help="Can be 'pinv', or 'qr'. 'pinv' uses the Moore-Penrose pseudoinverse "
        "to solve the least squares problem. 'qr' uses the QR factorization. "
        "(default: 'pinv')",
    )
    return parser.parse_args()


def main():
    # parse command-line arguments
    args = parse_args()

    # prepare train and test data
    # Ordinary Least Squares (OLS)
    np.random.seed(9876789)
    nsamples = 100
    x = np.linspace(0, 10, 100)
    X = np.column_stack((x, x ** 2))
    beta = np.array([1, 0.1, 10])
    e = np.random.normal(size=nsamples)
    X = sm.add_constant(X)
    y = np.dot(X, beta) + e

    # enable auto logging
    # auto_log('statsmodels')

    ols = sm.OLS(y, X)
    model = ols.fit(method='pinv')

    # evaluate model
    y_pred = model.predict(X)
    mse = mean_squared_error(y, y_pred)

    # log metrics
    log_metrics({"mse": mse})


if __name__ == "__main__":
    main()
