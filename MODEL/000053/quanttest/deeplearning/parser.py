import argparse
import torch

parser = argparse.ArgumentParser()
parser.add_argument('--corpus_dir', default='/data/user/018187/TrainValidData/Data2/')

# TODO 常改动超参
parser.add_argument('--epochs', default=50, type=int) # 训练轮数
parser.add_argument('--mode', default='ensemble')  # single / ensemble /
parser.add_argument('--model', default='aemlp')  # cnn / mlp / aemlp
parser.add_argument('--input_size', default=58, type=int)  # 输入特征的维度（因子个数）
parser.add_argument('--hidden_size', default=64, type=int)  # 隐藏层的维度

parser.add_argument('--batch_size', default=32768, type=int)  # int(2e15) = 32768
parser.add_argument('--dropout', default=0.2, type=float)
# parser.add_argument('--dropout_list', type=float, nargs='+',default=[0.03, 0.4, 0.3, 0.1], help='dropout list for model training')
parser.add_argument('--action_threshold', default=0.0, type=float)
parser.add_argument('--lr', default=0.0015, type=float) #learning rate 学习率
parser.add_argument('--weight_decay', default=5e-04, type=float)

parser.add_argument('--useGPU', default=True, type=bool) #是否使用GPU
parser.add_argument('--gpu', default=0, type=int) # gpu 卡号
parser.add_argument('--save_dir', default='/data/user/000053/quanttest/saved_nn/') # 模型保存位置

###############################################################################################

args = parser.parse_args()
device = torch.device(f"cuda:{args.gpu}" if torch.cuda.is_available() and args.useGPU else "cpu")
args.device = device