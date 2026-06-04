import enum
import os
import torch.utils.data as data
import torchvision.transforms as transforms
import random
import numpy as np
import torch
import h5py

def choose_indexes(tot_len, div_indexes, window_size):
    if isinstance(div_indexes, list):
        div_indexes = np.array(div_indexes)
    assert div_indexes[-1] <= tot_len, " Divide Indexes Out of Range"
    start = window_size - 1 
    chosen_index_list = []
    for ind in div_indexes:
        end = ind
        local_indexes = list(range(start, end)) 
        chosen_index_list.extend(local_indexes) 
        start = ind + window_size- 1
    chosen_index_list.append(div_indexes[-1])
    return chosen_index_list
    
#def batchfy(factor_data, tag_data, div_indexes, window_size ):
#    chosen_index_list = choose_indexes(len(tag_data), div_indexes, window_size)
#    factor, tag=[],[]
#    for end in chosen_index_list:
#        begin = end-window_size+1
#        factor.append(factor_data[begin: end+1])
#        tag.append(tag_data[ begin: end+1])
#    factor = np.stack(factor, axis=0)
#    tag = np.stack(tag, axis=0)
#    return factor, tag

def preprocess_index(start_index, raw_length, div_indexes, window_size):
    chosen_index_list = choose_indexes(raw_length, div_indexes, window_size)
    chosen_index = np.array(chosen_index_list)
    chosen_index += start_index
    return chosen_index
    

class LOB_Dataset(data.Dataset):
    def __init__(self, data_root, window_size):
        self.window_size = window_size
        self.Factors, self.Tags, self.Indexes = self.load_data(data_root,window_size)
        print('number of points:', len(self.Factors))
        print('number of instances:', len(self.Indexes))
        self.window_size = window_size
        self.size = len(self.Indexes)
    
    def load_data(self, data_root, window_size):
        all_factor, all_tag, all_index =[],[],[]
        start_index = 0
        print('...loading dataset...')
        for file_name in os.listdir(data_root):
            with h5py.File(os.path.join(data_root, file_name) ,"r") as f:
#                timestamp=f["timestamp"].value 
                factor_data=f["factor"].value 
                tag_data =f["tag"].value
                div_indexes=f["div_indexes"].value 
                f.close()
            raw_length = len(tag_data)
            chosen_index = preprocess_index(start_index, raw_length, div_indexes, window_size)
            start_index += raw_length
#            print(factor_data.shape, tag_data.shape, chosen_index.shape, chosen_index[0])
            all_factor.append(factor_data)
            all_tag.append(tag_data)
            all_index.append(chosen_index)
        return np.concatenate(all_factor, axis=0), \
                np.concatenate(all_tag, axis=0), \
                np.concatenate(all_index, axis=0)

    def __getitem__(self, index):
        
        end = self.Indexes[index]
        begin = end-self.window_size+1
        
        factor = self.Factors[begin: end+1]
        tag = self.Tags[ begin: end+1]
        
        factor = torch.from_numpy(factor)
        tag = torch.from_numpy(tag)
        return factor, tag

    def __len__(self):
        return self.size

def get_dataloaders(data_root, args):
    train_data_root = os.path.join(data_root, 'TrainData', args.data_tag)
    valid_data_root = os.path.join(data_root, 'ValidData', args.data_tag)
    
    train_dataset = LOB_Dataset(train_data_root, args.window_size)
    train_loader = data.DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, pin_memory=True)
    
    valid_dataset = LOB_Dataset(valid_data_root, args.window_size)
    valid_loader = data.DataLoader(valid_dataset, batch_size=args.batch_size, shuffle=False, pin_memory=True)
    return train_loader, valid_loader


import argparse
parser = argparse.ArgumentParser(description='Debug')

parser.add_argument('--batch-size', type=int, default=128, metavar='N',
                    help='input batch size for training (default: 256)')
parser.add_argument('--window_size', type=int, default=100)

parser.add_argument('--data_tag', default='tagL', type=str, help='tagL or tagS')       


if __name__ == "__main__":
    
    args = parser.parse_args()

    trainL, validL = get_dataloaders('/data/user/015629/InternData/SampleData/', args)
    
    print('length:~',trainL.__len__(), validL.__len__())
    for i, (data, label) in enumerate(trainL):
        print(i)
        print('data~~:',data.shape)
        print('label~~:',label.shape)
        if i >2:
            break
        
