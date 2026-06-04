from parallel_train.backend import LocalTrainBackend
from alpha_invest.datasets.dataset_loader import DatasetLoader
from alpha_invest.datasets.dataset_manager import DataSetManager, PurgedGroupTimeSeriesSplit
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', 20)
import torch
from torch.utils import data
from torchinfo import summary
import torch.nn as nn
from datetime import datetime
import torch.optim as optim

from sklearn.metrics import accuracy_score, classification_report
from tqdm import tqdm
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

print(device)

class deeplob(nn.Module):
    def __init__(self, y_len, batch_size, data_window, num_features):
        super().__init__()
        self.y_len = y_len
        self.batch_size = batch_size
        self.lstm_hidden_size = 64

        # convolution blocks
        self.conv1 = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=32, kernel_size=(3, num_features), stride=(1, 1), padding='valid'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(32),
            nn.MaxPool2d((2, 1), stride=(2, 1)),
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=(3, 1), stride=(1, 1), padding='valid'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(32),
            nn.MaxPool2d((2, 1), stride=(2, 1)),
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=(3, 1),  stride=(1, 1), padding='valid'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(64),
        )

        # inception moduels
        # inception moduels
        self.inp1 = nn.Sequential(
            nn.Conv2d(in_channels=64, out_channels=24, kernel_size=(3, 1), padding='same'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(24),
            nn.Conv2d(in_channels=24, out_channels=24, kernel_size=(3, 1), padding='same'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(24),
        )
        self.inp2 = nn.Sequential(
            nn.Conv2d(in_channels=64, out_channels=24, kernel_size=(1, 1), padding='same'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(24),
            nn.Conv2d(in_channels=24, out_channels=24, kernel_size=(5, 1), padding='same'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(24),
        )
        self.inp3 = nn.Sequential(
            nn.AvgPool2d((3, 1), stride=(1, 1), padding=(1, 0)),
            nn.Conv2d(in_channels=64, out_channels=8, kernel_size=(1, 1), padding='same'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(8),
        )

        # automatic calc shape
        #################################################
        sample_data = torch.ones([batch_size, 1, data_window, num_features])
        x = self.conv1(sample_data)

        x_inp1 = self.inp1(x)
        x_inp2 = self.inp2(x)
        x_inp3 = self.inp3(x)
        x = torch.cat((x_inp1, x_inp2, x_inp3), dim=1)
        # lstm layers
        #################################################
        out_shape = x.shape[1]#取第二维channel_num作为LSTM的输入维度，第四维feature_num必须为1，从四维变成3维数据，适应LSTM
        print("CNN connect to LSTM: out_shape:", out_shape,  x.shape)
        self.lstm = nn.LSTM(input_size=out_shape, hidden_size=self.lstm_hidden_size, num_layers=1, batch_first=True)
        self.fc = nn.Linear(self.lstm_hidden_size, 1)
        #################################################
        # out_shape = x.view(batch_size, - 1).shape[-1]
        # print("CNN connect to linear: out_shape:", out_shape, x.shape)
        # self.fc1 = nn.Linear(98304, 256)
        # self.fc2 = nn.Linear(256, self.y_len)
        #################################################


    def forward(self, x):
        # h0: (number of hidden layers, batch size, hidden size)
        h0 = torch.zeros(1, x.size(0), self.lstm_hidden_size).to(device)
        c0 = torch.zeros(1, x.size(0), self.lstm_hidden_size).to(device)
        x = self.conv1(x)

        x_inp1 = self.inp1(x)
        x_inp2 = self.inp2(x)
        x_inp3 = self.inp3(x)

        x = torch.cat((x_inp1, x_inp2, x_inp3), dim=1)

        x = x.permute(0, 2, 1, 3)#变成（batch_size, 时间序列维度，channel_num, feature_num)
        #################################################
        x = torch.reshape(x, (-1, x.shape[1], x.shape[2]))#第四维feature_num必须为1，从四维变成3维数据，适应LSTM
        x, _ = self.lstm(x, (h0, c0))
        x = x[:, -1, :]
        #################################################
        # x = torch.flatten(x, 1, -1)
        # x = self.fc1(x)
        # x = self.fc2(x)
        #################################################
        forecast_y = self.fc(x)

        return forecast_y

class DeepLOBPack(LocalTrainBackend):
    def __init__(self):
        pass

    def prepare_data(self, data_params):
        dloader = DatasetLoader()
        dloader.load_factor_data(factor_path = "/data/user/quanttest007/alpha_invest/merge_data.pkl", classify_or_not = False,
                                 mock_data_flag=data_params["mock_data_flag"], num_features=data_params["num_features"], tag_name=data_params["tag_name"])
        #TODO: 训练集和验证集分开标准化
        self.factor_data_train, self.factor_data_test, self.label_data_train, self.label_data_test = dloader.train_test_split(
            train_test_split_date="20220601")

        # STEP: 数据预处理&特征工程
        from sklearn.preprocessing import StandardScaler
        train_factor_scaler = StandardScaler()
        train_factor_scaler.fit(self.factor_data_train.values[:, 3:])#数据标准化
        self.factor_data_train.loc[:, 3:] = train_factor_scaler.transform(self.factor_data_train.values[:, 3:])
        self.factor_data_test.loc[:, 3:] = train_factor_scaler.transform(self.factor_data_test.values[:, 3:])

        #STEP: 构建torch数据集
        self.data_window = data_params.pop("window")
        self.random_state = data_params.pop("random_state")
        self.num_features = data_params["num_features"]
        dmanager_train = DataSetManager(self.factor_data_train, self.label_data_train, data_type = 'tick')
        dataset_train = dmanager_train.transform_torch_dataset_ts(window=self.data_window)
        train_size = int(0.8 * len(dataset_train))
        valid_size = len(dataset_train) - train_size
        dataset_train, dataset_val = torch.utils.data.random_split(dataset_train, [train_size, valid_size])
        print("prepare_data, dataset_train shape:", len(dataset_train.indices), "dataset_val shape:",
              len(dataset_val.indices))

        dataset_test = DataSetManager(self.factor_data_test, self.label_data_test, data_type='tick')
        dataset_test = dataset_test.transform_torch_dataset_ts(window=self.data_window)
        self.dataset_train, self.dataset_val, self.dataset_test = dataset_train, dataset_val, dataset_test

    def train_loop(self, model_params, verbose = 1):
        import sys
        sys.path.append("/data/user/013150")
        from ray import tune

        batch_size = model_params.pop("batch_size")
        lr = model_params.pop("lr")
        epochs = model_params.pop("epochs")

        train_loader = torch.utils.data.DataLoader(dataset=self.dataset_train, batch_size=batch_size, shuffle=True, drop_last=True)
        val_loader = torch.utils.data.DataLoader(dataset=self.dataset_val, batch_size=batch_size, shuffle=False)

        model = deeplob(y_len=1, batch_size = batch_size, data_window = self.data_window, num_features = self.num_features)
        self.model = model
        model.to(device)
        if verbose > 0:
            summary(model, (1, 1, self.data_window, self.num_features))

        # criterion = nn.CrossEntropyLoss()
        criterion = torch.nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)

        train_losses = np.zeros(epochs)
        valid_losses = np.zeros(epochs)
        best_test_loss = np.inf
        best_test_epoch = 0

        for it in tqdm(range(epochs)):

            model.train()
            t0 = datetime.now()
            train_loss = []
            for inputs, targets in train_loader:
                # move data to GPU
                inputs, targets = inputs.to(device, dtype=torch.float), targets.to(device, dtype=torch.float)
                # print("inputs.shape:", inputs.shape)
                # zero the parameter gradients
                optimizer.zero_grad()
                # Forward pass
                # print("about to get model output")
                outputs = model(inputs)
                # print("done getting model output")
                # print("outputs.shape:", outputs.shape, "targets.shape:", targets.shape)
                loss = criterion(outputs, targets)
                # Backward and optimize
                # print("about to optimize")
                loss.backward()
                optimizer.step()
                train_loss.append(loss.item())
            # Get train loss and test loss
            train_loss = np.mean(train_loss)  # a little misleading

            model.eval()
            valid_loss = []
            all_targets = []
            all_predictions = []

            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device, dtype=torch.float), targets.to(device, dtype=torch.int64)
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                valid_loss.append(loss.item())

                _, predictions = torch.max(outputs, 1)
                all_predictions.append(predictions.cpu().numpy())
                all_targets.append(targets.cpu().numpy())

            valid_loss = np.mean(valid_loss)

            # Save losses
            train_losses[it] = train_loss
            valid_losses[it] = valid_loss

            if valid_loss < best_test_loss:
                torch.save(model, '/data/user/quanttest007/best_val_model_pytorch')
                best_test_loss = valid_loss
                best_test_epoch = it
                print('model saved')

            dt = datetime.now() - t0
            auc_report = self.predict(self.dataset_test)
            print(f'Epoch {it + 1}/{epochs}, Train Loss: {train_loss:.4f}, Validation Loss: {valid_loss:.4f}, Duration: {dt}, Best Val Epoch: {best_test_epoch}')
            tune.report(train_losses=train_losses[-1], valid_losses=valid_losses[-1], epochs = it)
        train_result = self.analysis_train_result()
        print('train_result', train_result)


    def get_label_auc_report(self, model, dataset, classify_th = 0.0012):
        def classic(label):
            th = classify_th
            if -th < label < th:
                return 0
            elif label >= th:
                return 1
            else:
                return 2

        all_targets = []
        all_predictions = []

        test_loader = torch.utils.data.DataLoader(dataset=dataset, batch_size=128, shuffle=False)
        for inputs, targets in test_loader:
            # Move to GPU
            inputs, targets = inputs.to(device, dtype=torch.float), targets.to(device, dtype=torch.int64)
            # Forward pass
            predictions = model(inputs)
            all_targets.append(targets.cpu().detach().numpy())
            all_predictions.append(predictions.cpu().detach().numpy())

        all_targets = np.concatenate(all_targets).reshape(-1)
        all_predictions = np.concatenate(all_predictions).reshape(-1)
        f1 = np.frompyfunc(lambda x: classic(x), 1, 1)  # y_class = np.apply_along_axis(classic, 0, y)
        y_class = f1(all_targets).astype('int64')
        preds_class = f1(all_predictions).astype('int64')
        auc_report = pd.DataFrame(classification_report(y_class, preds_class, output_dict=True))
        return auc_report, all_targets, all_predictions


    def analysis_train_result(self):
        result_list = []
        for th in [0.0012]:
            auc_report_train, targets_train, preds_train = self.get_label_auc_report(self.model, self.dataset_train, th)
            auc_report_valid, targets_valid, preds_valid = self.get_label_auc_report(self.model, self.dataset_val, th)
            train_triggers = sum(preds_train>th)+sum(preds_train<-th)
            valid_triggers = sum(preds_valid>th)+sum(preds_valid<-th)

            train_winrate = sum(targets_train[preds_train>th]>0.001)+sum(targets_train[preds_train<-th]<-0.001) / train_triggers
            valid_winrate = sum(targets_valid[preds_valid > th]>0.001) + sum(targets_valid[preds_valid < -0.001]) /valid_triggers

            train_avgret = sum(targets_train[preds_train > th]) - sum(targets_train[preds_train<-th])
            valid_avgret = sum(targets_valid[preds_valid > th]) - sum(targets_valid[preds_valid<-th])#费前收益率

            result_list.append([th, "train", train_winrate, train_avgret,
                                            auc_report_train.loc['precision'].iloc[0], auc_report_train.loc['precision'].iloc[1], auc_report_train.loc['precision'].iloc[2],
                                            auc_report_train.loc['recall'].iloc[0], auc_report_train.loc['recall'].iloc[1], auc_report_train.loc['recall'].iloc[2],
                                            auc_report_train.loc['support'].iloc[0], auc_report_train.loc['support'].iloc[1], auc_report_train.loc['support'].iloc[2]])
            result_list.append([th, "valid", valid_winrate, valid_avgret,
                                            auc_report_valid.loc['precision'].iloc[0], auc_report_valid.loc['precision'].iloc[1],
                                            auc_report_valid.loc['precision'].iloc[2],
                                            auc_report_valid.loc['recall'].iloc[0], auc_report_valid.loc['recall'].iloc[1],
                                            auc_report_valid.loc['recall'].iloc[2],
                                            auc_report_valid.loc['support'].iloc[0], auc_report_valid.loc['support'].iloc[1],
                                            auc_report_valid.loc['support'].iloc[2]
                                            ])

            result = pd.DataFrame(result_list, columns = ["th", "dataset", "winrate", "avgret",
                                                          "precition0", "precition1", "precition2",
                                                          "recall0", "recall1", "recall2",
                                                          "support0", "support1", "support2"])
            return result


    def predict(self, dataset ,model = None):
        if not model:
            model = torch.load('/data/user/quanttest007/best_val_model_pytorch')
        auc_report,all_targets, all_predictions = self.get_label_auc_report(model, dataset)
        return auc_report


if __name__ == "__main__":
    data_params = {"num_features": 40,
                   "tag_name": "Tag5minRet",
                   "mock_data_flag": True,
                   "window": 100,
                   "random_state":100
                   }
    model_params = {'lr': 0.0001,
                    'batch_size': 128,
                    'epochs': 2}
    DeepLOBPack.run_single_instance(data_params=data_params, model_params=model_params)