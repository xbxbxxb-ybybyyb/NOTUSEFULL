import torch
import torch.nn as nn
import numpy as np
from DataProvider import DataProvider
import DLinear

class Configs:
    seq_len = 240
    pred_len = 3
    batch_size = 32
    kernel_size = 5      # 求trend的滑动窗口，感觉可调？？？
    enc_in = 3      # features数量，要和DataProvider中feature定义长度保持一致
    c_out = 1       # label数量，……一致
    individual = True      # 是否独立建模

configs = Configs()
scaler = True

device = 'cuda' if torch.cuda.is_available() else 'cpu'

model = DLinear.Model(configs)  # 定义模型结构
model.load_state_dict(torch.load('/data/user/000055/zjs_project/DLinear_model/best_model.pth'))  # 加载模型参数
model = model.to(device)

season_list = []
trend_list = []
if model.individual:
    for i in range(model.channels):
#        model.Linear_Seasonal.weight = \
#            nn.Parameter((1/model.seq_len)*torch.ones([model.pred_len, model.seq_len]))
        print(model.Linear_Seasonal[i].weight)
#        model.Linear_Trend.weight = \
#            nn.Parameter((1/model.seq_len)*torch.ones([model.pred_len, model.seq_len]))
        print(model.Linear_Trend[i].weight)
        break
        
###可以把权重矩阵下载下来，可视化，进行解读