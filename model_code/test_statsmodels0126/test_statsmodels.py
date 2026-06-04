import os
os.environ["use_cmo"]='True'
import numpy as np
from xquant.model import auto_log, log_metrics, log_params
from sklearn.linear_model import LinearRegression


def main():
    # prepare training data
    X = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
    y = np.dot(X, np.array([1, 2])) + 3

    # train a model
    model = LinearRegression()
    model.fit(X, y)

    # show logged data
    log_params({'alpha': 0, 'beta': 0, 'seed': 4, 'num_boost_round': 10})
    log_metrics(
        {"OPTIMAL_ALPHA": 1, "MSE": 1, "mae": 1})
    log_metrics({"test1": 1, "test2": 2})
    for i in range(1, 5):
        step = i
        m_dict = {'a': i, 'b': i * 10}
        log_metrics(m_dict, step=step)

if __name__ == "__main__":
    main()
