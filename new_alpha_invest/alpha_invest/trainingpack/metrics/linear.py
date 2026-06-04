from sklearn.metrics import mean_squared_error # 均方误差
from sklearn.metrics import mean_absolute_error # 平方绝对误差
from sklearn.metrics import r2_score # R square
import numpy as np
# 调整后的R square
def adj_r_squared(x_test,y_test,y_predict):
    SS_R = sum((y_test-y_predict)**2)
    SS_T = sum((y_test-np.mean(y_test))**2)
    r_squared = 1 - (float(SS_R))/SS_T
    adj_r_squared = 1 - (1-r_squared)*(len(y_test)-1)/(len(y_test)-x_test.shape[1]-1)
    return adj_r_squared
# 皮尔逊相关系数
from scipy.stats import pearsonr
#调用
# mean_squared_error(y_test,y_predict)
# mean_absolute_error(y_test,y_predict)
# r2_score(y_test,y_predict)
# adj_r_squared(x_test,y_test,y_predict)
# pearsonr(y_test,y_predict)
