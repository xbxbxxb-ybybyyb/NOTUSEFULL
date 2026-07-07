from CNNBase import CNNBase
import os
from PIL import Image
import numpy as np
import pandas as pd

class CNN1(CNNBase):
  def __init__(self):
    super(CNN1, self).__init__()

    self.config['w'] = 10
    self.config['h'] = 10
    self.config['c'] = 1
    self.config['lr'] = 0.001
    #迭代次数
    self.config['epoch'] = 30
    #每次迭代输入的图片数据
    self.config['bsz'] = 128
    self.config['keep'] = 20
    self.config['model_path'] = 'model/fc_model.ckpt'
    self.config['model_prefix'] = 'model/'
    self.config['previous_model'] = 'model/fc_model.ckpt-29'
    self.config['target_num'] = 18
    #self.config['predict_model'] = 'model/fc_model.ckpt-15.meta'


  def read_data(self):
      #datas = []
      #labels = []

      Y = pd.read_pickle('DATA/experimental_train.pkl')
      X = pd.read_pickle('DATA/experimental_features.pkl')
      l = X.shape[0]
      X = np.reshape(X,(l,10,10,1))
      datas = X[:40000,:,:]
      labels = Y[:40000]
      return datas, labels

  def provide_train(self):
    data_dirs = ['part_27']
    data, label = self.read_data()
    num_example=data.shape[0]
 
    ratio = 0.8
    s = np.int(num_example*ratio)
    print('num_example' + str(num_example))
    x_train=data[:s]
    y_train=label[:s]
    x_val=data[s:]
    y_val=label[s:]
    #return data, label, x_val, y_val
    return x_train, y_train, x_val, y_val
 
  def provide_test(self):
    data_dirs = ['part_27']
    data, label = self.read_data()
    return data, label
 
cnn = CNN1()
cnn.Run(cnn.config['previous_model'])
#cnn.Predict()
