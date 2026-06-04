import torch.nn as nn
import torch.nn.init as init
import torch

def init_params(net):
    '''Init layer parameters.'''
    for m in net.modules():
        if isinstance(m, nn.Conv2d):
            init.kaiming_normal(m.weight, mode='fan_out')
            if m.bias:
                init.constant(m.bias, 0)
        elif isinstance(m, nn.BatchNorm2d):
            init.constant(m.weight, 1)
            init.constant(m.bias, 0)
        elif isinstance(m, nn.Linear):
            init.normal(m.weight, std=1e-3)
            if m.bias:
                init.constant(m.bias, 0)

                
import argparse
parser = argparse.ArgumentParser(description='Debug')

parser.add_argument('--batch-size', type=int, default=128, metavar='N',
                    help='input batch size for training (default: 256)')
parser.add_argument('--window_size', type=int, default=100)

parser.add_argument('--data_tag', default='tagL', type=str, help='tagL or tagS')       


if __name__ == "__main__":
    
    args = parser.parse_args()