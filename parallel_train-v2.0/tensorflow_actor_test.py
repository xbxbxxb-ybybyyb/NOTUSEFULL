import numpy as np
import tensorflow as tf
from parallel_train.trainer import TrainerWrapper, RayParams, SplitTaskParam
from parallel_train.backend import TensorflowBackend
import json
import os


# Actor分布式模式，继承自BackendWrapper
class TensorflowBackendActorExample(TensorflowBackend):
    def train(self, model_params):
        per_worker_batch_size = 64
        # This environment variable will be set by Ray Train.
        tf_config = json.loads(os.environ['TF_CONFIG'])
        num_workers = len(tf_config['cluster']['worker'])

        strategy = tf.distribute.MultiWorkerMirroredStrategy()

        global_batch_size = per_worker_batch_size * num_workers
        multi_worker_dataset = self.mnist_dataset(global_batch_size)

        with strategy.scope():
            # Model building/compiling need to be within `strategy.scope()`.
            multi_worker_model = self.build_and_compile_cnn_model()

        multi_worker_model.fit(multi_worker_dataset, epochs=3, steps_per_epoch=70)

    def mnist_dataset(self,batch_size):
        (x_train, y_train), _ = tf.keras.datasets.mnist.load_data()
        # The `x` arrays are in uint8 and have values in the [0, 255] range.
        # You need to convert them to float32 with values in the [0, 1] range.
        x_train = x_train / np.float32(255)
        y_train = y_train.astype(np.int64)
        train_dataset = tf.data.Dataset.from_tensor_slices(
            (x_train, y_train)).shuffle(60000).repeat().batch(batch_size)
        return train_dataset

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
    # 实例化Trainer，设置Trainer入参，已继承并实现的Backend类，任务类型，以及ray_params参数类型
    trainer = TrainerWrapper(backend=TensorflowBackendActorExample, task_mode='Actor',
                             ray_params=RayParams(cpus_per_worker=1, ))
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
