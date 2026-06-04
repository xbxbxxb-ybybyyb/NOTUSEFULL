# -*- coding: utf-8 -*-
# author: 018187
# date:   2021/8/27
import numpy as np
import NumpyModel.Layers as npl
from NumpyModel.SetTFNPWeights import set_np_conv2d_weights, set_np_lstm_weights, set_np_dense_weights, TF_WEIGHTS_NAME_LIST


class Model2Numpy(object):
    def __init__(self, input_shape):
        self.input_shape = input_shape
        self.time_steps, self.feature_num = input_shape
        self.conv2d_1, self.max_pool_1, self.conv2d_2, self.max_pool_2, self.conv2d_3 = None, None, None, None, None
        self.conv2d_a1, self.conv2d_b1, self.conv2d_b2, self.conv2d_c1, self.conv2d_c2, self.conv2d_c3 = None, None, None, None, None, None
        self.avg_pool_d1, self.conv2d_d1 = None, None
        self.max_pool_3, self.reshape_1, self.permute_1 = None, None, None
        self.lstm_1, self.lstm_2, self.lstm_3, self.lstm_4, self.lstm_5 = None, None, None, None, None
        self.dense_1, self.dense_2 = None, None

    def create_layers(self):
        self.conv2d_1 = npl.Conv2D(n_filters=32, filter_shape=(3, self.feature_num),
                                          input_shape=(1, self.time_steps, self.feature_num), padding='valid', activation='relu')
        # self.max_pool_1 = npl.MaxPooling2D(pool_shape=(2, 1), stride=(2, 1),
        #                                         input_shape=(32, self.time_steps - 2, 1), padding='same')
        self.conv2d_2 = npl.Conv2D(n_filters=32, filter_shape=(3, 1),
                                          input_shape=(32, (self.time_steps - 2) // 2, 1), padding='same', activation='relu')
        # self.max_pool_2 = npl.MaxPooling2D(pool_shape=(2, 1), stride=(2, 1),
        #                                          input_shape=(32, (self.time_steps - 2) // 2, 1), padding='same')
        self.conv2d_3 = npl.Conv2D(n_filters=64, filter_shape=(3, 1),
                                          input_shape=(32, self.time_steps // 4, 1), padding='same', activation='relu')

        self.conv2d_a1 = npl.Conv2D(n_filters=16, filter_shape=(1, 1),
                                           input_shape=(64, self.time_steps // 4, 1), padding='same', activation='relu')
        self.conv2d_b1 = npl.Conv2D(n_filters=12, filter_shape=(1, 1),
                                           input_shape=(64, self.time_steps // 4, 1), padding='same', activation='relu')
        self.conv2d_b2 = npl.Conv2D(n_filters=16, filter_shape=(5, 1),
                                           input_shape=(12, self.time_steps // 4, 1), padding='same', activation='relu')
        self.conv2d_c1 = npl.Conv2D(n_filters=16, filter_shape=(1, 1),
                                           input_shape=(64, self.time_steps // 4, 1), padding='same', activation='relu')
        self.conv2d_c2 = npl.Conv2D(n_filters=24, filter_shape=(3, 1),
                                           input_shape=(16, self.time_steps // 4, 1), padding='same', activation='relu')
        self.conv2d_c3 = npl.Conv2D(n_filters=24, filter_shape=(3, 1),
                                           input_shape=(24, self.time_steps // 4, 1), padding='same', activation='relu')
        # self.avg_pool_d1 = npl.AveragePooling2D(pool_shape=(3, 1), stride=(1, 1),
        #                                               input_shape=(64, self.time_steps // 4, 1), padding='same')
        self.conv2d_d1 = npl.Conv2D(n_filters=8, filter_shape=(1, 1),
                                           input_shape=(64, self.time_steps // 4, 1), padding='same', activation='relu')

        # self.max_pool_3 = npl.MaxPooling2D(pool_shape=(3, 1), stride=(3, 1),
        #                                          input_shape=(64, self.time_steps // 4, 1), padding='same')

        ts_window = int(np.ceil(self.time_steps / 12))
        self.reshape_1 = npl.Reshape(output_shape=(64, ts_window))
        self.permute_1 = npl.Permute(output_shape=(ts_window, 64), perm=(2, 1))
        self.lstm_1 = npl.TFLSTM(n_units=64, input_shape=(ts_window, 64), activation='softsign', recurrent_activation='sigmoid')
        self.lstm_2 = npl.TFLSTM(n_units=64, input_shape=(ts_window, 64), activation='softsign', recurrent_activation='sigmoid')
        self.lstm_3 = npl.TFLSTM(n_units=64, input_shape=(ts_window, 64), activation='softsign', recurrent_activation='sigmoid')
        self.lstm_4 = npl.TFLSTM(n_units=64, input_shape=(ts_window, 64), activation='softsign', recurrent_activation='sigmoid')
        self.lstm_5 = npl.TFLSTM(n_units=64, input_shape=(ts_window, 64), activation='softsign', recurrent_activation='sigmoid', return_sequence=False)

        self.dense_1 = npl.Dense(n_units=64, activation='relu')
        self.dense_2 = npl.Dense(n_units=1)

    def set_tf_weights(self, tf_weights_dict):
        assert set(TF_WEIGHTS_NAME_LIST) == set(tf_weights_dict.keys()), " Weights Length NOT Match "
        tf_weight_list = [tf_weights_dict[weight_name] for weight_name in TF_WEIGHTS_NAME_LIST]
        self.conv2d_1 = set_np_conv2d_weights(self.conv2d_1, tf_weight_list[:2])
        self.conv2d_2 = set_np_conv2d_weights(self.conv2d_2, tf_weight_list[2:4])
        self.conv2d_3 = set_np_conv2d_weights(self.conv2d_3, tf_weight_list[4:6])
        self.conv2d_a1 = set_np_conv2d_weights(self.conv2d_a1, tf_weight_list[6:8])
        self.conv2d_b1 = set_np_conv2d_weights(self.conv2d_b1, tf_weight_list[8:10])
        self.conv2d_b2 = set_np_conv2d_weights(self.conv2d_b2, tf_weight_list[10:12])
        self.conv2d_c1 = set_np_conv2d_weights(self.conv2d_c1, tf_weight_list[12:14])
        self.conv2d_c2 = set_np_conv2d_weights(self.conv2d_c2, tf_weight_list[14:16])
        self.conv2d_c3 = set_np_conv2d_weights(self.conv2d_c3, tf_weight_list[16:18])
        self.conv2d_d1 = set_np_conv2d_weights(self.conv2d_d1, tf_weight_list[18:20])

        self.lstm_1 = set_np_lstm_weights(self.lstm_1, (tf_weight_list[20], tf_weight_list[21]))
        self.lstm_2 = set_np_lstm_weights(self.lstm_2, (tf_weight_list[22], tf_weight_list[23]))
        self.lstm_3 = set_np_lstm_weights(self.lstm_3, (tf_weight_list[24], tf_weight_list[25]))
        self.lstm_4 = set_np_lstm_weights(self.lstm_4, (tf_weight_list[26], tf_weight_list[27]))
        self.lstm_5 = set_np_lstm_weights(self.lstm_5, (tf_weight_list[28], tf_weight_list[29]))

        self.dense_1 = set_np_dense_weights(self.dense_1, tf_weight_list[30:32])
        self.dense_2 = set_np_dense_weights(self.dense_2, tf_weight_list[32:])

    def predict(self, X):
        """"""
        x = np.expand_dims(X, axis=1)

        x  = self.conv2d_1.forward_pass(x)
        # x = self.max_pool_1.forward_pass(x)
        x = self.compute_max_pooling2(x, pool_len=2)

        x  = self.conv2d_2.forward_pass(x)
        # x = self.max_pool_2.forward_pass(x)
        x = self.compute_max_pooling2(x, pool_len=2)

        x  = self.conv2d_3.forward_pass(x)

        branch_a = self.conv2d_a1.forward_pass(x)

        branch_b = self.conv2d_b1.forward_pass(x)
        branch_b = self.conv2d_b2.forward_pass(branch_b)

        branch_c = self.conv2d_c1.forward_pass(x)
        branch_c = self.conv2d_c2.forward_pass(branch_c)
        branch_c = self.conv2d_c3.forward_pass(branch_c)

        branch_d = self.compute_average_pooling(x, pool_len=3)
        branch_d = self.conv2d_d1.forward_pass(branch_d)

        x = np.concatenate([branch_a, branch_b, branch_c, branch_d], axis=1)
        x = self.compute_max_pooling3(x, pool_len=3)

        x = self.reshape_1.forward_pass(x)
        x = self.permute_1.forward_pass(x)

        x = self.lstm_1.forward_pass(x)
        x = self.lstm_2.forward_pass(x)
        x = self.lstm_3.forward_pass(x)
        x = self.lstm_4.forward_pass(x)
        x = self.lstm_5.forward_pass(x)

        x = self.dense_1.forward_pass(x)
        out = self.dense_2.forward_pass(x)

        return np.squeeze(out)

    @staticmethod
    def compute_average_pooling(x, pool_len=3):
        branch_d = np.zeros_like(x)
        branch_d[:, :, 1:-1, :] = (x[:, :, :-2, :] + x[:, :, 1:-1, :] + x[:, :, 2:, :]) / 3
        branch_d[:, :, 0, :] = (x[:, :, 0, :] + x[:, :, 1, :]) / 2
        branch_d[:, :, -1, :] = (x[:, :, -1, :] + x[:, :, -2, :]) / 2
        return branch_d

    @staticmethod
    def compute_max_pooling2(x, pool_len=2):
        ts_window, res = x.shape[2], x.shape[2] % pool_len
        if res == 0:
            padding = ((0, 0), (0, 0), (0, 0), (0, 0))
        else:
            padding = ((0, 0), (0, 0), (0, 1), (0, 0))
        x_pad = np.pad(x, padding, mode="constant")
        pool_list = [np.expand_dims(np.max(x_pad[:, :, i * pool_len: (i + 1) * pool_len], axis=2), axis=2)
                                   for i in range((ts_window - 1) // pool_len + 1)]
        return np.concatenate(pool_list, axis=2)

    @staticmethod
    def compute_max_pooling3(x, pool_len=3):
        ts_window, res = x.shape[2], x.shape[2] % pool_len
        if res == 0:
            padding = ((0, 0), (0, 0), (0, 0), (0, 0))
        elif res == 1:
            padding = ((0, 0), (0, 0), (1, 1), (0, 0))
        else:
            padding = ((0, 0), (0, 0), (0, 1), (0, 0))
        x_pad = np.pad(x, padding, mode="constant")
        pool_list = [np.expand_dims(np.max(x_pad[:, :, i * pool_len: (i + 1) * pool_len], axis=2), axis=2)
                                   for i in range((ts_window - 1) // pool_len + 1)]
        return np.concatenate(pool_list, axis=2)
