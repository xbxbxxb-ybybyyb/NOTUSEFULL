import os
import torch
import torch.nn as nn
from tqdm import tqdm

from model import regressor, cnnRegressor, aemlp
from parser import args  # hyper-parameters
from dataset import getData
from loss import FocalLoss, WeightedFocalLoss
from utils import myPrint
from test import valid

import warnings
warnings.filterwarnings("ignore")


def train(tag_index = 0):

    if args.model == 'mlp':
        model = regressor(input_size=args.input_size, hidden_size=args.hidden_size, output_size=1, dropout=args.dropout).to(args.device)
    elif args.model == 'cnn':
        model = cnnRegressor(input_size=args.input_size, hidden_size=args.hidden_size, output_size=1, dropout=args.dropout).to(args.device)
    elif args.model == 'aemlp':
        model = aemlp(input_size=args.input_size, hidden_size=args.hidden_size, output_size=1, dropout=args.dropout).to(args.device)
    myPrint(model, "logTrain_tag_{}".format(tag_index))
    
    criterion = nn.MSELoss()  # 定义损失函数
#    criterion_bce = nn.BCELoss()  # BCELoss
#    weight = torch.tensor([0.3, 0.7]).to(args.device)
    criterion_bce = WeightedFocalLoss(alpha=0.25, gamma=2)
    criterion_ce = nn.CrossEntropyLoss()  # multi-class CELoss
    
    # AutoEncoder part
    criterion_ae = nn.MSELoss()
    
    
#    """  # 加权损失法
#    criterion = nn.MSELoss(reduction='none')  # 加权tag>0（提recall） or pred>0（提precision） 对应的loss, 配合下方每个batch - loss*weight
#    """
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)  # Adam, learning-rate = 0.001
    train_loader, test_loader = getData(corpus_dir = args.corpus_dir, tag_index=tag_index, batch_size = args.batch_size)
    
    myPrint("Start Training for Tag_{}======================================== ".format(tag_index), "{0}/logTrain_tag_{1}".format(args.model, tag_index))
    myPrint("This is AE-MLP-Focalloss-2class4loss ======================================== ", "{0}/logTrain_tag_{1}".format(args.model, tag_index))
    
    # train per epoch (batch-training)
    for i in range(args.epochs):
        model.train()
        total_loss, total_loss_mse, total_loss_bce, total_loss_ae, total_loss_ae_mse  = 0, 0, 0, 0, 0 
        
        for data, label, label_class in tqdm(train_loader):
            data = data.to(args.device)            
            label = label.to(args.device)  # ground-truth
            
            if args.model == 'aemlp':
                outRegressor, outAction, outAe, x_decoder = model(data)
                # binary class
                labelAction = (label>args.action_threshold).float().to(args.device)  # threshold = 1.0, 1.2, 0.0
            elif args.model == 'cnn':
                outRegressor, outAction = model(data)
                # binary class
                labelAction = (label>args.action_threshold).float().to(args.device)  # threshold = 1.0, 1.2, 0.0
            elif args.model == 'mlp':
                outRegressor = model(data)
            
            # Loss weight
            # a, b, c, d = 0.4, 1.0, 0.0, 0.0  # multi-class
            # mse, bce, ae_reconstruct, ae_task
            a, b, c, d = 0.4, 1.0 * 10, 0.5 * 2, 0.5 * 10  # binary-class
            
            if args.model == 'aemlp':                
                loss_mse = a * criterion(outRegressor, label)
                loss_bce = b * criterion_bce(outAction, labelAction)  # binary-class or Focal loss                
                # loss_bce = b * criterion_ce(outAction, labelAction)  # multi-class
                loss_ae = c * criterion_ae(x_decoder, data)  # AE re-construct
                loss_ae_mse = d * criterion_bce(outAe, labelAction)  # AE output binary-class
                loss = loss_mse + loss_bce + loss_ae + loss_ae_mse
            elif args.model == 'cnn':
                loss_mse = a * criterion(outRegressor, label)
                # loss_bce = b * criterion_bce(outAction, labelAction)  # binary-class
                loss_bce = b * criterion_ce(outAction, labelAction)  # multi-class
                loss = loss_mse + loss_bce
            elif args.model == 'mlp':
                loss = criterion(outRegressor, label)
            
            
            # weight loss for better top-k acc
            """  # if MSELoss - reduction = 'None', 选择关注下 `tag>0 or pred>0` 的loss
            weight = (label > 0) + 1  # (batch_sz, 1); element 是 2 or 1 # or pred>0 (label这样不work)
            weight = (pred > 0) + 1
            weight = (((pred > 0) + (label > 1.2)) > 0) + 1
            loss = torch.mean(loss * weight, dim=0)
            """
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            if args.model == 'aemlp':
                total_loss_mse += loss_mse.item()
                total_loss_bce += loss_bce.item()
                total_loss_ae += loss_ae.item()  # AE re-construct
                total_loss_ae_mse += loss_ae_mse.item()  # AE regressor
            elif args.model == 'cnn':
                total_loss_mse += loss_mse.item()
                total_loss_bce += loss_bce.item()
            elif args.model == 'mlp':
                # TODO: baseline MLP need no operation here
                pass
               
        # save model each 5 epoches
        if i % 5 == 0:
            save_file_tmp = os.path.join(args.save_dir, "tag_{0}/{2}_2class-fl-4loss_tag_{0}_epoch{1}".format(tag_index, i, args.model))
            torch.save(model.state_dict(), save_file_tmp, _use_new_zipfile_serialization=False)  # _use_new_zipfile_serialization=False
            myPrint('第%d个 epoch，已保存模型############################################################' % i, "{0}/logTrain_tag_{1}".format(args.model, tag_index))
        
        # eval per epoch
        myPrint("Epoch_{0} Total Loss:  {1}  \n".format(i, total_loss) + 
                "Main Regressor MSE Total Loss:  {}      ".format(total_loss_mse) +
                "Main Action BCE Total Loss:  {}  \n".format(total_loss_bce) +
                "AutoEncoder Task Total Loss:  {}      ".format(total_loss_ae_mse) + 
                "AutoEncoder Re-construction Total Loss:  {}  \n".format(total_loss_ae),
                "{0}/logTrain_tag_{1}".format(args.model, tag_index))
        # EVAL on val-set
        valid(model, tag_index=tag_index, test_loader=test_loader, mod=args.model)  # eval model with some metrics
        


if __name__ == '__main__':
    
    torch.manual_seed(42)
        
    for tag_index in range(6):  # range(1, 6)
        train(tag_index)
    
    