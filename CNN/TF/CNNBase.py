import numpy as np
import time
import os
import numpy as np
import tensorflow as tf
tf.compat.v1.disable_eager_execution()

class CNNBase:
  def __init__(self):
    self.config = {}

  def provide_train(self):

    raise NotImplementedError
  def provide_test(self):

    raise NotImplementedError
    
  def inference(self, input_tensor, train, regularizer):
      target_num = self.config['target_num']
      #-----------------------第一层----------------------------
      with tf.compat.v1.variable_scope('layer1-conv1'):
         #初始化权重conv1_weights为可保存变量，大小为5x5,3个通道（RGB），数量为32个
          conv1_weights = tf.compat.v1.get_variable("weight",[5,5,3,32],initializer=tf.compat.v1.truncated_normal_initializer(stddev=0.1))
          #初始化偏置conv1_biases，数量为32个    
          conv1_biases = tf.compat.v1.get_variable("bias", [32], initializer=tf.compat.v1.constant_initializer(0.0))
          #卷积计算，tf.nn.conv2d为tensorflow自带2维卷积函数，input_tensor为输入数据，
          #conv1_weights为权重，strides=[1, 1, 1, 1]表示左右上下滑动步长为1，padding='SAME'表示输入和输出大小一样，即补0
          conv1 = tf.nn.conv2d(input=input_tensor, filters=conv1_weights, strides=[1, 1, 1, 1], padding='SAME')
          #激励计算，调用tensorflow的relu函数
          relu1 = tf.nn.relu(tf.nn.bias_add(conv1, conv1_biases))
   
      with tf.compat.v1.name_scope("layer2-pool1"):
         #池化计算，调用tensorflow的max_pool函数，strides=[1,2,2,1]，表示池化边界，2个对一个生成，padding="VALID"表示不操作。
          pool1 = tf.nn.max_pool2d(input=relu1, ksize = [1,2,2,1],strides=[1,2,2,1],padding="VALID")
  #-----------------------第二层----------------------------
      with tf.compat.v1.variable_scope("layer3-conv2"):
           #同上，不过参数的有变化，根据卷积计算和通道数量的变化，设置对应的参数
          conv2_weights = tf.compat.v1.get_variable("weight",[5,5,32,64],initializer=tf.compat.v1.truncated_normal_initializer(stddev=0.1))
          conv2_biases = tf.compat.v1.get_variable("bias", [64], initializer=tf.compat.v1.constant_initializer(0.0))
          conv2 = tf.nn.conv2d(input=pool1, filters=conv2_weights, strides=[1, 1, 1, 1], padding='SAME')
          relu2 = tf.nn.relu(tf.nn.bias_add(conv2, conv2_biases))
   
      with tf.compat.v1.name_scope("layer4-pool2"):
          pool2 = tf.nn.max_pool2d(input=relu2, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='VALID')
  #-----------------------第三层----------------------------
          #同上，不过参数的有变化，根据卷积计算和通道数量的变化，设置对应的参数
      with tf.compat.v1.variable_scope("layer5-conv3"):
          conv3_weights = tf.compat.v1.get_variable("weight",[3,3,64,128],initializer=tf.compat.v1.truncated_normal_initializer(stddev=0.1))
          conv3_biases = tf.compat.v1.get_variable("bias", [128], initializer=tf.compat.v1.constant_initializer(0.0))
          conv3 = tf.nn.conv2d(input=pool2, filters=conv3_weights, strides=[1, 1, 1, 1], padding='SAME')
          relu3 = tf.nn.relu(tf.nn.bias_add(conv3, conv3_biases))
   
      with tf.compat.v1.name_scope("layer6-pool3"):
          pool3 = tf.nn.max_pool2d(input=relu3, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='VALID')
  #-----------------------第四层----------------------------
          #同上，不过参数的有变化，根据卷积计算和通道数量的变化，设置对应的参数
      with tf.compat.v1.variable_scope("layer7-conv4"):
          conv4_weights = tf.compat.v1.get_variable("weight",[3,3,128,128],initializer=tf.compat.v1.truncated_normal_initializer(stddev=0.1))
          conv4_biases = tf.compat.v1.get_variable("bias", [128], initializer=tf.compat.v1.constant_initializer(0.0))
          conv4 = tf.nn.conv2d(input=pool3, filters=conv4_weights, strides=[1, 1, 1, 1], padding='SAME')
          relu4 = tf.nn.relu(tf.nn.bias_add(conv4, conv4_biases))
   
      with tf.compat.v1.name_scope("layer8-pool4"):
          pool4 = tf.nn.max_pool2d(input=relu4, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='VALID')
          nodes = 6*6*128
          reshaped = tf.reshape(pool4,[-1,nodes])
          #使用变形函数转化结构
  #-----------------------第五层---------------------------
      with tf.compat.v1.variable_scope('layer9-fc1'):
          #初始化全连接层的参数，隐含节点为1024个
          fc1_weights = tf.compat.v1.get_variable("weight", [nodes, 1024],
                                        initializer=tf.compat.v1.truncated_normal_initializer(stddev=0.1))
          if regularizer != None: tf.compat.v1.add_to_collection('losses', regularizer(fc1_weights))#正则化矩阵
          fc1_biases = tf.compat.v1.get_variable("bias", [1024], initializer=tf.compat.v1.constant_initializer(0.1))
          #使用relu函数作为激活函数
          fc1 = tf.nn.relu(tf.matmul(reshaped, fc1_weights) + fc1_biases)
           #采用dropout层，减少过拟合和欠拟合的程度，保存模型最好的预测效率
          if train: fc1 = tf.nn.dropout(fc1, 1 - (0.5))
  #-----------------------第六层----------------------------
      with tf.compat.v1.variable_scope('layer10-fc2'):
           #同上，不过参数的有变化，根据卷积计算和通道数量的变化，设置对应的参数
          fc2_weights = tf.compat.v1.get_variable("weight", [1024, 512],
                                        initializer=tf.compat.v1.truncated_normal_initializer(stddev=0.1))
          if regularizer != None: tf.compat.v1.add_to_collection('losses', regularizer(fc2_weights))
          fc2_biases = tf.compat.v1.get_variable("bias", [512], initializer=tf.compat.v1.constant_initializer(0.1))
   
          fc2 = tf.nn.relu(tf.matmul(fc1, fc2_weights) + fc2_biases)
          if train: fc2 = tf.nn.dropout(fc2, 1 - (0.5))
  #-----------------------第七层----------------------------
      with tf.compat.v1.variable_scope('layer11-fc3'):
           #同上，不过参数的有变化，根据卷积计算和通道数量的变化，设置对应的参数
          fc3_weights = tf.compat.v1.get_variable("weight", [512, target_num], initializer=tf.compat.v1.truncated_normal_initializer(stddev=0.1))

          if regularizer != None: tf.compat.v1.add_to_collection('losses', regularizer(fc3_weights))
          fc3_biases = tf.compat.v1.get_variable("bias", [target_num], initializer=tf.compat.v1.constant_initializer(0.1))
          logit = tf.matmul(fc2, fc3_weights) + fc3_biases #matmul矩阵相乘
     #返回最后的计算结果
      return logit

  #定义一个函数，按批次取数据
  def minibatches(self, inputs=None, targets=None, batch_size=None, shuffle=False):
      assert len(inputs) == len(targets)
      if shuffle:
          indices = np.arange(len(inputs))
          np.random.shuffle(indices)
      for start_idx in range(0, len(inputs) - batch_size + 1, batch_size):
          if shuffle:
              excerpt = indices[start_idx:start_idx + batch_size]
          else:
              excerpt = slice(start_idx, start_idx + batch_size)
          yield inputs[excerpt], targets[excerpt]

  def train_again(self):
    w = self.config['w']
    h = self.config['h']
    c = self.config['c']
    lr = self.config['lr']
    n_epoch=self.config['epoch']
    batch_size = self.config['bsz']
    mkeep = self.config['keep']
    model_path = self.config['model_path']#'model_svd3/fc_model.ckpt'
    data,label,x_val,y_val = self.provide_train()


    x = tf.compat.v1.placeholder(tf.float32,shape=[None,w,h,c],name='x')
    y_ = tf.compat.v1.placeholder(tf.int32,shape=[None,],name='y_')
    #---------------------------网络结束---------------------------
    #设置正则化参数为0.0001
    regularizer = tf.keras.regularizers.l2(0.5 * (0.0001))
    #将上述构建网络结构引入
    logits = self.inference(x,False,regularizer)
     
    #(小处理)将logits乘以1赋值给logits_eval，定义name，方便在后续调用模型时通过tensor名字调用输出tensor
    b = tf.constant(value=1,dtype=tf.float32)
    logits_eval = tf.multiply(logits,b,name='logits_eval') #b为1
     
    #设置损失函数，作为模型训练优化的参考标准，loss越小，模型越优
    loss=tf.nn.sparse_softmax_cross_entropy_with_logits(logits=logits, labels=y_)
    #设置整体学习率为α为0.001
    train_op=tf.compat.v1.train.AdamOptimizer(learning_rate=lr).minimize(loss)
    #设置预测精度
    correct_prediction = tf.equal(tf.cast(tf.argmax(input=logits,axis=1),tf.int32), y_)    
    acc= tf.reduce_mean(input_tensor=tf.cast(correct_prediction, tf.float32))
    ckpt = tf.compat.v1.train.get_checkpoint_state(self.config['model_prefix'])
    saver = tf.compat.v1.train.import_meta_graph(ckpt.model_checkpoint_path +'.meta') 
    
    with tf.compat.v1.Session() as sess:
        data, label = self.provide_test()
        #saver = tf.compat.v1.train.import_meta_graph(self.config['predict_model'])
        #saver.restore(sess,tf.train.latest_checkpoint(self.config['model_path']))
        saver.restore(sess, ckpt.model_checkpoint_path)
        graph = tf.compat.v1.get_default_graph()
        logits = graph.get_tensor_by_name("logits_eval:0")

        #sess.run(tf.compat.v1.global_variables_initializer())
        
        for epoch in range(n_epoch):
            start_time = time.time()
            #training#训练集
            train_loss, train_acc, n_batch = 0, 0, 0
            for x_train_a, y_train_a in self.minibatches(data, label, batch_size, shuffle=True):
                _,err,ac=sess.run([train_op,loss,acc], feed_dict={x: x_train_a, y_: y_train_a})
                train_loss += err; train_acc += ac; n_batch += 1
                print("   train loss: %f" % (np.sum(train_loss)/ n_batch))
                print("   train acc: %f" % (np.sum(train_acc)/ n_batch))
        
            #validation#验证集
            val_loss, val_acc, n_batch = 0, 0, 0
            for x_val_a, y_val_a in self.minibatches(x_val, y_val, batch_size, shuffle=False):
                err, ac = sess.run([loss,acc], feed_dict={x: x_val_a, y_: y_val_a})
                val_loss += err; val_acc += ac; n_batch += 1
                print("   validation loss: %f" % (np.sum(val_loss)/ n_batch))
                print("   validation acc: %f" % (np.sum(val_acc)/ n_batch))
            #保存模型及模型参数   
            saver.save(sess,self.config['new_model_prefix'],global_step=epoch)

  def predict(self):
    with tf.compat.v1.Session() as sess:
        data, label = self.provide_test()
        saver = tf.compat.v1.train.import_meta_graph(self.config['predict_model'])
        saver.restore(sess,tf.train.latest_checkpoint(self.config['model_prefix']))

        graph = tf.compat.v1.get_default_graph()
        x = graph.get_tensor_by_name("x:0")
        feed_dict = {x:data}
        logits = graph.get_tensor_by_name("logits_eval:0")
        classification_result = sess.run(logits, feed_dict)
        #打印出预测矩阵
        #print(classification_result)
        #打印出预测矩阵每一行最大值的索引
        #print(tf.argmax(input=classification_result,axis=1).eval())
        output = []
        output = tf.argmax(input=classification_result,axis=1).eval()
        cnt = 0;
        for i in range(len(output)):
            if (output[i] == label[i]):
              cnt += 1
        print("cnt:" + str(cnt))
        print("ratio:"+ str(cnt / len(output)))
        return classification_result

  def RUN(self):
    #-----------------构建网络----------------------
    #本程序cnn网络模型，共有7层，前三层为卷积层，后三层为全连接层，前三层中，每层包含卷积、激活、池化层
    #占位符设置输入参数的大小和格式
    w = self.config['w']
    h = self.config['h']
    c = self.config['c']
    lr = self.config['lr']
    n_epoch=self.config['epoch']
    batch_size = self.config['bsz']
    mkeep = self.config['keep']
    model_path = self.config['model_path']#'model_svd3/fc_model.ckpt'
    data,label,x_val,y_val = self.provide_train()

    x = tf.compat.v1.placeholder(tf.float32,shape=[None,w,h,c],name='x')
    y_ = tf.compat.v1.placeholder(tf.int32,shape=[None,],name='y_')
    #---------------------------网络结束---------------------------
    #设置正则化参数为0.0001
    regularizer = tf.keras.regularizers.l2(0.5 * (0.0001))
    #将上述构建网络结构引入
    logits = self.inference(x,False,regularizer)
     
    #(小处理)将logits乘以1赋值给logits_eval，定义name，方便在后续调用模型时通过tensor名字调用输出tensor
    b = tf.constant(value=1,dtype=tf.float32)
    logits_eval = tf.multiply(logits,b,name='logits_eval') #b为1
     
    #设置损失函数，作为模型训练优化的参考标准，loss越小，模型越优
    loss=tf.nn.sparse_softmax_cross_entropy_with_logits(logits=logits, labels=y_)
    #设置整体学习率为α为0.001
    train_op=tf.compat.v1.train.AdamOptimizer(learning_rate=lr).minimize(loss)
    #设置预测精度
    correct_prediction = tf.equal(tf.cast(tf.argmax(input=logits,axis=1),tf.int32), y_)    
    acc= tf.reduce_mean(input_tensor=tf.cast(correct_prediction, tf.float32))
     
    #训练和测试数据，可将n_epoch设置更大一些
    saver = tf.compat.v1.train.Saver(max_to_keep=mkeep)#可以指定保存的模型个数，利用max_to_keep=4，则最终会保存4个模型（
    with tf.compat.v1.Session() as sess:
        #初始化全局参数
        sess.run(tf.compat.v1.global_variables_initializer())
        #开始迭代训练，调用的都是前面设置好的函数或变量
        for epoch in range(n_epoch):
            start_time = time.time()
            #training#训练集
            train_loss, train_acc, n_batch = 0, 0, 0
            #for x_train_a, y_train_a in minibatches(x_train, y_train, batch_size, shuffle=True):
            for x_train_a, y_train_a in self.minibatches(data, label, batch_size, shuffle=True):
                _,err,ac=sess.run([train_op,loss,acc], feed_dict={x: x_train_a, y_: y_train_a})
                train_loss += err; train_acc += ac; n_batch += 1
                print("   train loss: %f" % (np.sum(train_loss)/ n_batch))
                print("   train acc: %f" % (np.sum(train_acc)/ n_batch))
        
            #validation#验证集
            val_loss, val_acc, n_batch = 0, 0, 0
            for x_val_a, y_val_a in self.minibatches(x_val, y_val, batch_size, shuffle=False):
                err, ac = sess.run([loss,acc], feed_dict={x: x_val_a, y_: y_val_a})
                val_loss += err; val_acc += ac; n_batch += 1
                print("   validation loss: %f" % (np.sum(val_loss)/ n_batch))
                print("   validation acc: %f" % (np.sum(val_acc)/ n_batch))
            #保存模型及模型参数   
            saver.save(sess,model_path,global_step=epoch)
