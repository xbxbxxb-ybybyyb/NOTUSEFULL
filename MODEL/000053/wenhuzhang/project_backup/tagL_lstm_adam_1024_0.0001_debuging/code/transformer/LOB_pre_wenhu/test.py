

import torch
import numpy as np
import os
#import torchvision

os.environ['CUDA_VISIBLE_DEVICES']='0,1'
#os.mkdir('')
print(torch.__version__, torch.cuda.is_available())

X = np.random.random((1,20,2))
X = torch.from_numpy(X)

#print(X, X.device)

model =torch.nn.LSTM(input_size=2,hidden_size=16,num_layers=2,
                        bias=True,batch_first=True,dropout=0.5,bidirectional=False)
X = X.cuda()
model = model.cuda()
Y, hidden = model(X)
print(X.shape, Y.shape)
print(X[0,0,:], Y[0,0,:])
#print(torch.cuda.is_available(),torch.cuda.current_device(),\
#torch.cuda.device_count())

