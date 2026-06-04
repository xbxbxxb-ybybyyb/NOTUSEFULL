import pickle
import torch
from torch.utils.data import Dataset,DataLoader

class TSDataSet(Dataset):
    def __init__(self, df_x, df_y, window = 10):
        df_x = df_x.reset_index();
        df_x["stock"] = df_x["level_1"].apply(lambda x:int(x.split(".")[0]))
        df_x = df_x.set_index(["timestamp", "level_1"])
        x = df_x.values
        y = df_y.values
        self.stocks = sorted(set(df_x.index.get_level_values(1)))
        self.dates = sorted(set(df_x.index.get_level_values(0)))
        self.factors = df_x.columns.tolist()
        self.window = window

        #转为3D
        x = x.reshape((len(self.dates), len(self.stocks), len(self.factors)))
        y = y.reshape((len(self.dates), len(self.stocks), 1))

        self.x_train = torch.tensor(x, dtype = torch.float32)
        self.y_train = torch.tensor(y, dtype = torch.float32)

    def __len__(self):
        #idx = len(stocks)*(len(dates)-window+1)
        return (len(self.dates)-self.window+1)*len(self.stocks)

    def __getitem__(self, idx):
        if idx == 243:
            pass
        stock_id = int(idx/(len(self.dates)-self.window+1))
        date_id = idx - stock_id*(len(self.dates)-self.window+1)
        if self.y_train.shape[2]==1:
            return self.x_train[date_id:date_id+self.window, stock_id, :],self.y_train[date_id+self.window-1,stock_id,0]
        else:
            return self.x_train[date_id:date_id + self.window, stock_id, :], self.y_train[date_id + self.window - 1,
                                                                             stock_id, :]



import pandas as pd
dfx = pd.read_pickle("./original_datax.pkl")
dfy = pd.read_pickle("./original_datay.pkl")
print(dfx)


import yaml
from alpha_invest.models.pytorch_tcn_ts import TCN

def get_tcn_task():
    config = yaml.load(open("./qlib_examples/benchmarks/TCTS/workflow_config_tcts_Alpha360.yaml", "rb"))
    return config
config = get_tcn_task()

tsds = TSDataSet(dfx, dfy, window=config['task']["model"]["kwargs"]["d_feat"])
# train_loader = DataLoader(tsds, batch_size=1, shuffle=False)

# for i, (data, label) in enumerate(train_loader):
#     print(i, data.shape, label.shape, data[:,:,3])


model_params = config['task']["model"]["kwargs"]
model = TCN(**model_params)
print(model)
model.fit(tsds)
