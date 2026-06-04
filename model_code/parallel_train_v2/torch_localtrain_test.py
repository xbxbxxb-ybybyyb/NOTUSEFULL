import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from parallel_train.backend import LocalTrainBackend
from parallel_train.trainer import ParallelTrainer, SplitTaskParam, RayParams
from parallel_train import world_rank


# step1:选择分布式DistTrainBackend基类，或者LocalTrainBackend基类，并实现prepare_data与train方法
class TorchLocalBackendExample(LocalTrainBackend):
    def prepare_data(self, data_params):
        self.task_rank = world_rank()  # LocalTrain模式，获取Task的自增唯一编号
        print("task_rank:{} data_params:{}".format(self.task_rank, data_params))

    def train(self, model_params):
        class NeuralNetwork(nn.Module):
            def __init__(self, input_size,  layer_size, output_size):
                super(NeuralNetwork, self).__init__()
                self.layer1 = nn.Linear(input_size, layer_size)
                self.relu = nn.ReLU()
                self.layer2 = nn.Linear(layer_size, output_size)

            def forward(self, input):
                return self.layer2(self.relu(self.layer1(input)))

        input = torch.randn(model_params['num_samples'], model_params['input_size'])
        labels = torch.randn(model_params['num_samples'], model_params['output_size'])
        num_epochs = 3
        model = NeuralNetwork(model_params['input_size'], model_params['layer_size'], model_params['output_size'])
        loss_fn = nn.MSELoss()
        optimizer = optim.SGD(model.parameters(), lr=0.1)

        for epoch in range(num_epochs):
            output = model(input)
            loss = loss_fn(output, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        print(f"task_rank: {self.task_rank}, epoch: {epoch}, loss: {loss.item()}")
        # 返回给主程序训练结果
        return {"task_rank": self.task_rank, "epoch": epoch, "loss": loss.item(), "status": True}


def main():
    # step2: 实例化Trainer，设置Trainer入参，已继承并实现的Backend类，任务类型，以及ray_params参数类型
    trainer = ParallelTrainer(backend=TorchLocalBackendExample, task_mode='LocalTrain', 
                            ray_params=RayParams(cpus_per_worker=1))

    # step3: trainer开始处理，可以添加initial_hook函数，进行初始化操作
    trainer.start()

    # step4: 框架根据data_params配置的字典参数自动进行任务切分，SplitTaskParam类型的参数多个任务笛卡儿积切分，非SplitTaskParam参数多个任务共享
    # 如下参数被切分为四组参数：
    # {'share_factor': 'factor_share', 'train_date': '20220418', 'strategy_type_factor': 'factor1'}
    # {'share_factor': 'factor_share', 'train_date': '20220418', 'strategy_type_factor': 'factor2'}
    # {'share_factor': 'factor_share', 'train_date': '20220419', 'strategy_type_factor': 'factor1'}
    # {'share_factor': 'factor_share', 'train_date': '20220419', 'strategy_type_factor': 'factor2'}
    data_params = {"train_date": SplitTaskParam(["20220418", "20220419"]),
                   "strategy_type_factor": SplitTaskParam(["factor1", "factor2"]),
                   "share_factor": "factor_share"
                   }
    # 设置模型所需参数，透传给Backend类中train方法中的model_params所使用
    model_params = {"num_samples": 20, "input_size": 10, "layer_size": 15, "output_size": 5}
    # 并行训练开始
    return_iterator = trainer.parallel_run(model_params=model_params, data_params=data_params)

    # step5: 获取训练结果迭代器，并打印train方法中的返回值
    result_list = []
    for result in return_iterator:
        result_list.extend(result)
    print("LocalTrain模式汇总的训练结果为：")
    print(pd.DataFrame(result_list))

    # step6: 关闭Trainer
    trainer.shutdown()


if __name__ == "__main__":
    main()