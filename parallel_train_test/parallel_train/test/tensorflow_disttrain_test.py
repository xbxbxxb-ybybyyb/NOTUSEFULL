import numpy as np
import pandas as pd
import tensorflow as tf
import json
import os
from parallel_train.trainer import ParallelTrainer, RayParams, SplitTaskParam
from parallel_train.backend import TensorflowBackend
from parallel_train import world_size, world_rank, local_rank, report


# step1: DistTrain分布式模式，继承自TensorflowBackend
class TensorflowDistBackendExample(TensorflowBackend):
    def prepare_data(self, data_params):
        # 设置数据集
        self.x_train, self.y_train = self.mnist_dataset()
        self.world_rank = world_rank()#DistTrain模式，获取worker的编号，world_rank一对一绑定一个worker，可按需按world_rank绑定处理逻辑
        print(f"world_rank {self.world_rank}, data_params: {data_params}")

    def train(self, model_params):
        # TF_CONFIG为分布式TF的必要环境变量，已有框架自动完成设置。
        tf_config = json.loads(os.environ['TF_CONFIG'])
        num_workers = len(tf_config['cluster']['worker'])

        per_worker_batch_size = model_params["per_worker_batch_size"]
        epochs = model_params["epochs"]
        steps_per_epoch = model_params["steps_per_epoch"]
        global_batch_size = per_worker_batch_size * num_workers

        # 分布式改造1： 必须将模型放入MultiWorkerMirroredStrategy会话中定义，以保证各个worker协同训练；否则每个worker各自训练一个完整模型
        strategy = tf.distribute.MultiWorkerMirroredStrategy()
        with strategy.scope():
            print(f"world_rank {self.world_rank}: build and compile_cnn_model...")
            multi_worker_model = self.build_and_compile_cnn_model()

        self.multi_worker_dataset = tf.data.Dataset.from_tensor_slices((self.x_train, self.y_train)).shuffle(60000).repeat().batch(global_batch_size)
        history = multi_worker_model.fit(self.multi_worker_dataset, epochs=epochs, steps_per_epoch=steps_per_epoch)

        # 分布式改造2（可选）：将训练过程中数据回传给主程序，可在主程序中汇总各个worker的结果
        # print(self.world_rank)
        report(world_rank1 = self.world_rank, loss = history.history['loss'][-1])

        # DistTrain无返回值，通过paralel_train.report函数回传数据
        return

    def mnist_dataset(self):
        (x_train, y_train), _ = tf.keras.datasets.mnist.load_data()
        # The `x` arrays are in uint8 and have values in the [0, 255] range.
        # You need to convert them to float32 with values in the [0, 1] range.
        x_train = x_train / np.float32(255)
        y_train = y_train.astype(np.int64)
        return x_train, y_train

    def build_and_compile_cnn_model(self):
        model = tf.keras.Sequential([
            tf.keras.layers.InputLayer(input_shape=(28, 28)),
            tf.keras.layers.Reshape(target_shape=(28, 28, 1)),
            tf.keras.layers.Conv2D(32, 3, activation='relu'),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(10)
        ])
        model.compile(
            loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            optimizer=tf.keras.optimizers.SGD(learning_rate=0.001),
            metrics=['accuracy'])
        return model


if __name__ == "__main__":
    # step2: 实例化Trainer，设置Trainer入参，已继承并实现的Backend类，任务类型，以及ray_params参数类型
    trainer = ParallelTrainer(backend=TensorflowDistBackendExample, task_mode='DistTrain',
                             ray_params=RayParams(cpus_per_worker=1, ))
    # step3: 可以添加initial_hook函数
    trainer.start()

    # step4: 框架根据data_params配置的字典参数自动进行任务切分，SplitTaskParam类型的参数多个任务笛卡儿积切分，非SplitTaskParam参数多个任务共享
    # 如下参数被切分为两组组参数：
    # {'share_factor': 'factor_share', 'train_date': '20220418', 'strategy_type_factor': 'factor1'}
    # {'share_factor': 'factor_share', 'train_date': '20220418', 'strategy_type_factor': 'factor2'}
    data_params = {"train_date": SplitTaskParam(["20220418", "20220419"]),
                   "strategy_type_factor": SplitTaskParam(["factor1"]),
                   "share_factor": "factor_share"}
    # 分布式并行训练开始，在tensorflow 2.x版本下运行
    model_params = {"per_worker_batch_size": 64, "epochs":3, "steps_per_epoch":10}
    callback_iterator = trainer.parallel_run(model_params=model_params, data_params=data_params)

    # step5： 异步返回worker的回调信息，若worker中有调用parallel_train.report方法发送信息，可在此主程序中获取到
    for result in callback_iterator:
        print("获取parallel_train.report方法传递的回调结果：")
        print(pd.DataFrame(result))

    # step6: 关闭Trainer
    trainer.shutdown()
