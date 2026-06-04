import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import ToTensor
import pandas as pd
from parallel_train import world_size, world_rank, local_rank, report
from parallel_train.backend import TorchBackend, prepare_model, prepare_data_loader
from parallel_train.trainer import ParallelTrainer, SplitTaskParam, RayParams


# 定义模型
class NeuralNetwork(nn.Module):
    def __init__(self):
        super(NeuralNetwork, self).__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28 * 28, 512), nn.ReLU(), nn.Linear(512, 512), nn.ReLU(),
            nn.Linear(512, 10), nn.ReLU())

    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits

# step1 继承并实现LocalTrainBackend或者分布式Backend，此处继承并实现了TorchBackend，训练FashionMNIST
class TorchDistBackendExample(TorchBackend):

    def prepare_data(self, data_params):
        # 设置数据集
        self.training_data = datasets.MNIST(root="~/.keras/datasets", train=True, download=True, transform=ToTensor())
        self.test_data = datasets.MNIST(root="~/.keras/datasets", train=False, download=True, transform=ToTensor())
        self.world_rank = world_rank()#DistTrain模式，获取worker的编号，world_rank一对一绑定一个worker，可按需按world_rank绑定处理逻辑
        self.train_date = data_params["train_date"]
        print(f"world_rank {self.world_rank}, data_params: {data_params}")


    def train(self, model_params):
        # 获取model_params中透传的参数
        batch_size = model_params["batch_size"]
        lr = model_params["lr"]
        epochs = model_params["epochs"]

        # 分布式改造1：使用prepare_data_loader辅助函数将数据集转换为分布式数据集
        worker_batch_size = batch_size // world_size()       # 分布式训练下，每个step原本的batch_size分摊给各个worker，world_size()为worker的个数
        train_dataloader = DataLoader(self.training_data, batch_size=worker_batch_size)
        test_dataloader = DataLoader(self.test_data, batch_size=worker_batch_size)
        train_dataloader = prepare_data_loader(train_dataloader)
        test_dataloader = prepare_data_loader(test_dataloader)

        # 分布式改造2： 使用prepare_model将模型自动转换为分布式模型
        model = NeuralNetwork()
        model = prepare_model(model)

        loss_fn = nn.CrossEntropyLoss()
        optimizer = torch.optim.SGD(model.parameters(), lr=lr)

        loss_results = []
        for epoch in range(epochs):
            self.train_epoch(train_dataloader, model, loss_fn, optimizer, epoch)
            loss = self.validate_epoch(test_dataloader, model, loss_fn)
            #分布式改造3（可选）：将训练过程中数据回传给主程序，可在主程序中汇总各个worker的结果
            report(loss=loss, world_rank = self.world_rank)
            loss_results.append(loss)
        #DistTrain无返回值，通过paralel_train.report函数回传数据
        return

    def train_epoch(self, dataloader, model, loss_fn, optimizer, epoch):
        size = len(dataloader.dataset) // world_size()
        model.train()
        for batch, (X, y) in enumerate(dataloader):
            # Compute prediction error
            pred = model(X)
            loss = loss_fn(pred, y)

            # Backpropagation
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        loss, current = loss.item(), batch * len(X)
        print(f"world_rank: {self.world_rank}, Epoch: {epoch}, Train Loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")

    def validate_epoch(self, dataloader, model, loss_fn):
        size = len(dataloader.dataset) // world_size()
        num_batches = len(dataloader)
        model.eval()
        test_loss, correct = 0, 0
        with torch.no_grad():
            for X, y in dataloader:
                pred = model(X)
                test_loss += loss_fn(pred, y).item()
                correct += (pred.argmax(1) == y).type(torch.float).sum().item()
        test_loss /= num_batches
        correct /= size
        print(f"world_rank: {self.world_rank}, Valid Accuracy: {(100 * correct):>0.1f}%, Avg loss: {test_loss:>8f}. ")
        return test_loss


def main():
    # step2: 实例化Trainer，设置Trainer入参，已继承并实现的Backend类，任务类型（DistTrain or LocalTrain），以及ray_params参数类型
    trainer = ParallelTrainer(backend=TorchDistBackendExample,
                              task_mode='DistTrain',
                              ray_params=RayParams(cpus_per_worker=1, gpus_per_worker=1))

    # step3: trainer开始处理，可以添加initial_hook函数
    def initial_hook():
        import os
        os.system("pip install -U --trusted-host 168.7.17.225 -i http://168.7.17.225:8081/repository/pypi/simple/ pip")
        os.system("pip install -U --trusted-host 168.7.17.225 -i http://168.7.17.225:8081/repository/pypi/simple/ aiohttp==3.7.4")
        os.system("pip install -U --trusted-host 168.7.17.225 -i http://168.7.17.225:8081/repository/pypi/simple/ ray==1.5.2")
    trainer.start(initialization_hook = initial_hook)

    # step4: 设置data_params进行数据参数切分，如下被切分为两组参数，share_factor为共享参数
    # {'share_factor': 'factor_share', 'train_date': '20220418', 'strategy_type_factor': 'factor1'}
    # {'share_factor': 'factor_share', 'train_date': '20220419', 'strategy_type_factor': 'factor1'}
    data_params = {"train_date": SplitTaskParam(["20220418", "20220419"]),
                   "strategy_type_factor": "factor1",
                   "share_factor": "factor_share"}
    # 模型参数
    model_params = {"lr": 1e-3, "batch_size": 64, "epochs": 4}
    callback_iterator = trainer.parallel_run(model_params=model_params, data_params=data_params)

    # step5: 异步返回worker的回调信息，若worker中有调用parallel_train.report方法发送信息，可在此主程序中获取到。
    for result in callback_iterator:
        print("获取parallel_train.report方法传递的回调结果：")
        print(pd.DataFrame(result))

    # step6: 关闭Trainer
    trainer.shutdown()


if __name__ == "__main__":
    main()
