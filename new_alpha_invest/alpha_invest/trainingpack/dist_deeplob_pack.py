from xquant.model.parallel_train.session import world_size, world_rank, local_rank, report
from xquant.model.parallel_train.backend import TorchBackend, prepare_model, prepare_data_loader
from alpha_invest.datasets.dataset_loader import DatasetLoader
from alpha_invest.datasets.dataset_manager import DataSetManager, PurgedGroupTimeSeriesSplit
import numpy as np
import torch
from torch.utils import data
from torchinfo import summary
import torch.nn as nn
from datetime import datetime
import torch.optim as optim
from sklearn.metrics import accuracy_score, classification_report
from tqdm import tqdm

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(device)

class deeplob(nn.Module):
    def __init__(self, y_len):
        super().__init__()
        self.y_len = y_len

        # convolution blocks
        self.conv1 = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=32, kernel_size=(1, 2), stride=(1, 2)),
            nn.LeakyReLU(negative_slope=0.01),
            #             nn.Tanh(),
            nn.BatchNorm2d(32),
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=(4, 1)),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(32),
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=(4, 1)),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(32),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=(1, 2), stride=(1, 2)),
            nn.Tanh(),
            nn.BatchNorm2d(32),
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=(4, 1)),
            nn.Tanh(),
            nn.BatchNorm2d(32),
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=(4, 1)),
            nn.Tanh(),
            nn.BatchNorm2d(32),
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=(1, 10)),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(32),
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=(4, 1)),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(32),
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=(4, 1)),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(32),
        )

        # inception moduels
        self.inp1 = nn.Sequential(
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=(1, 1), padding='same'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(64),
            nn.Conv2d(in_channels=64, out_channels=64, kernel_size=(3, 1), padding='same'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(64),
        )
        self.inp2 = nn.Sequential(
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=(1, 1), padding='same'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(64),
            nn.Conv2d(in_channels=64, out_channels=64, kernel_size=(5, 1), padding='same'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(64),
        )
        self.inp3 = nn.Sequential(
            nn.MaxPool2d((3, 1), stride=(1, 1), padding=(1, 0)),
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=(1, 1), padding='same'),
            nn.LeakyReLU(negative_slope=0.01),
            nn.BatchNorm2d(64),
        )

        # lstm layers
        self.lstm = nn.LSTM(input_size=192, hidden_size=64, num_layers=1, batch_first=True)
        self.fc1 = nn.Linear(64, self.y_len)

    def forward(self, x):
        # h0: (number of hidden layers, batch size, hidden size)
        h0 = torch.zeros(1, x.size(0), 64).to(device)
        c0 = torch.zeros(1, x.size(0), 64).to(device)

        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)

        x_inp1 = self.inp1(x)
        x_inp2 = self.inp2(x)
        x_inp3 = self.inp3(x)

        x = torch.cat((x_inp1, x_inp2, x_inp3), dim=1)

        #         x = torch.transpose(x, 1, 2)
        x = x.permute(0, 2, 1, 3)
        x = torch.reshape(x, (-1, x.shape[1], x.shape[2]))

        x, _ = self.lstm(x, (h0, c0))
        x = x[:, -1, :]
        x = self.fc1(x)
        forecast_y = torch.softmax(x, dim=1)

        return forecast_y

