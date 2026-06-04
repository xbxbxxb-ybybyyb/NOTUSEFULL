"""
Tensorflow implementation of DeepFM [1]
Modified by Sun Haiping for return prediction

Reference:
[1] DeepFM: A Factorization-Machine based Neural Network for CTR Prediction,
    Huifeng Guo, Ruiming Tang, Yunming Yey, Zhenguo Li, Xiuqiang He.
"""
import os
import numpy as np
import tensorflow as tf
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import roc_auc_score
from sklearn.metrics import mean_squared_error
from time import time
from tensorflow.contrib.layers.python.layers import batch_norm as batch_norm


class DeepFM(BaseEstimator, TransformerMixin):
    def __init__(self, feature_size, field_size,
                 embedding_size=8, dropout_fm=[1, 1],
                 deep_layers=[32, 32], dropout_deep=[0.5, 0.5, 0.5],
                 deep_layers_activation=tf.nn.relu,
                 epoch=10, batch_size=256,
                 learning_rate=0.001, optimizer_type="adam",
                 batch_norm=0, batch_norm_decay=0.995,
                 verbose=False, random_seed=2016,
                 use_fm=True, use_deep=True,
                 loss_type="logloss", eval_metric=roc_auc_score,
                 l2_reg=0.0, l1_reg=0.0, greater_is_better=True,label_do='day1'):
        # assert (use_fm or use_deep)
        # assert loss_type in ["logloss", "mse","mae"], \
            # "loss_type can be either 'logloss' for classification task or 'mse' for regression task"

        self.feature_size = feature_size        # denote as M, size of the feature dictionary
        self.field_size = field_size            # denote as F, size of the feature fields
        self.embedding_size = embedding_size    # denote as K, size of the feature embedding

        self.dropout_fm = dropout_fm
        self.deep_layers = deep_layers
        self.dropout_deep = dropout_deep
        self.deep_layers_activation = deep_layers_activation
        self.use_fm = use_fm
        self.use_deep = use_deep
        self.l2_reg = l2_reg
        self.l1_reg = l1_reg

        self.epoch = epoch
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.optimizer_type = optimizer_type

        self.batch_norm = batch_norm
        self.batch_norm_decay = batch_norm_decay

        self.verbose = verbose
        self.random_seed = random_seed
        self.loss_type = loss_type
        self.label_do = label_do
        print(loss_type)
        if loss_type == 'logloss':
            eval_metric = roc_auc_score # 分类模型
            greater_is_better = True
        else:
            eval_metric = mean_squared_error # 回归模型
            greater_is_better = False
        self.eval_metric = eval_metric
        self.greater_is_better = greater_is_better
        self.train_result, self.valid_result, self.loss_result = [], [], []

        self._init_graph()


    def _init_graph(self):
        tf.set_random_seed(self.random_seed)
        self.graph = tf.Graph()
        with self.graph.as_default():
            np.random.seed(self.random_seed)            
            self.feat_value = tf.placeholder(tf.float32, shape=[None, None],
                                                 name="feat_value")  # None * F
            self.label = tf.placeholder(tf.float32, shape=[None, 1], name="label")  # None * 1
            self.dropout_keep_fm = tf.placeholder(tf.float32, shape=[None], name="dropout_keep_fm")
            self.dropout_keep_deep = tf.placeholder(tf.float32, shape=[None], name="dropout_keep_deep")

            self.train_phase = tf.placeholder(tf.bool, name="train_phase")

            self.weights = self._initialize_weights()

           # ---------- first order term ----------
            self.y_first_order = self.feat_value
            if self.use_fm:
               # ---------- second order term ---------------
                feat_value = tf.reshape(self.feat_value, shape=[-1, self.feature_size, 1]) # None * F * 1
                self.embeddings = tf.multiply(self.weights["feature_embeddings"], feat_value,name='embeddings')  # None * F * K # embedding作用降维
                # sum_square part
                self.summed_features_emb = tf.reduce_sum(self.embeddings, 1,name='summed_features_emb')  # None * K
                self.summed_features_emb_square = tf.square(self.summed_features_emb,name='summed_features_emb_square')  # None * K

                # square_sum part
                self.squared_features_emb = tf.square(self.embeddings,name='squared_features_emb')
                self.squared_sum_features_emb = tf.reduce_sum(self.squared_features_emb, 1,name='squared_sum_features_emb')  # None * K

                # second order
                self.y_second_order = 0.5 * tf.subtract(self.summed_features_emb_square, self.squared_sum_features_emb)  # None * K
                self.y_second_order = tf.nn.dropout(self.y_second_order, self.dropout_keep_fm[1], seed=self.random_seed,name='y_second_order')  # None * K
            if self.use_deep:
                # ---------- Deep component ----------
                self.y_deep = tf.reshape(self.embeddings, shape=[-1, self.feature_size * self.embedding_size],name='y_deep') # None * (F*K)
                self.y_deep = tf.nn.dropout(self.y_deep, self.dropout_keep_deep[0], seed=self.random_seed)
                for i in range(0, len(self.deep_layers)):
                    self.y_deep = tf.add(tf.matmul(self.y_deep, self.weights["layer_%d" %i]), self.weights["bias_%d"%i]) # None * layer[i] * 1
                    if self.batch_norm:
                        self.y_deep = self.batch_norm_layer(self.y_deep, train_phase=self.train_phase, scope_bn="bn_%d" %i) # None * layer[i] * 1
                    self.y_deep = self.deep_layers_activation(self.y_deep)
                    self.y_deep = tf.nn.dropout(self.y_deep, self.dropout_keep_deep[1+i], seed=self.random_seed) # dropout at each Deep layer


            # ---------- DeepFM ----------
            if self.use_fm and self.use_deep:
                concat_input = tf.concat([self.y_first_order, self.y_second_order, self.y_deep], axis=1)
            elif self.use_fm:
                concat_input = tf.concat([self.y_first_order, self.y_second_order], axis=1)
            elif self.use_deep:
                concat_input = self.y_deep
            else: # 使用LR
                concat_input = self.y_first_order  
            
            # add Barra softmax
            

            
            # loss
            if self.loss_type == "logloss": # 交叉熵损失函数
                self.out = tf.add(tf.matmul(concat_input, self.weights["concat_projection"]), self.weights["concat_bias"])
                self.out = tf.nn.sigmoid(self.out, name='predict')
                self.loss = tf.losses.log_loss(self.label, self.out,name='loss')
            elif self.loss_type == "mse": 
                self.out = tf.add(tf.matmul(concat_input, self.weights["concat_projection"]), self.weights["concat_bias"], name='predict')
                self.loss = tf.nn.l2_loss(tf.subtract(self.label, self.out),name='loss')
            elif self.loss_type == "mae": 
                self.out = tf.add(tf.matmul(concat_input, self.weights["concat_projection"]), self.weights["concat_bias"], name='predict')
                maes = tf.losses.absolute_difference(self.label, self.out)
                self.loss = tf.reduce_sum(maes,name='loss')
            elif self.loss_type == "huber": 
                self.out = tf.add(tf.matmul(concat_input, self.weights["concat_projection"]), self.weights["concat_bias"], name='predict')
                hubers = tf.losses.huber_loss(self.label, self.out)
                self.loss = tf.reduce_sum(hubers,name='loss')

            self.loss += tf.contrib.layers.l2_regularizer(
                self.l2_reg)(self.weights["concat_projection"])
                # +tf.contrib.layers.l1_regularizer(\
                #     self.l1_reg)(self.weights["concat_projection"])                
                      

            # optimizer
            if self.optimizer_type == "adam": #(Adaptive Moment Estimation)是一种不同参数自适应不同学习速率方法,参数比较平稳
                self.optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate, beta1=0.9, beta2=0.999,
                                                        epsilon=1e-8).minimize(self.loss) 
            # beta_1: 接近 1 的常数，（有偏）一阶矩估计的指数衰减因子；
            # beta_2: 接近 1 的常数，（有偏）二阶矩估计的指数衰减因子；
            elif self.optimizer_type == "adagrad":
                self.optimizer = tf.train.AdagradOptimizer(learning_rate=self.learning_rate,
                                                           initial_accumulator_value=1e-8).minimize(self.loss)
            elif self.optimizer_type == "gd":
                self.optimizer = tf.train.GradientDescentOptimizer(learning_rate=self.learning_rate).minimize(self.loss)
            elif self.optimizer_type == "momentum":
                self.optimizer = tf.train.MomentumOptimizer(learning_rate=self.learning_rate, momentum=0.95).minimize(
                    self.loss)
            elif self.optimizer_type == "yellowfin":
                self.optimizer = YFOptimizer(learning_rate=self.learning_rate, momentum=0.0).minimize(
                    self.loss)

            # init
            self.saver = tf.train.Saver()
            init = tf.global_variables_initializer()
            self.sess = self._init_session()
            self.sess.run(init)

            # number of params
            total_parameters = 0
            for variable in self.weights.values():
                shape = variable.get_shape()
                variable_parameters = 1
                for dim in shape:
                    variable_parameters *= dim.value
                total_parameters += variable_parameters
            if self.verbose > 0:
                print("#params: %d" % total_parameters)


    def _init_session(self):
        config = tf.ConfigProto(device_count={"gpu": 0})
        config.gpu_options.allow_growth = True
        return tf.Session(config=config)


    def _initialize_weights(self):
        tf.set_random_seed(self.random_seed)
        np.random.seed(self.random_seed)
        weights = dict()
        # embeddings
        if self.use_fm:
            weights["feature_embeddings"] = tf.Variable(
                tf.truncated_normal([self.feature_size, self.embedding_size], 0.0, 0.02, seed=self.random_seed),
                name="feature_embeddings")  # feature_size * K
            weights["feature_bias"] = tf.Variable(
                tf.random_uniform([self.feature_size, 1], 0.0, 1.0, seed=self.random_seed), name="feature_bias")  # feature_size * 1
        # deep layers
        num_layer = len(self.deep_layers)
        input_size = self.feature_size * self.embedding_size
        glorot = np.sqrt(2.0 / (input_size + self.deep_layers[0]))
        weights["layer_0"] = tf.Variable(
            tf.truncated_normal([input_size, self.deep_layers[0]], mean=0, stddev=glorot, seed=self.random_seed), dtype=np.float32)
        weights["bias_0"] = tf.Variable(np.random.normal(loc=0, scale=glorot, size=(1, self.deep_layers[0])),
                                                        dtype=np.float32)  # 1 * layers[0]
        for i in range(1, num_layer):
            glorot = np.sqrt(2.0 / (self.deep_layers[i-1] + self.deep_layers[i]))
            weights["layer_%d" % i] = tf.Variable(
                tf.truncated_normal([self.deep_layers[i-1], self.deep_layers[i]], mean=0, stddev=glorot, seed=self.random_seed),
                dtype=np.float32)  # layers[i-1] * layers[i]
            weights["bias_%d" % i] = tf.Variable(
                tf.truncated_normal([1, self.deep_layers[i]], mean=0, stddev=glorot, seed=self.random_seed),
                dtype=np.float32)  # 1 * layer[i]


        # final concat projection layer
        if self.use_fm and self.use_deep:
            input_size = self.feature_size + self.embedding_size + self.deep_layers[-1]
        elif self.use_fm:
            input_size = self.feature_size + self.embedding_size
        elif self.use_deep:
            input_size = self.deep_layers[-1]
        else:
            input_size = self.feature_size
        glorot = np.sqrt(2.0 / (input_size + 1))
        weights["concat_projection"] = tf.Variable(
                        tf.random_normal([input_size, 1], mean=0, stddev=glorot,seed=self.random_seed),
                        dtype=np.float32)  # layers[i-1]*layers[i]
        weights["concat_bias"] = tf.Variable(tf.constant(0.01), dtype=np.float32)

        return weights


    def batch_norm_layer(self, x, train_phase, scope_bn):
        bn_train = batch_norm(x, decay=self.batch_norm_decay, center=True, scale=True, updates_collections=None,
                              is_training=True, reuse=None, trainable=True, scope=scope_bn)
        bn_inference = batch_norm(x, decay=self.batch_norm_decay, center=True, scale=True, updates_collections=None,
                                  is_training=False, reuse=True, trainable=True, scope=scope_bn)
        z = tf.cond(train_phase, lambda: bn_train, lambda: bn_inference)
        return z


    def get_batch(self, Xv, y, batch_size, index):
        start = index * batch_size
        end = (index+1) * batch_size
        end = end if end < len(y) else len(y)
        return Xv[start:end], [[y_] for y_ in y[start:end]]


    # shuffle three lists simutaneously
    def shuffle_in_unison_scary(self, b, c):
        np.random.seed(self.random_seed) 
        rng_state = np.random.get_state()
        np.random.set_state(rng_state)
        np.random.shuffle(b)
        np.random.set_state(rng_state)
        np.random.shuffle(c)


    def fit_on_batch(self, Xv, y):
        feed_dict = {self.feat_value: Xv,
                     self.label: y,
                     self.dropout_keep_fm: self.dropout_fm,
                     self.dropout_keep_deep: self.dropout_deep,
                     self.train_phase: True}
        loss, opt = self.sess.run((self.loss, self.optimizer), feed_dict=feed_dict)
        return loss


    def fit(self, Xv_train, y_train,
            Xv_valid=None, y_valid=None,
            fold_num=None,clf_str=None,early_stopping=False, refit=False):
        """
        :param Xv_train: [[val1_1, val1_2, ...], [val2_1, val2_2, ...], ..., [vali_1, vali_2, ..., vali_j, ...], ...]
                         vali_j is the feature value of feature field j of sample i in the training set
                         vali_j can be either binary (1/0, for binary/categorical features) or float (e.g., 10.24, for numerical features)
        :param y_train: label of each sample in the training set
        :param Xv_valid: list of list of feature values of each sample in the validation set
        :param y_valid: label of each sample in the validation set
        :param early_stopping: perform early stopping or not
        :param refit: refit the model on the train+valid dataset or not
        :return: None
        """
        has_valid = Xv_valid is not None
        for epoch in range(self.epoch):
            # half_time = 5
            # if epoch%half_time == 0 and epoch>half_time:
            #     learn_rate_decay = 0.5
            #     self.learning_rate = self.learning_rate*learn_rate_decay                
            t1 = time()
            self.shuffle_in_unison_scary(Xv_train, y_train) #@后续放开，有随机性在里面，不受seed控制
            total_batch = int(len(y_train) / self.batch_size)
            for i in range(total_batch):
                Xv_batch, y_batch = self.get_batch(Xv_train, y_train, self.batch_size, i)
                loss = self.fit_on_batch(Xv_batch, y_batch)
