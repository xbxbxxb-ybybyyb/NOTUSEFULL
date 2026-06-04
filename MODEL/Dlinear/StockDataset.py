import torch
from torch.utils.data import Dataset
import pandas as pd
import numpy as np

class StockDataset(Dataset):
    def __init__(self, df, seq_len, pred_len, features, target):
        """
        :param df: 数据框，包含特征列和目标列。
        :param seq_len: 输入序列长度。
        :param pred_len: 预测序列长度。
        :param features: 特征列名列表。
        :param target: 目标列名。
        """
        self.seq_len = seq_len
        self.pred_len = pred_len
        self.features = features
        self.target = target
        self.data = df

    def __len__(self):
        return len(self.data) - self.seq_len - self.pred_len + 1

    def __getitem__(self, index):
        s_begin = index
        s_end = s_begin + self.seq_len
        r_begin = s_end
        r_end = r_begin + self.pred_len

        seq_x = self.data.iloc[s_begin:s_end][self.features].values
        seq_y = self.data.iloc[r_begin:r_end][self.target].values

        return torch.tensor(seq_x, dtype=torch.float32), torch.tensor(seq_y, dtype=torch.float32)
        
        