import torch
import torch.nn as nn


class regressor(nn.Module):
        
    def __init__(self, input_size, hidden_size=64, output_size=1, dropout=0.2):
        super().__init__()
        # input: batch_size, factor_size
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.dropout = dropout
        self.mlp = nn.Sequential(
                    nn.Linear(self.input_size, 128),
                    nn.ReLU(),
                    nn.Dropout(self.dropout),
                    nn.Linear(128, self.hidden_size),
                    nn.ReLU(), 
                    nn.Linear(self.hidden_size, 16),
                )
        self.linear = nn.Linear(16, self.output_size)
                
    def forward(self, x):
        # input x: batch_size, factor_size
        rep = self.mlp(x)
        out = self.linear(rep)
        return out
        

class cnnRegressor(nn.Module):
        
    def __init__(self, input_size, hidden_size=64, output_size=1, dropout=0.2):
        super().__init__()
        # input: batch_size, factor_size
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.dropout = dropout
        
        self.bn = nn.BatchNorm1d(self.input_size)
        self.conv = nn.Conv1d(1, 1, 3, stride=3, padding=0, dilation = 3)  # out: 58 -> 18
        
        self.mlp = nn.Sequential(
                    nn.Linear(self.input_size, 128),
                    nn.ReLU(),
                    nn.Dropout(self.dropout),
                    nn.Linear(128, self.hidden_size),
                    nn.ReLU(), 
                    nn.Linear(self.hidden_size, 32),
                )
        # Two Task heads
        self.outRegressor = nn.Linear(32+18, self.output_size)  # regressor
        # binary-class
        self.outAction = nn.Sequential(
                            nn.Linear(32+18, self.output_size),
                            nn.Sigmoid(),
                )
        # multi-class, here num_class=2 （just use softmax）
#        self.outAction = nn.Sequential(
#                            nn.Linear(32+18, 2),
#                            nn.Softmax(),
#                )
                
    def forward(self, x):
        # input x: batch_size, factor_size
        x = self.bn(x)
        
        conv_rep = (self.conv(x.unsqueeze(1))).squeeze(1)  # unsqueeze(1) cater to Conv - (C_in,) 
        rep = self.mlp(x)
        rep = torch.cat((conv_rep, rep), dim=1)
        # output
        out = self.outRegressor(rep)
        action = self.outAction(rep)
        return out, action
    
               
class aemlp(nn.Module):
        
    def __init__(self, input_size, hidden_size=64, output_size=1, dropout=0.2):
        """
        TODO: 
            传 hidden_size_list
            传 dropout_list
        """
        super().__init__()
        # input: batch_size, factor_size
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.dropout = dropout
        
        self.bn = nn.BatchNorm1d(self.input_size)
        # 1-d conv part
        # self.conv = nn.Conv1d(1, 1, 3, stride=3, padding=0, dilation = 3)  # out: 58 -> 18
        
        # 1. AutoEncoder
        # GaussianNoise Layer -> forward torch.randn done!
        self.encoder = nn.Sequential(
                    nn.Linear(self.input_size, 128),
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                )
                
        self.decoder = nn.Sequential(
                    nn.Dropout(self.dropout),
                    nn.Linear(128, self.input_size),
                )
        
        self.ae = nn.Sequential(
                    nn.Linear(self.input_size, 128),
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    nn.Dropout(self.dropout),
                )
                  
        self.aeAction = nn.Sequential(
                    nn.Linear(128, 32),
                    nn.ReLU(),
                    nn.Linear(32, self.output_size),
                    nn.Sigmoid(),
                )    
        
        # 2. Main regressor head
        # after concat, put into regressor head
        self.mlp = nn.Sequential(
                    nn.BatchNorm1d(self.input_size + 128),
                    nn.Dropout(self.dropout),
                    nn.Linear(self.input_size + 128, 128),
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    nn.Dropout(self.dropout),
                    nn.Linear(128, self.hidden_size),
                    nn.BatchNorm1d(self.hidden_size),
                    nn.ReLU(), 
                    nn.Dropout(self.dropout),
                    nn.Linear(self.hidden_size, 32),
                )
        
        # Output Layer: Two tasks 
        # Regressor
        self.outRegressor = nn.Linear(32, self.output_size)  # regressor
        
        # Auxiliary Task: binary classification or multi-class classification?  e.g. nn.Softmax(dim=-1)
        self.outAction = nn.Sequential(
                            nn.Linear(32, self.output_size),
                            nn.Sigmoid(),
                )
        # multi-class, here num_class=5
#        self.outAction = nn.Sequential(
#                            nn.Linear(32+18, 6),
#                            nn.Softmax(),
#                )
        
    def forward(self, x):
        x = self.bn(x)
        if self.training == True:
            # gaussianNoise = torch.normal(mean=0.0,std=torch.tensor([[0.03]*58]*32768).float())
            gaussianNoise = torch.randn(x.shape[0], 58) / 20  # stddev = 1/20, where 20 is hyper-param
            x0 = x + gaussianNoise.cuda()
        else:
            x0 = x
        
        # conv part
        # x_conv = (self.conv(x0.unsqueeze(1))).squeeze(1)
        
        # AutoEncoder part
        x_encoder = self.encoder(x0)
        x_decoder = self.decoder(x_encoder)
        x_ae = self.ae(x_decoder)
        outAe = self.aeAction(x_ae)
        
        # Main Regressor
        x_inp = torch.cat((x0, x_encoder), dim=1)
        x_inp = self.mlp(x_inp)        
        outAction = self.outAction(x_inp)
        outRegressor = self.outRegressor(x_inp)
        
        return outRegressor, outAction, outAe, x_decoder


class aemlp4Factors(aemlp):
    
    def __init__(self, input_size, hidden_size=64, output_size=1, dropout=0.2):
        super().__init__(input_size, hidden_size=64, output_size=1, dropout=0.2)
        
    def forward(self, x):
        x = self.bn(x)
        if self.training == True:
            # gaussianNoise = torch.normal(mean=0.0,std=torch.tensor([[0.03]*58]*32768).float())
            gaussianNoise = torch.randn(x.shape[0], 58) / 20  # stddev = 1/20, where 20 is hyper-param
            x0 = x + gaussianNoise.cuda()
        else:
            x0 = x
        
        # conv part
        # x_conv = (self.conv(x0.unsqueeze(1))).squeeze(1)
        
        # AutoEncoder part
        x_encoder = self.encoder(x0)
        x_decoder = self.decoder(x_encoder)
        x_ae = self.ae(x_decoder)
        outAe = self.aeAction(x_ae)
        
        # Main Regressor
        x_inp = torch.cat((x0, x_encoder), dim=1)
        x_inp = self.mlp(x_inp)  # shape: 32; i.e. nn-fatcors     
        outAction = self.outAction(x_inp)
        outRegressor = self.outRegressor(x_inp)
        
        # return x_inp (shape: 32) for Xgboost-Factors
        return x_inp, outRegressor, outAction, outAe, x_decoder
        
