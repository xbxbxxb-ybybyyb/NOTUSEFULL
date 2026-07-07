from CNNBase import CNNBase
import os
from PIL import Image
import numpy as np

class CNN1(CNNBase):
  def __init__(self):
    super(CNN1, self).__init__()

    self.config['w'] = 100
    self.config['h'] = 100
    self.config['c'] = 3
    self.config['lr'] = 0.001
    #迭代次数
    self.config['epoch'] = 10
    #每次迭代输入的图片数据
    self.config['bsz'] = 64
    self.config['keep'] = 10
    self.config['model_path'] = 'model_svd3/fc_model.ckpt'
    self.config['model_prefix'] = 'model_svd3/'
    self.config['new_model_prefix'] = 'new_model_svd3/fc_model.ckpt'
    self.config['target_num'] = 2
    self.config['predict_model'] = 'model_svd3/fc_model.ckpt-0.meta'


  def read_data(self, data_dirs):
      datas = []
      labels = []
      
      for data_dir in data_dirs:
          fi = open(data_dir + '/tag.csv')
          print(data_dir + '/tag.csv')
          mp = {}
          for ln in fi:
            tk = ln.split(',')
            tk[1] = tk[1].strip()
            if (tk[1] == "REAL"):
              mp[tk[0]] = 1
            else:
              mp[tk[0]] = 0
  
          for fname in os.listdir(data_dir):
              fpath = os.path.join(data_dir, fname)
              #print(fname)
              ftype = fname.split(".")[-1]#jpg or csv
              mid = fname.split(".")[1]#jpg or csv
              prefix = fname.split(".")[0] + ".mp4"
              if (ftype == 'csv'):continue
              label = mp[prefix]#int(fname.split("_")[0])
              if (os.path.isfile(fpath) == False):continue
  
              image = Image.open(fpath)
  
              image = image.resize((100, 100),Image.ANTIALIAS)
              image = np.array(image) / 255.0
              #image = compression_procrutes(image, image1, 3)
              #image = compression(image, 0)
              data = image#np.array(image) / 255.0
              #print(data.shape)
              #datas.append(data.flatten())
              datas.append(data)
              labels.append(label)
              if (len(datas) > 300):
                break
  
      print("convert to np array")
      datas = np.array(datas)
      labels = np.array(labels)
      print("end convert to np array")
      print("shape of datas: {}\tshape of labels: {}".format(datas.shape,
  labels.shape))
      return datas, labels

  def provide_train(self):
    data_dirs = ['part_27']
    data, label = self.read_data(data_dirs)
    num_example=data.shape[0]
 
    ratio = 0.8
    s = np.int(num_example*ratio)
    print('num_example' + str(num_example))
    #x_train=data[:s]
    #y_train=label[:s]
    x_val=data[s:]
    y_val=label[s:]
    return data, label, x_val, y_val
 
  def provide_test(self):
    data_dirs = ['part_27']
    data, label = self.read_data(data_dirs)
    return data, label
 
cnn = CNN1()
#cnn.RUN()
#cnn.predict()
cnn.train_again()
