
import argparse
import os
import sys
import time
import shutil
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torch.utils.data as data
from torch.autograd import Variable
import torch.backends.cudnn as cudnn
import math
import numpy as np
import warnings
from utils import *
from trainer import train_one_epoch, test
from model import LSTM_Model, Transformer_Model
from dataloader import get_dataloaders
#from tensorboardX import SummaryWriter

from torch.utils.tensorboard import SummaryWriter


warnings.filterwarnings('ignore')

parser = argparse.ArgumentParser(description='PyTorch Lob Predict')

parser.add_argument('--batch_size', type=int, default=1024, metavar='N',
                    help='input batch size for training (default: 256)')
parser.add_argument('--epochs', type=int, default=200, metavar='N',
                    help='number of epochs to train (default: 200)')
parser.add_argument('--lrdecay', default=30, type=int,
                    help='epochs to decay lr')
parser.add_argument('--start_epoch', type=int, default=0, metavar='N',
                    help='number of start epoch (default: 1)')
parser.add_argument('--lr', '--learning-rate', default=0.1, type=float,
                    help='initial learning rate')
parser.add_argument('--lrfact', default=1, type=float,
                    help='learning rate factor')
parser.add_argument('--lossfact', default=2.0, type=float,
                    help='loss factor')

parser.add_argument('--momentum', default=0.9, type=float, help='momentum')
parser.add_argument('--weight_decay', '--wd', default=1e-4, type=float,
                    help='weight decay (default: 1e-4)')
parser.add_argument('--seed', type=int, default=1, metavar='S',
                    help='random seed (default: 1)')
parser.add_argument('--log_interval', type=int, default=20, metavar='N',
                    help='how many batches to wait before logging training status')

parser.add_argument('--pretrained', default='', type=str,
                    help='path to pretrained checkpoint (default: none)')
parser.add_argument('--save', default='', type=str, metavar='PATH',
                    help='folder path to save checkpoint (default: none)')
                    
                    
parser.add_argument('--optimizer', default='adam', type=str)
parser.add_argument('--model_name', default='lstm', type=str)
parser.add_argument('--expname', default='give_me_a_name', type=str, metavar='n',
                    help='name of experiment (default: test')
                    
parser.add_argument('--testonly', default=False, type=bool)

parser.add_argument('--window_size', type=int, default=100)
parser.add_argument('--data_tag', default='tagL', type=str, help='tagL or tagS')       

parser.set_defaults(testonly=False)
parser.set_defaults(optimizer='adam')

parser.set_defaults(expname='debuging')
parser.set_defaults(lr=0.0001)
parser.set_defaults(model_name='lstm')

#parser.set_defaults(expname='lstm_try0706')
#parser.set_defaults(model_name='lstm')


def create_optimizer(model, args):
    
    if args.optimizer.lower() == 'adam':
        return optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay,  betas=(0.9, 0.98))
    elif args.optimizer.lower() == 'sgd':
        return optim.SGD(model.parameters(), lr=args.lr, weight_decay=args.weight_decay, momentum=args.momentum)
    else:
        raise ValueError



def main():
    global args, best_prec1
    args = parser.parse_args()
    
    args.expname = args.data_tag+'_'+args.model_name+'_'\
                    +args.optimizer+'_'+str(args.batch_size)+'_'+str(args.lr)+'_'\
                    +args.expname
    torch.manual_seed(args.seed)
    
    save_path = "/data/user/000054/wenhuzhang/project_backup/%s/"%(args.expname)
    if not args.testonly:
        cp_projects(save_path)
    log_path = os.path.join(save_path, 'log_file.txt')
#        os.makedirs(log_path)
#        sys.stdout = open(log_path, "w")
    print(torch.__version__)

    MyPrint(args, log_path)
    logger = SummaryWriter(save_path)
    
    train_loader, valid_loader = get_dataloaders('/data/user/015629/InternData/SampleData/', args)
    
    if args.model_name =='lstm':
        model = LSTM_Model(input_dim=113, hidden=64, layers=4, drop=0.2,output_size=1)
    elif args.model_name =='transformer':
        model = Transformer_Model(input_dim=113, hidden=64, n_layers=4, max_len=100,\
        output_size=1, n_heads=2, drop=0.5, layer_norm_eps=1e-12, initializer_range=0.02)
    
    nParams = sum([p.nelement() for p in model.parameters()])
    
    MyPrint('Number of model parameters is: '+ str(nParams), log_path)
    
    optimizer = create_optimizer(model, args)
    
    model = model.cuda()
    criterion = nn.MSELoss().cuda()
    L2 = nn.MSELoss().cuda()
    L1 = nn.L1Loss().cuda()
    
    best_l2 = float('inf')
    best_l1 = -1
    best_epoch = -1
    for epoch in range(args.start_epoch, args.epochs):

#        adjust_learning_rate(optimizer, epoch)
        MyPrint("lr: "+ str(optimizer.param_groups[0]['lr']), log_path)

        # train for one epoch
        train_one_epoch(train_loader, model, criterion, optimizer, epoch,logger, args, log_path)

        # evaluate on validation set
        l1, l2 = test(valid_loader, model,L2,L1, epoch, logger, args, log_path)

        # remember best prec@1 and save checkpoint
        is_best = l2 < best_l2
        if is_best:
            best_epoch = epoch
            best_l1 = l1
        best_l2 = min(l2, best_l2)
        save_checkpoint({
            'epoch': epoch + 1,
            'state_dict': model.state_dict(),
            'l1': l1,
            'l2': l2,
            'optimizer' : optimizer.state_dict(),
        }, is_best, save_path+"/model")

        MyPrint('Best MSE: '+ str(best_l2), log_file)
        logger.add_scalar('best/L2', best_l2, global_step=epoch)

    MyPrint("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!traingning finish!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
   
    MyPrint('Best MSE: '+str(best_l2), log_file)
    MyPrint('Best L1: '+str(best_l1), log_file)
    MyPrint('Best Epoch'+str(best_epoch), log_file)
    MyPrint('Number of model parameters is'+str(nParams), log_file)
   
    

if __name__ == '__main__':
    main()

