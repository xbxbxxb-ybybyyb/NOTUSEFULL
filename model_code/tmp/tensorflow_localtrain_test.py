import numpy as np
import tensorflow as tf
import pandas as pd
from parallel_train.trainer import ParallelTrainer, RayParams, SplitTaskParam
from parallel_train.backend import LocalTrainBackend
from parallel_train import world_rank


# step1: LocalTrain模式继承LocalTrainBackend
class TensorflowLocalBackendExample(LocalTrainBackend):
    def prepare_data(self, data_params):
        self.task_rank = world_rank()  # LocalTrain模式，获取Task的自增唯一编号
        print(f"world_rank {self.task_rank}, data_params: {data_params}")

    def train(self, model_params):
        batch_size = model_params["batch_size"]
        epochs = model_params["epochs"]
        steps_per_epoch = model_params["steps_per_epoch"]

        single_worker_dataset = self.mnist_dataset(batch_size)
        single_worker_model = self.build_and_compile_cnn_model()
        history = single_worker_model.fit(single_worker_dataset, epochs=epochs, steps_per_epoch=steps_per_epoch)
        #返回给主程序训练结果
        return {"task_rank": self.task_rank, "loss":history.history['loss'][-1],  "status": True}

    def mnist_dataset(self, batch_size):
        (x_train, y_train), _ = tf.keras.datasets.mnist.load_data()
        # The `x` arrays are in uint8 and have values in the [0, 255] range.
        # You need to convert them to float32 with values in the [0, 1] range.
        x_train = x_train / np.float32(255)
        y_train = y_train.astype(np.int64)
        train_dataset = tf.data.Dataset.from_tensor_slices(
            (x_train, y_train)).shuffle(60000).repeat().batch(batch_size)
        return train_dataset

    @staticmethod
    def build_and_compile_cnn_model():
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
    trainer = ParallelTrainer(backend=TensorflowLocalBackendExample,
                              task_mode='LocalTrain',
                              ray_params=RayParams(cpus_per_worker=1, ))
    # step3: trainer开始处理，可以添加initial_hook函数
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
    model_params = {"batch_size":64, "epochs":3, "steps_per_epoch": 70}
    # 并行训练开始，在tensorflow 2.x版本下运行
    return_iterator = trainer.parallel_run(model_params=model_params, data_params=data_params)

    # step5: 异步获取每个Task的train方法中的返回值，直到所有Task全部完成
    result_list = []
    for result in return_iterator:
        result_list.extend(result)

    print("LocalTrain模式汇总的训练结果为：")
    print(pd.DataFrame(result_list))

    # step:6 关闭Trainer
    trainer.shutdown()
