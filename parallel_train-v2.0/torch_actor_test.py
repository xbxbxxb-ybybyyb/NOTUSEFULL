import torch
import torch.nn as nn
from parallel_train.backend import prepare_model
import torch.optim as optim
from parallel_train.backend import TorchBackend
from parallel_train.trainer import TrainerWrapper, SplitTaskParam, RayParams

num_samples = 20
input_size = 10
layer_size = 15
output_size = 5

# step1: 准备模型
class NeuralNetwork(nn.Module):
    def __init__(self):
        super(NeuralNetwork, self).__init__()
        self.layer1 = nn.Linear(input_size, layer_size)
        self.relu = nn.ReLU()
        self.layer2 = nn.Linear(layer_size, output_size)

    def forward(self, input):
        return self.layer2(self.relu(self.layer1(input)))


class TorchBackendActorExample(TorchBackend):
    def prepare_data(self, data_param):
        pass

    def train(self, model_params):
        # 使用随机数据集
        input = torch.randn(num_samples, input_size)
        labels = torch.randn(num_samples, output_size)

        num_epochs = 3
        # 实例化model
        model = NeuralNetwork()
        # 分布式训练，分布式准备模型
        model = prepare_model(model)
        loss_fn = nn.MSELoss()
        optimizer = optim.SGD(model.parameters(), lr=0.1)

        # 训练逻辑
        for epoch in range(num_epochs):
            output = model(input)
            loss = loss_fn(output, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            print(f"epoch: {epoch}, loss: {loss.item()}")


def main():
    # 选择分布式模型，或者是Task普通并行任务方式
    # 实例化Trainer，设置Trainer入参，已继承并实现的Backend类，任务类型，以及ray_params参数类型
    trainer = TrainerWrapper(backend=TorchBackendActorExample, task_mode='Actor', ray_params=RayParams(cpus_per_worker=1, ))
    # trainer开始处理，可以添加initial_hook函数
    trainer.start()
    data_params = {"train_date": SplitTaskParam(["20220418", "20220419"]),
                   "strategy_type_factor": SplitTaskParam(["factor1", "factor2"])}
    # 并行训练开始
    reports = trainer.parallel_run(model_params=None, data_params=data_params)

    # 获取训练report迭代器
    for report in reports:
        pass

    # 关闭Trainer
    trainer.shutdown()


if __name__ == "__main__":
    main()