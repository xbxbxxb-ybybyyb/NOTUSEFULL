import torch
import torch.nn as nn
import torch.optim as optim
from parallel_train.backend import BackendTaskWrapper
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

# In this example we use a randomly generated dataset.


# step2:选择分布式BackendWrapper基类，或者BackendTaskWrapper基类，并实现prepare_data与train方法
class TorchBackendTaskExample(BackendTaskWrapper):
    def prepare_data(self, data_param):
        print(data_param)

    def train(self, model_params):
        input = torch.randn(num_samples, input_size)
        labels = torch.randn(num_samples, output_size)
        num_epochs = 3
        model = NeuralNetwork()
        loss_fn = nn.MSELoss()
        optimizer = optim.SGD(model.parameters(), lr=0.1)

        for epoch in range(num_epochs):
            output = model(input)
            loss = loss_fn(output, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            print(f"epoch: {epoch}, loss: {loss.item()}")



def main():
    # 实例化Trainer，设置Trainer入参，已继承并实现的Backend类，任务类型，以及ray_params参数类型
    trainer = TrainerWrapper(backend=TorchBackendTaskExample, task_mode='Task', ray_params=RayParams(cpus_per_worker=1,))
    # trainer开始处理，可以添加initial_hook函数
    trainer.start()
    data_params = {"train_date": SplitTaskParam(["20220418", "20220419"]),
                   "strategy_type_factor": SplitTaskParam(["factor1", "factor2"])}
    # 并行训练开始
    reports = trainer.parallel_run(model_params=None, data_params=data_params)

    # 获取训练结果迭代器
    for report in reports:
        pass

    # 关闭Trainer
    trainer.shutdown()


if __name__ == "__main__":
    main()