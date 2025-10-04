import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
#
# RNNモデルの定義
#
class KyudoRNN(nn.Module):
  def __init__(self, input_size=1, hidden_size=64, output_size=1, n_layers=1):
    super(KyudoRNN, self).__init__() 
    # GPUチェック
    self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    self.n_layers = n_layers
    self.hidden_size = hidden_size
    
    self.rnn = nn.RNN(input_size, hidden_size, n_layers, batch_first=True)
    self.fc = nn.Linear(hidden_size, output_size)
    
  def forward(self, x):
    batch_size = x.size(0)
    inith = self.init_hidden(batch_size)
    out, hidden = self.rnn(x, inith)
    y = self.fc(out[:,-1,:])
    return y
  
  def init_hidden(self, batch_size):
    return torch.zeros(self.n_layers, batch_size, self.hidden_size).to(self.device)
#
# GRUモデルの定義
#
class KyudoGRU(nn.Module):
  def __init__(self, input_size=8, hidden_size=64, output_size=3, n_layers=1):
    super(KyudoGRU, self).__init__() 
    # GPUチェック
    self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    self.n_layers = n_layers
    self.hidden_size = hidden_size
    
    self.gru = nn.GRU(input_size, hidden_size, n_layers, batch_first=True)
    self.fc = nn.Linear(hidden_size, output_size)
    
  def forward(self, x):
    batch_size = x.size(0)
    inith = self.init_hidden(batch_size)
    #out, hidden = self.gru(x, inith)
    #y = self.fc(out[:,-1,:])
    _, hidden = self.gru( x, inith )
    y = self.fc( hidden.squeeze(0) )
    return y
  
  def init_hidden(self, batch_size):
    return torch.zeros(self.n_layers, batch_size, self.hidden_size).to(self.device)
#eof 