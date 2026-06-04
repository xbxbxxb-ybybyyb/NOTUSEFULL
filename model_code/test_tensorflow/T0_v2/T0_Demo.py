import tensorflow as tf
import numpy as np
import re
import os

def conv2d(x, W, strides, padding):
    return tf.nn.conv2d(input=x, filters=W, strides=[1, strides[0], strides[1], 1], padding=padding)

def max_pool(x, shape, strides, padding):
    return tf.nn.max_pool2d(input=x, ksize=[1, shape[0], shape[1], 1],
                          strides=[1, strides[0], strides[1], 1], padding=padding)

def avg_pool(x, shape, strides, padding):
    return tf.nn.avg_pool2d(input=x, ksize=[1, shape[0], shape[1], 1],
                          strides=[1, strides[0], strides[1], 1], padding=padding)

def weight_variable(shape):
    with tf.compat.v1.variable_scope('weight'):
        initializer = tf.compat.v1.keras.initializers.VarianceScaling(scale=1.0, mode="fan_avg", distribution="uniform")
        var = tf.Variable(initializer(shape))
        return var

def bias_variable(shape):
    with tf.compat.v1.variable_scope('bias'):
        initial = tf.constant(0.1, shape=shape)
        return tf.Variable(initial)


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
        w_fc = weight_variable([4, 2, 128, 256])
        b_fc = bias_variable([256])

        fc1 = tf.nn.relu(conv2d(h_pool4, w_fc, [1, 1], 'VALID') + b_fc)
        fc1 = tf.reshape(fc1, [-1, 256])

    with tf.compat.v1.variable_scope('out'):
        w_out = weight_variable([256, 1])
        b_out = bias_variable([1])
        out = tf.matmul(fc1, w_out) + b_out
        out = tf.nn.dropout(out, 1 - (dnn_keepProb))

    return out

# Create the model
slice_lag = 300
factor_num = 150
l2_rate = 0.1
lr = 0.1
train_num = int(3e8)
valid_num = int(5e7)
epo_num = 50
batch_size = 1024
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
config = tf.compat.v1.ConfigProto(device_count={"gpu": 0})
config.gpu_options.allow_growth = True

with tf.compat.v1.variable_scope("DeepNet"):
    x = tf.compat.v1.placeholder(tf.float32, [None, slice_lag, factor_num], name='x')
    y = tf.compat.v1.placeholder(tf.float32, [None, 1], name='y')
    dnn_keepProb = tf.compat.v1.placeholder(tf.float32, name='dnn_keepProb')
    # Build the graph for the deep net
    y_regression = DeepNet(x, image_len=slice_lag, factor_num=factor_num, dnn_keepProb=dnn_keepProb)

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

with tf.compat.v1.Session(config=config) as sess:
    sess.run(tf.compat.v1.global_variables_initializer())
    train_data = np.random.random_sample((train_num, factor_num))
    train_label = np.random.random_sample((train_num, 1))
    valid_data = np.random.random_sample((valid_num, factor_num))
    valid_label = np.random.random_sample((valid_num, 1))

    for epo in range(epo_num):
        rng_state = np.random.get_state()
        np.random.shuffle(train_data)
        np.random.set_state(rng_state)
        np.random.shuffle(train_label)
        start = 0
        end = slice_lag
        while end < train_data.shape[0]:
            batch_train_data = []
            batch_train_label = []
            for count in range(batch_size):
                if end < train_data.shape[0]:
                    batch_train_data.append(train_data[start:end])
                    batch_train_label.append(train_label[end])
                    start = start + 1
                    end = end + 1
                else:
                    break
            if len(batch_train_data) == batch_size:
                sess.run(train_step, feed_dict={x: batch_train_data, y: batch_train_label,
                                          dnn_keepProb: 0.8})

        start = 0
        end = slice_lag
        predicts = []
        while end < valid_data.shape[0]:
            batch_valid_data = []
            for count in range(batch_size):
                if end < valid_data.shape[0]:
                    batch_valid_data.append(valid_data[start:end])
                    start = start + 1
                    end = end + 1
                else:
                    break
            predicts.append(sess.run(y_regression, feed_dict={x: batch_valid_data,
                                            dnn_keepProb: 1.0}))
        if len(batch_valid_data) > 0:
            predicts.append(
                sess.run(y_regression, feed_dict={x: batch_valid_data,
                                              dnn_keepProb: 1.0}))

        predicts = np.concatenate(predicts,axis=0)
        print ("mean loss ", np.mean(predicts) - np.mean(valid_label))


