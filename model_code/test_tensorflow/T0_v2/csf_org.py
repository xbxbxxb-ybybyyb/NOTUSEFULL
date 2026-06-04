
import os
os.system("nvidia-smi")
import sys
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../"))

import tensorflow as tf
import numpy as np
import re
import time
#from tensorflow.contrib import rnn
from tensorflow.python.ops import rnn
from data_list_queue_org import Data
from Logger import Logger
#from xquant.model.tracking import auto_log, log_metrics
tf.compat.v1.disable_eager_execution()


def DeepNet(x, image_len, factor_num, dnn_keepProb):
    with tf.compat.v1.variable_scope('reshape'):
        x_image = tf.reshape(x, [-1, image_len, factor_num, 1])

    with tf.compat.v1.variable_scope('conv1'):
        W_conv1 = weight_variable([3, 3, 1, 16])
        b_conv1 = bias_variable([16])
        h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1, [1, 1], 'VALID') + b_conv1)

    with tf.compat.v1.variable_scope('pool1'):
        h_pool1 = max_pool(h_conv1, [3, 3], [3, 3], 'SAME')

    with tf.compat.v1.variable_scope('conv2'):
        W_conv2 = weight_variable([3, 1, 16, 32])
        b_conv2 = bias_variable([32])
        h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2, [1, 1], 'SAME') + b_conv2)

    with tf.compat.v1.variable_scope('pool2'):
        h_pool2 = max_pool(h_conv2, [3, 3], [3, 3], 'SAME')

    with tf.compat.v1.variable_scope('conv3'):
        W_conv3 = weight_variable([3, 1, 32, 64])
        b_conv3 = bias_variable([64])
        h_conv3 = tf.nn.relu(conv2d(h_pool2, W_conv3, [1, 1], 'SAME') + b_conv3)

    with tf.compat.v1.variable_scope('pool3'):
        h_pool3 = max_pool(h_conv3, [3, 3], [3, 3], 'SAME')

    with tf.compat.v1.name_scope('conv4'):
        w_4_1 = weight_variable([1, 1, 64, 32])
        b_4_1 = bias_variable([32])
        out1 = tf.nn.relu(conv2d(h_pool3, w_4_1, [1, 1], 'SAME') + b_4_1)
        w_4_2 = weight_variable([3, 1, 64, 64])
        b_4_2 = bias_variable([64])
        out2 = tf.nn.relu(conv2d(h_pool3, w_4_2, [1, 1], 'SAME') + b_4_2)

        w_4_3 = weight_variable([1, 1, 64, 32])
        b_4_3 = bias_variable([32])
        out3 = tf.nn.relu(conv2d(h_pool3, w_4_3, [1, 1], 'SAME') + b_4_3)
        h_conv4 = tf.concat([out1, out2, out3], 3)

    with tf.compat.v1.variable_scope('pool4'):
        h_pool4 = max_pool(h_conv4, [3, 3], [3, 3], 'SAME')

    with tf.compat.v1.variable_scope('fc1'):
        shape = h_pool4._shape_tuple()
        fc1 = tf.reshape(h_pool4, [-1, shape[1] * shape[2] * shape[3]])

    with tf.compat.v1.variable_scope('out'):
        w_out = weight_variable([fc1._shape_tuple()[1], 1])
        b_out = bias_variable([1])
        out = tf.matmul(fc1, w_out) + b_out
        out = tf.nn.dropout(out, 1 - (dnn_keepProb))

    return out


def conv2d(x, W, strides, padding):
    return tf.nn.conv2d(input=x, filters=W, strides=[1, strides[0], strides[1], 1], padding=padding)


def max_pool(x, shape, strides, padding):
    return tf.nn.max_pool2d(input=x, ksize=[1, shape[0], shape[1], 1],
                          strides=[1, strides[0], strides[1], 1], padding=padding)


def avg_pool(x, shape, strides, padding):
    return tf.nn.avg_pool2d(input=x, ksize=[1, shape[0], shape[1], 1],
                          strides=[1, strides[0], strides[1], 1], padding=padding)


def weight_variable(shape, numVariable=None):
    with tf.compat.v1.variable_scope('weight'):
        # initializer = tf.contrib.layers.xavier_initializer()
        # var = tf.Variable(initializer(shape))
        var = tf.Variable(tf.random.truncated_normal(shape, stddev=0.1))
        if numVariable is not None:
            numVariable[0] += np.prod(shape)
        return var


def bias_variable(shape, numVariable=None):
    with tf.compat.v1.variable_scope('bias'):
        initial = tf.constant(0.1, shape=shape)
        if numVariable is not None:
            numVariable[0] += np.prod(shape)
        return tf.Variable(initial)


t1 = time.time()
# Create the model
slice_lag = 300
factor_num = 200
l2_rate = 0.1
lr = 0.1
train_num = int(1e6)
valid_num = int(5e4)
epo_num = 10
batch_size = 512
config = tf.compat.v1.ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = 0.25
factor_group = [[0, factor_num]]
train_label = np.random.random_sample((train_num, 1))
train_data = np.random.random_sample((train_num, factor_num))
with tf.compat.v1.variable_scope("DeepNet"):
    x = tf.compat.v1.placeholder(tf.float32, [None, slice_lag, factor_num], name='x')
    y = tf.compat.v1.placeholder(tf.float32, [None, 1], name='y')
    # dnn_keepProb = tf.placeholder(tf.float32, name='dnn_keepProb')
    # Build the graph for the deep net
    numVariable = [0]
    y_regression =  DeepNet(x, slice_lag, factor_num, 0.8)
    numVariable = numVariable[0]

    with tf.compat.v1.variable_scope('rmse'):
        mses = tf.pow(tf.subtract(y, y_regression), 2)
        rmse = tf.sqrt(tf.reduce_mean(input_tensor=mses))

    trainable_vars = tf.compat.v1.trainable_variables()
    variables_to_regularization = []

    for v in trainable_vars:
        if (re.match(r'.*weight*', v.name)):
            variables_to_regularization.append(v)

    with tf.compat.v1.variable_scope('regularization_loss'):
        loss_regularization = l2_rate * tf.reduce_sum(
            input_tensor=[tf.nn.l2_loss(v) for v in variables_to_regularization])

    with tf.compat.v1.variable_scope('loss'):
        loss = loss_regularization + rmse

    with tf.compat.v1.name_scope('adam_optimizer'):
        train_step = tf.compat.v1.train.AdamOptimizer(learning_rate=lr).minimize(loss)

log_file_path =  "/tmp"
log_err_file = log_file_path + "/" + "org.txt"
if not os.path.exists(log_file_path):
  os.makedirs(log_file_path)
log_error_fd = Logger(log_err_file, level='debug')

with tf.compat.v1.Session(config=config) as sess:
    sess.run(tf.compat.v1.global_variables_initializer())
    train_data_set = Data(train_data, train_label, slice_lag, log_error_fd)
    train_batch_data = train_data_set.next_batch_train_prefetch(batch_size, True)
    one_epo_step = int(train_num / batch_size)
    for epo in range(epo_num):
        log_error_fd.logger.debug("epochs start")
        for step in range(one_epo_step):
            train_step.run(feed_dict={x: train_batch_data[0], y: train_batch_data[1]})
            train_batch_data = train_data_set.next_batch_train_prefetch(batch_size, True)
            if step % 100 == 0:
            	local_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            	log_error_fd.logger.debug("[{}] train step {} finish.".format(local_time,step))

        log_error_fd.logger.debug("epochs end")

print("T0 time: ", time.time()-t1)