#                 print('epoch:',epoch,',batch:',i,',loss:',loss)
            self.loss_result.append(loss)
            # evaluate training and validation datasets
            train_result, predicted = self.evaluate(Xv_train, y_train)
            self.train_result.append(train_result)
            if has_valid:
                valid_result, predicted = self.evaluate(Xv_valid, y_valid)
                self.valid_result.append(valid_result)
            if self.verbose > 0 and epoch % self.verbose == 0:
                if has_valid:
                    print('epoch:',epoch,',batch:',i,',loss:',loss)
                    print("[%d %d] train-result=%.4f, valid-result=%.4f [%.1f s]"
                        % (epoch + 1, len(self.valid_result), train_result, valid_result, time() - t1))
                else:
                    print("[%d] train-result=%.4f [%.1f s]"
                        % (epoch + 1, train_result, time() - t1))
            if has_valid and early_stopping and self.training_termination(self.valid_result):
                break

        # fit a few more epoch on train+valid until result reaches the best_train_score
        if has_valid and refit:
            if self.greater_is_better:
                best_valid_score = max(self.valid_result)
            else:
                best_valid_score = min(self.valid_result)
            best_epoch = self.valid_result.index(best_valid_score)
            best_train_score = self.train_result[best_epoch]
            Xv_train = Xv_train + Xv_valid
            y_train = y_train + y_valid
            for epoch in range(1):
                self.shuffle_in_unison_scary(Xv_train, y_train)
                total_batch = int(len(y_train) / self.batch_size)
                for i in range(total_batch):
                    Xv_batch, y_batch = self.get_batch(Xv_train, y_train,
                                                                self.batch_size, i)
                    self.fit_on_batch(Xv_batch, y_batch)
                # check
                train_result, predicted = self.evaluate(Xv_train, y_train)
                if abs(train_result - best_train_score) < 0.001 or \
                    (self.greater_is_better and train_result > best_train_score) or \
                    ((not self.greater_is_better) and train_result < best_train_score):
                    break
      


    def training_termination(self, valid_result):
        if len(valid_result) > 5:
            if self.greater_is_better:
                if valid_result[-1] < (valid_result[-2])*1.005 and \
                    valid_result[-2] < (valid_result[-3])*1.01 and \
                    valid_result[-3] < (valid_result[-4])*1.01 and \
                    valid_result[-4] < (valid_result[-5])*1.02:
                    return True
            else:
                if valid_result[-1] > (valid_result[-2])*1.01 and \
                    valid_result[-2] > (valid_result[-3])*1.02 and \
                    valid_result[-3] > (valid_result[-4])*1.02 and \
                    valid_result[-4] > (valid_result[-5])*1.03:
                    return True
        return False


    def predict(self, Xv):
        """
        :param Xv: list of list of feature values of each sample in the dataset
        :return: predicted probability of each sample
        """        
        # dummy y
        dummy_y = [1] * len(Xv)
        batch_index = 0
        Xv_batch, y_batch = self.get_batch(Xv, dummy_y, self.batch_size, batch_index)
        y_pred = None
        while len(Xv_batch) > 0:
            num_batch = len(y_batch)
            feed_dict = {self.feat_value: Xv_batch,
                         self.label: y_batch,
                         self.dropout_keep_fm: [1.0] * len(self.dropout_fm),
                         self.dropout_keep_deep: [1.0] * len(self.dropout_deep),
                         self.train_phase: False}
            batch_out = self.sess.run(self.out, feed_dict=feed_dict)
            if batch_index == 0:
                y_pred = np.reshape(batch_out, (num_batch,))
            else:
                y_pred = np.concatenate((y_pred, np.reshape(batch_out, (num_batch,))))

            batch_index += 1
            Xv_batch, y_batch = self.get_batch(Xv, dummy_y, self.batch_size, batch_index)

        return y_pred


    def evaluate(self, Xv, y):
        """
        :param Xv: list of list of feature values of each sample in the dataset
        :param y: label of each sample in the dataset
        :return: metric of the evaluation
        """
        y_pred = self.predict(Xv)
        return self.eval_metric(y, y_pred),y_pred


