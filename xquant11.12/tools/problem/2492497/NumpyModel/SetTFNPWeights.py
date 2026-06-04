# -*- coding: utf-8 -*-
# author: 018187
# date:   2021/8/25
import numpy as np


TF_WEIGHTS_NAME_LIST = ['ensemble_sub_0/group0/conv1/weight/Variable',
                     'ensemble_sub_0/group0/conv1/bias/Variable',
                     'ensemble_sub_0/group0/conv2/weight/Variable',
                     'ensemble_sub_0/group0/conv2/bias/Variable',
                     'ensemble_sub_0/group0/conv3/weight/Variable',
                     'ensemble_sub_0/group0/conv3/bias/Variable',
                     'ensemble_sub_0/group0/Inception1/weight/Variable',
                     'ensemble_sub_0/group0/Inception1/bias/Variable',
                     'ensemble_sub_0/group0/Inception1/weight_1/Variable',
                     'ensemble_sub_0/group0/Inception1/bias_1/Variable',
                     'ensemble_sub_0/group0/Inception1/weight_2/Variable',
                     'ensemble_sub_0/group0/Inception1/bias_2/Variable',
                     'ensemble_sub_0/group0/Inception1/weight_3/Variable',
                     'ensemble_sub_0/group0/Inception1/bias_3/Variable',
                     'ensemble_sub_0/group0/Inception1/weight_4/Variable',
                     'ensemble_sub_0/group0/Inception1/bias_4/Variable',
                     'ensemble_sub_0/group0/Inception1/weight_5/Variable',
                     'ensemble_sub_0/group0/Inception1/bias_5/Variable',
                     'ensemble_sub_0/group0/Inception1/weight_6/Variable',
                     'ensemble_sub_0/group0/Inception1/bias_6/Variable',
                     'ensemble_sub_0/lstm/multi_rnn_cell/cell_0/lstm_cell/kernel',
                     'ensemble_sub_0/lstm/multi_rnn_cell/cell_0/lstm_cell/bias',
                     'ensemble_sub_0/lstm/multi_rnn_cell/cell_1/lstm_cell/kernel',
                     'ensemble_sub_0/lstm/multi_rnn_cell/cell_1/lstm_cell/bias',
                     'ensemble_sub_0/lstm/multi_rnn_cell/cell_2/lstm_cell/kernel',
                     'ensemble_sub_0/lstm/multi_rnn_cell/cell_2/lstm_cell/bias',
                     'ensemble_sub_0/lstm/multi_rnn_cell/cell_3/lstm_cell/kernel',
                     'ensemble_sub_0/lstm/multi_rnn_cell/cell_3/lstm_cell/bias',
                     'ensemble_sub_0/lstm/multi_rnn_cell/cell_4/lstm_cell/kernel',
                     'ensemble_sub_0/lstm/multi_rnn_cell/cell_4/lstm_cell/bias',
                     'ensemble_sub_0/dnn/weight/Variable',
                     'ensemble_sub_0/dnn/bias/Variable',
                     'ensemble_sub_0/regression/weight/Variable',
                     'ensemble_sub_0/regression/bias/Variable']

## set conv weights
def set_np_conv2d_weights(np_conv2d_layer, keras_conv2d_weights):
    np_conv2d_layer.W = keras_conv2d_weights[0].transpose(3, 2, 0, 1)
    np_conv2d_layer.w0 = np.expand_dims(keras_conv2d_weights[1], axis=-1)

    return np_conv2d_layer

## set dense weights
def set_np_dense_weights(np_dense_layer, keras_dense_weights):
    np_dense_layer.W = keras_dense_weights[0]
    np_dense_layer.w0 = np.expand_dims(keras_dense_weights[1], axis=0)

    return np_dense_layer

## set lstm weights
def set_np_lstm_weights(np_lstm_layer, keras_lstm_weights):
    np_lstm_layer._kernel = keras_lstm_weights[0]
    np_lstm_layer._bias = keras_lstm_weights[1]

    return np_lstm_layer