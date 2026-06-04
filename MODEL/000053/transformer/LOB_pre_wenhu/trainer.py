

import os
import sys
import time
import shutil
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from torch.autograd import Variable
import math
import numpy as np
from utils import *

def train_one_epoch(train_loader, model, criterion, optimizer,\
     epoch, logger, args, log_file):
    """Train for one epoch on the training set"""
    batch_time = AverageMeter()
    losses = AverageMeter()


    # switch to train mode
    model.train()
    end = time.time()

    for i, (inputs, targets) in enumerate(train_loader):
        global_step = epoch * len(train_loader) + i
        targets = targets.cuda()
        inputs = inputs.cuda()

        # compute output
        outs = model(inputs)

       
        # loss
#        print(outs.shape, targets.shape)
        if outs.size(-1)==1:    
            outs = outs.squeeze(-1)
        loss = criterion(outs, targets) * 1.0
        
        
        losses.update(to_python_float(loss), inputs.size(0))
       
        # compute gradient and do SGD step
        optimizer.zero_grad()
        loss.backward()
        clip_gradient(optimizer, 0.5)
        optimizer.step()

        # measure elapsed time
        batch_time.update(time.time() - end)
        end = time.time()

        if i % args.log_interval == 0:
            MyPrint('Epoch: [{0}][{1}/{2}]\t'
                  'Time {batch_time.val:.3f} ({batch_time.avg:.3f})\t'
                  'Loss {loss.val:.4f} ({loss.avg:.4f})\t'.format(
                      epoch, i, len(train_loader), batch_time=batch_time,
                    loss=losses), log_file)
            
            logger.add_scalar('train/losses', losses.avg, global_step=global_step)
    return
    
def test(valid_loader, model, L2, L1, epoch, logger, args, log_file):
    """Train for one epoch on the training set"""
    batch_time = AverageMeter()
    E_l1 = AverageMeter()
    E_l2 = AverageMeter()


    # switch to train mode
    model.eval()
    end = time.time()

    for i, (inputs, targets) in enumerate(valid_loader):
        global_step = epoch * len(valid_loader) + i
        targets = targets.cuda()
        inputs = inputs.cuda()

        # compute output
        outs = model(inputs)
        
        outs = outs.squeeze(-1)
        
        error_l1= L1(outs[:,-1], targets[:,-1])
        error_l2= L2(outs[:,-1], targets[:,-1])
        
        
        E_l1.update(to_python_float(error_l1), inputs.size(0))
        E_l2.update(to_python_float(error_l2), inputs.size(0))


        # measure accuracy and record loss
#        metrics = evaluation(output.data, target)
        
        # measure elapsed time
        batch_time.update(time.time() - end)
        end = time.time()

        if i % args.log_interval == 0:
            MyPrint('Epoch: [{0}][{1}/{2}]\t'
                  'Time {batch_time.val:.3f} ({batch_time.avg:.3f})\t'
                  'L1Error {l1.val:.4f} ({l1.avg:.4f})\t'
                  'L2Error@1 {l2.val:.3f} ({l2.avg:.3f})\t'.format(
                      epoch, i, len(valid_loader), batch_time=batch_time,
                    l1=E_l1, l2=E_l2), log_file)
            
            logger.add_scalar('val/L1', E_l1.avg, global_step=global_step)
            logger.add_scalar('val/L2', E_l2.avg, global_step=global_step)
    return E_l1.avg, E_l2.avg
    


def clip_gradient(optimizer, grad_clip):
    for group in optimizer.param_groups:
        for param in group['params']:
            if param.grad is not None:
                param.grad.data.clamp_(-grad_clip, grad_clip)
                