class DistDeepLOBPack(TorchBackend):
    def __init__(self):
        pass

    def prepare_data(self, data_params):
        dloader = DatasetLoader()
        dloader.load_factor_data()
        self.factor_data_train, self.factor_data_test, self.label_data_train, self.label_data_test = dloader.train_test_split(
            train_split_ratio=0.9)


        data_window = data_params.pop("window")
        dmanager_train = DataSetManager(self.factor_data_train, self.label_data_train, data_type = 'tick')
        dataset_train = dmanager_train.transform_torch_dataset_ts(window=data_window)
        train_size = int(0.8 * len(dataset_train))
        valid_size = len(dataset_train) - train_size
        dataset_train, dataset_val = torch.utils.data.random_split(dataset_train, [train_size, valid_size])
        print("prepare_data, dataset_train shape:", len(dataset_train.indices), "dataset_val shape:",
              len(dataset_val.indices))

        dataset_train.k = 4
        dataset_train.num_classes = 3
        dataset_train.T = 100

        dataset_val.k = 4
        dataset_val.num_classes = 3
        dataset_val.T = 100

        dataset_test = DataSetManager(self.factor_data_test, self.label_data_test, data_type='tick')
        dataset_test = dataset_test.transform_torch_dataset_ts(window=100)
        dataset_test.k = 4
        dataset_test.num_classes = 3
        dataset_test.T = 100

        self.dataset_train, self.dataset_val, self.dataset_test = dataset_train, dataset_val, dataset_test

    def train_loop(self, model_params):
        import sys
        sys.path.append("/data/user/013150")
        from ray import tune

        batch_size = model_params.pop("batch_size")
        lr = model_params.pop("lr")
        epochs = model_params.pop("epochs")

        # 分布式改造1：使用prepare_data_loader辅助函数将数据集转换为分布式数据集
        worker_batch_size = batch_size // world_size()  # 分布式训练下，每个step原本的batch_size分摊给各个worker，world_size()为worker的个数
        train_loader = torch.utils.data.DataLoader(dataset=self.dataset_train, batch_size=worker_batch_size, shuffle=True)
        val_loader = torch.utils.data.DataLoader(dataset=self.dataset_val, batch_size=worker_batch_size, shuffle=False)

        train_loader = prepare_data_loader(train_loader)
        val_loader = prepare_data_loader(val_loader)

        model = deeplob(y_len=self.dataset_train.num_classes)
        model = prepare_model(model)
        model.to(device)
        summary(model, (1, 1, 100, 40))

        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)

        train_losses = np.zeros(epochs)
        test_losses = np.zeros(epochs)
        best_test_loss = np.inf
        best_test_epoch = 0

        for it in tqdm(range(epochs)):

            model.train()
            t0 = datetime.now()
            train_loss = []
            for inputs, targets in train_loader:
                # move data to GPU
                inputs, targets = inputs.to(device, dtype=torch.float), targets.to(device, dtype=torch.int64)
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
            test_loss = []
            all_targets = []
            all_predictions = []

            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device, dtype=torch.float), targets.to(device, dtype=torch.int64)
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                test_loss.append(loss.item())

                _, predictions = torch.max(outputs, 1)
                all_predictions.append(predictions.cpu().numpy())
                all_targets.append(targets.cpu().numpy())

            all_targets = np.concatenate(all_targets)
            all_predictions = np.concatenate(all_predictions)
            test_loss = np.mean(test_loss)

            # Save losses
            train_losses[it] = train_loss
            test_losses[it] = test_loss

            if test_loss < best_test_loss:
                torch.save(model, '/tmp/best_val_model_pytorch')
                best_test_loss = test_loss
                best_test_epoch = it
                print('model saved')

            dt = datetime.now() - t0
            score = accuracy_score(all_targets, all_predictions)
            print(f'Epoch {it + 1}/{epochs}, accuracy_score: {score}, Train Loss: {train_loss:.4f}, \
            Validation Loss: {test_loss:.4f}, Duration: {dt}, Best Val Epoch: {best_test_epoch}')
        tune.report(train_losses=train_losses, test_losses=test_losses)
        self.predict()

    def predict(self, model = None):
        if not model:
            model = torch.load('/tmp/best_val_model_pytorch')
        all_targets = []
        all_predictions = []

        test_loader = torch.utils.data.DataLoader(dataset=self.dataset_test, batch_size=128, shuffle=False)
        for inputs, targets in test_loader:
            # Move to GPU
            inputs, targets = inputs.to(device, dtype=torch.float), targets.to(device, dtype=torch.int64)

            # Forward pass
            outputs = model(inputs)

            # Get prediction
            # torch.max returns both max and argmax
            _, predictions = torch.max(outputs, 1)

            all_targets.append(targets.cpu().numpy())
            all_predictions.append(predictions.cpu().numpy())

        all_targets = np.concatenate(all_targets)
        all_predictions = np.concatenate(all_predictions)

        print('accuracy_score:', accuracy_score(all_targets, all_predictions))
        print(classification_report(all_targets, all_predictions, digits=4))

if __name__ == "__main__":
    model_params = {'lr': 0.0001,
                    'batch_size': 64,
                    'epochs': 2}
    DistDeepLOBPack.run_single_instance(data_params={"window":50}, model_params=model_params)