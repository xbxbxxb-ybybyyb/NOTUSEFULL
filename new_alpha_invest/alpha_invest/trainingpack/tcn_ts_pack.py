# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
from __future__ import division
from __future__ import print_function

import numpy as np
import pandas as pd
import copy

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from alpha_invest.trainingpack.models.pytorch_utils import count_parameters, get_or_create_path
from alpha_invest.trainingpack.models.tcn import TemporalConvNet
from alpha_invest.datasets.dataset_loader import DatasetLoader
from alpha_invest.datasets.dataset_manager import DataSetManager, PurgedGroupTimeSeriesSplit
from alpha_invest import alpha_logger as get_module_logger

from parallel_train.backend import LocalTrainBackend


class TcnTsPack(LocalTrainBackend):
    """TCN Model
    Parameters
    ----------
    d_feat : int
        input dimension for each time step
    metric: str
        the evaluate metric used in early stop
    optimizer : str
        optimizer name
    GPU : str
        the GPU ID(s) used for training
    """
    def __init__(self, n_jobs=10, GPU=0, seed=None, **kwargs):
        # Set logger.
        self.logger = get_module_logger

        self.device = torch.device("cuda:%d" % (GPU) if torch.cuda.is_available() and GPU >= 0 else "cpu")
        self.n_jobs = n_jobs
        self.seed = seed

        if self.seed is not None:
            np.random.seed(self.seed)
            torch.manual_seed(self.seed)


    def prepare_data(self, data_params):
        dloader = DatasetLoader()
        dloader.load_factor_data(factor_path=data_params["factor_path"],
                                 mock_data_flag=data_params["mock_data_flag"], num_features=data_params["num_features"],
                                 tag_name=data_params["tag_name"])
        self.factor_data_train, self.factor_data_test, self.label_data_train, self.label_data_test = dloader.train_test_split(
            train_test_split_date="20220601")
        # self.factor_data_train, self.factor_data_valid, self.label_data_train, self.label_data_valid = dloader.train_test_split(
        #     train_test_split_date="20220401", factor_data=self.factor_data_train, label_data=self.label_data_train)

        data_window = data_params.pop("window")
        self.data_window = data_window
        self.num_features = data_params["num_features"]
        dmanager_train = DataSetManager(self.factor_data_train, self.label_data_train, data_type='tick')
        dataset_train = dmanager_train.transform_torch_dataset_ts(window=data_window)
        train_size = int(0.8 * len(dataset_train))
        valid_size = len(dataset_train) - train_size
        dataset_train, dataset_val = torch.utils.data.random_split(dataset_train, [train_size, valid_size])
        print("prepare_data, dataset_train shape:", len(dataset_train.indices), "dataset_val shape:",
              len(dataset_val.indices))

        dataset_test = DataSetManager(self.factor_data_test, self.label_data_test, data_type='tick')
        dataset_test = dataset_test.transform_torch_dataset_ts(window=data_window)
        self.train_dataset, self.valid_dataset, self.test_dataset = dataset_train, dataset_val, dataset_test


    def train_loop(self, model_params):
        d_feat = 6
        n_chans = 128
        kernel_size = 5
        num_layers = 2
        dropout = 0.0
        n_epochs = 200
        lr = 0.001
        metric = ""
        batch_size = 3000
        early_stop = 20
        loss = "mse"
        optimizer = "adam"
        save_path='./tmp'
        evals_result=dict()



        self.d_feat = d_feat
        self.n_chans = n_chans
        self.kernel_size = kernel_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.n_epochs = n_epochs
        self.lr = lr
        self.metric = metric
        self.batch_size = batch_size
        self.early_stop = early_stop
        self.optimizer = optimizer.lower()
        self.loss = loss

        self.TCN_model = TCNModel(
            num_input=self.d_feat,
            output_size=1,
            num_channels=[self.n_chans] * self.num_layers,
            kernel_size=self.kernel_size,
            dropout=self.dropout,
        )
        if optimizer.lower() == "adam":
            self.train_optimizer = optim.Adam(self.TCN_model.parameters(), lr=self.lr)
        elif optimizer.lower() == "gd":
            self.train_optimizer = optim.SGD(self.TCN_model.parameters(), lr=self.lr)
        else:
            raise NotImplementedError("optimizer {} is not supported!".format(optimizer))
        self.logger.info("model:\n{:}".format(self.TCN_model))
        self.logger.info("model size: {:.4f} MB".format(count_parameters(self.TCN_model)))

        self.fitted = False
        self.TCN_model.to(self.device)

        save_path = get_or_create_path(save_path)

        stop_steps = 0
        train_loss = 0
        best_score = -np.inf
        best_epoch = 0
        evals_result["train"] = []
        evals_result["valid"] = []

        # train
        self.logger.info("training...")
        self.fitted = True


        self.train_loader = DataLoader(
            self.train_dataset, batch_size=self.batch_size, shuffle=True, num_workers=self.n_jobs, drop_last=True
        )
        self.valid_loader = DataLoader(
            self.valid_dataset, batch_size=self.batch_size, shuffle=False, num_workers=self.n_jobs, drop_last=True
        )

        for step in range(self.n_epochs):
            self.logger.info("Epoch%d:", step)
            self.logger.info("training...")
            self.train_epoch(self.train_loader)
            self.logger.info("evaluating...")
            train_loss, train_score = self.test_epoch(self.train_loader)
            val_loss, val_score = self.test_epoch(self.valid_loader)
            self.logger.info("train %.6f, valid %.6f" % (train_score, val_score))
            evals_result["train"].append(train_score)
            evals_result["valid"].append(val_score)

            if val_score > best_score:
                best_score = val_score
                stop_steps = 0
                best_epoch = step
                best_param = copy.deepcopy(self.TCN_model.state_dict())
            else:
                stop_steps += 1
                if stop_steps >= self.early_stop:
                    self.logger.info("early stop")
                    break

        self.logger.info("best score: %.6lf @ %d" % (best_score, best_epoch))
        self.TCN_model.load_state_dict(best_param)
        torch.save(best_param, save_path)

        if self.use_gpu:
            torch.cuda.empty_cache()

    def predict(self, dataset):
        if not self.fitted:
            raise ValueError("model is not fitted yet!")

        self.test_loader = DataLoader(
            self.test_dataset, batch_size=self.batch_size, shuffle=False, num_workers=self.n_jobs, drop_last=True
        )
        self.TCN_model.eval()
        preds = []

        for data in self.test_loader:
            feature = data[:, :, 0:-1].to(self.device)
            with torch.no_grad():
                pred = self.TCN_model(feature.float()).detach().cpu().numpy()
            preds.append(pred)

        return pd.Series(np.concatenate(preds))

    def train_epoch(self, data_loader):
        self.TCN_model.train()
        for data in data_loader:
            feature = data[0].to(self.device)
            label = data[1].to(self.device)

            pred = self.TCN_model(feature.float())
            loss = self.loss_fn(pred, label)

            self.train_optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_value_(self.TCN_model.parameters(), 3.0)
            self.train_optimizer.step()

    def test_epoch(self, data_loader):
        self.TCN_model.eval()
        scores = []
        losses = []

        for data in data_loader:
            feature = data[0].to(self.device)
            # feature[torch.isnan(feature)] = 0
            label = data[1].to(self.device)

            with torch.no_grad():
                pred = self.TCN_model(feature.float())
                loss = self.loss_fn(pred, label)
                losses.append(loss.item())

                score = self.metric_fn(pred, label)
                scores.append(score.item())

        return np.mean(losses), np.mean(scores)


    @property
    def use_gpu(self):
        return self.device != torch.device("cpu")

    def mse(self, pred, label):
        loss = (pred - label) ** 2
        return torch.mean(loss)

    def loss_fn(self, pred, label):
        mask = ~torch.isnan(label)

        if self.loss == "mse":
            return self.mse(pred[mask], label[mask])

        raise ValueError("unknown loss `%s`" % self.loss)

    def metric_fn(self, pred, label):

        mask = torch.isfinite(label)

        if self.metric == "" or self.metric == "loss":
            return -self.loss_fn(pred[mask], label[mask])

        raise ValueError("unknown metric `%s`" % self.metric)



class TCNModel(nn.Module):
    def __init__(self, num_input, output_size, num_channels, kernel_size, dropout):
        super().__init__()
        self.num_input = num_input
        self.tcn = TemporalConvNet(num_input, num_channels, kernel_size, dropout=dropout)
        self.linear = nn.Linear(num_channels[-1], output_size)

    def forward(self, x):
        output = self.tcn(x)
        output = self.linear(output[:, :, -1])
        return output.squeeze()


if __name__=="__main__":
    data_params = {"factor_path":"/data/user/quanttest007/alpha_invest/merge_data.pkl",
                    "num_features":20,
                   'window':20,
                   "tag_name": "tag5minLong",
                   "mock_data_flag":True,
                   'max_train_group_size':450, #训练集包含的天数
                   }
    model_params = {
    }
    TcnTsPack.run_single_instance(data_params=data_params, model_params= model_params)
