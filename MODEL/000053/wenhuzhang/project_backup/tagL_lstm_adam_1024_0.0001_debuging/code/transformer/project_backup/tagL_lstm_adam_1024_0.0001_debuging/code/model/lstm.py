import torch
import torch.nn as nn


class LSTM_Model(nn.Module):
    def __init__(self, input_dim=1, hidden=100, layers=1, drop=0.0,  output_size=1):
        super().__init__()
        
        self.lstm = nn.LSTM(input_size=input_dim, hidden_size=hidden, num_layers=layers,
                        bias=True,batch_first=True,dropout=drop, bidirectional=False)
        self.linear = nn.Linear(hidden, output_size)
        

    def forward(self, input_seq):
        b, l, c = input_seq.size()
        lstm_out, hidden_cell = self.lstm(input_seq)
        predictions = self.linear(lstm_out.contiguous()).contiguous().view(b,l,-1)
        return predictions