import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
#from torchvision import transforms

import os
from parser import args


def getData(corpus_dir, tag_index, batch_size, train_shuffle=True):
    # 构造 dataset 和 dataloader
    # [:, tag_index:tag_index+1] 是为了保持label的维度（依然为2, 这样myDataset里才能用from_numpy）
    trainX, trainY = np.load(os.path.join(corpus_dir, "TrainData.npy"), allow_pickle=True), np.load(os.path.join(corpus_dir, "TrainLabel.npy"), allow_pickle=True)[:, tag_index:tag_index+1]
    testX, testY = np.load(os.path.join(corpus_dir, "ValidData.npy"), allow_pickle=True), np.load(os.path.join(corpus_dir, "ValidLabel.npy"), allow_pickle=True)[:, tag_index:tag_index+1]
    
    num_workers = 8
    train_loader = DataLoader(dataset=myDataset(trainX, trainY), batch_size=batch_size, shuffle=train_shuffle, pin_memory=True, num_workers=num_workers)
    test_loader = DataLoader(dataset=myDataset(testX, testY), batch_size=batch_size, shuffle=False, pin_memory=True, num_workers=num_workers)
    
    return train_loader, test_loader
    

class myDataset(Dataset):
    
    def __init__(self, xx, yy):
        self.x = torch.from_numpy(xx)
        self.y = torch.from_numpy(yy)
        # multi-class label
        # bins = np.array([0.0, 1.2, 2.27, 2.95])  # threshold for tag0 (top-2 top-1)
        # bins = np.array([-3.0, -2.0, -1.54, -1.2, -0.8, -0.5, 0, 0.2, 1.0])
        bins = np.array([0.0])
        self.y_class = torch.from_numpy(np.digitize(yy, bins))  # get index for our multi-class task
        
    def __getitem__(self, index):
        x1 = self.x[index]
        y1 = self.y[index]
        y2 = self.y_class[index]

        return x1, y1, y2

    def __len__(self):
        return len(self.x)
        
       