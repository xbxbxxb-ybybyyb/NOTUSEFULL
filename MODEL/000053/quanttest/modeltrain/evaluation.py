import numpy as np
from sklearn import metrics
from sklearn.metrics import mean_squared_error, mean_absolute_error  # MSE, MAE

"""
1. Sign-accuracy of top_k% instances
2. MSE
3. MAE
TODO: 4. correlation between labels and predictions
"""


def get_validation_predicts_stat(labels=None, predicts=None):
    """
    :param labels: y_true
    :param predicts: y_predict
    :return: accuracy_str, mse_str, rmse_str, mae_str, corr_str, predicts_str 
    """
    # sort by predict value
    concat_infer = np.concatenate((predicts.reshape(-1, 1), labels.reshape(-1, 1)), axis=1)
    concat_infer = concat_infer[np.argsort(concat_infer[:, 0])]

    # 1. Sign Accuracy
    accuracy_str = ""
    quantile_list = [5, 10, 20, 50, 100]  # correspond to top 20%, 10%, 5%, 2%, 1%
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
        accuracy_str += "\n"

    # 2. MSE + RMSE (RMSE = MSE ** 0.5)
    mse = mean_squared_error(labels, predicts)
    mse_str = " Mean Squared Error is: {: .6f}".format(mse)
    rmse_str = " Root Mean Squared Error is: {: .6f}".format(np.sqrt(mse))

    # 3. MAE
    mae = mean_absolute_error(labels, predicts)
    mae_str = " Mean Absolute Error is: {: .6f}".format(mae)
    
    # TODO: 4. correlation
    correlation_matrix = np.corrcoef(labels, predicts)
    corr_str = "  Corrcoef is: {: .6f}".format(correlation_matrix[0][1])
    
    # TODO: 5. predicts range
    predicts_ranges = [concat_infer[int(0 * concat_infer.shape[0] / 10)][0], concat_infer[int(1 * concat_infer.shape[0] / 10)][0],
                       concat_infer[int(2 * concat_infer.shape[0] / 10)][0], concat_infer[int(3 * concat_infer.shape[0] / 10)][0],
                       concat_infer[int(4 * concat_infer.shape[0] / 10)][0], concat_infer[int(5 * concat_infer.shape[0] / 10)][0],
                       concat_infer[int(6 * concat_infer.shape[0] / 10)][0], concat_infer[int(7 * concat_infer.shape[0] / 10)][0],
                       concat_infer[int(8 * concat_infer.shape[0] / 10)][0], concat_infer[int(9 * concat_infer.shape[0] / 10)][0],
                       concat_infer[int(concat_infer.shape[0] - 1)][0]
                      ]
    # predicts_ranges = [concat_infer[int(i * concat_infer.shape[0] / 10)][0] for i in range(10)] + [concat_infer[int(concat_infer.shape[0] - 1)][0]]
    predicts_str = ""
    for predicts_range in predicts_ranges:
        predicts_str += "{0: .6f};  ".format(predicts_range)
        
    
    return accuracy_str, mse_str, rmse_str, mae_str, corr_str, predicts_str 
    
    
def get_validation_win_return(labels=None, predicts=None, buy=True):
    """
    :param labels: y_true
    :param predicts: y_predict
    :param buy: buy=True, means 买/做多，针对偶数tag；buy=False means 卖/做空，针对奇数tag
    :return: stock_num_str, win_str, return_rate_str, mean_return_rate_str
    """
    # sort by predict value. ascending order
    if not buy:  # sell
        labels = -labels
        predicts = -predicts
        
    concat_infer = np.concatenate((predicts.reshape(-1, 1), labels.reshape(-1, 1)), axis=1)
    concat_infer = concat_infer[np.argsort(concat_infer[:, 0])]
    
    stock_num_str = ""
    # 1. win rate (需要 rate>1.2 即手续交易费)
    win_str = ""
    # 2. return rate
    return_rate_str = ""
    # 3. mean rate of return for each stock_num, return_rate的计量单位是千分比
    mean_return_rate_str = ""
    
    # select items (predict > threshold) to buy
    quantile_list = [5, 10, 20, 50, 100]  # correspond to top 20%, 10%, 5%, 2*
    for quantile in quantile_list:
        quantile_num = int(concat_infer.shape[0] / quantile)
        dir_rst = concat_infer[-quantile_num:]
        
        stock_num = int(dir_rst.shape[0])
        stock_num_str += "top_{0}%_stock_num_satisfy: {1: .6f}  ".format(int(100 / quantile), stock_num)
        
        negative_num = (dir_rst[:, 1] < 1.2).sum()  # <1.2 就是考虑交易手续费，赚的大于手续费才算胜利
        win = 1.0 - negative_num * 1.0 / quantile_num  # acc of topk
        win_str += "top_{0}%_win-rate: {1: .6f}  ".format(int(100 / quantile), win)
        
        return_rate = (dir_rst[:, 1] - 1.2).sum()
        return_rate_str += "top_{0}%_return-rate: {1: .6f}  ".format(int(100 / quantile), return_rate)
        
        mean_return_rate = return_rate / stock_num
        mean_return_rate_str += "top_{0}%_mean-return-rate: {1: .6f}  ".format(int(100 / quantile), mean_return_rate)
    mean_return_rate_str += "\n"
    
    return stock_num_str, win_str, return_rate_str, mean_return_rate_str
    