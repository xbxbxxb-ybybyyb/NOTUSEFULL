import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error  # MSE, MAE

"""
TODO: Two evaluation metrics
1. Sign-accuracy of top_k% instances
2. MSE
3. MAE
"""


def get_validation_predicts_stat(labels=None, predicts=None):
    """
    :param labels: y_true
    :param predicts: y_predict
    :return: accuracy_str, mse_str
    """
    # sort by predict value
    concat_infer = np.concatenate((predicts.reshape(-1, 1), labels.reshape(-1, 1)), axis=1)
    concat_infer = concat_infer[np.argsort(concat_infer[:, 0])]

    # 1. Sign Accuracy
    accuracy_str = ""
    quantile_list = [5, 10, 20, 50]  # correspond to top 20%, 10%, 5%, 2*
    for direction in ["top", "bottom"]:
        for quantile in quantile_list:
            quantile_num = int(concat_infer.shape[0] / quantile)
        if direction == "top":
            dir_rst = concat_infer[-quantile_num:]
        else:
            dir_rst = concat_infer[:quantile_num]

        negative_num = (dir_rst[:, 0] * dir_rst[:, 1] < 0).sum()
        accuracy = 1.0 - negative_num * 1.0 / quantile_num  # acc of topk
        accuracy_str += "{0}_{1}%_acc: {2: .6f}  ".format(direction, int(100 / quantile), accuracy)

    # 2. MSE + RMSE (RMSE = MSE ** 0.5)
    mse = mean_squared_error(labels, predicts)
    mse_str = " Mean Squared Error is: {: .6f}".format(mse)
    rmse_str = " Mean Squared Error is: {: .6f}".format(np.sqrt(mse))

    # 3. MAE
    mae = mean_absolute_error(labels, predicts)
    mae_str = " Mean Absolute Error is: {: .6f}".format(mae)

    return accuracy_str, mse_str, rmse_str, mae_str