import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from datetime import datetime

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
    #
    self.csvfile = None
    self.csvpath = None 
    # GPUチェック
    self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    self.n_layers = n_layers
    self.hidden_size = hidden_size
    
    self.gru = nn.GRU(input_size, hidden_size, n_layers, batch_first=True)
    self.fc = nn.Linear(hidden_size, output_size)
    #self.softmax = nn.Softmax(dim=1)
    self.heads = nn.ModuleList([ nn.Linear(hidden_size, output_size) for _ in range(9) ])
  
  def forward(self, x):
    batch_size = x.size(0)
    inith = self.init_hidden(batch_size)
    #out, hidden = self.gru(x, inith)
    #y = self.fc(out[:,-1,:])
    _, hidden = self.gru( x, inith )
    y = self.fc( hidden.squeeze(0) )
    return y
  
  # 初期隠れ状態の生成
  def init_hidden(self, batch_size):
    return torch.zeros(self.n_layers, batch_size, self.hidden_size).to(self.device)
  
  # 出力マスク
  def mask_output(self, y, section, completed):
    aloowed = [0, 2*section - 1, 2*section]  # 0:移行中, 1:完了, 2:開始
    mask = torch.zeros_like(y)
    mask[:, aloowed] = 1
    ym = y * mask
    return ym
  
  # CSVファイルのオープン、書き込み、クローズ
  def open_csv(self, headers='', path="./", fname='model'):
      # CSV出力ファイルの作成
      timestamp = datetime.now().strftime('%Y%m%d')
      self.csvpath = path[:path.rfind('/')+1] + f"{fname}_{timestamp}.csv"
      self.csvfile = open( self.csvpath, 'w')
      # カラム名を出力
      line = ''
      for name in headers:
          if len(line) > 0: line += f",{name}"
          else: line += name
      self.csvfile.write(line + "\n")
      self.csvfile.flush()
      
  def write_csv(self, values):
      if self.csvfile is None: return
      line = ''
      for v in values:
          if len(line) > 0: line += f",{v:.4f}"
          else: line += f"{v}"
      self.csvfile.write(line + "\n")

  def close_csv(self):
      if self.csvfile is not None:
          self.csvfile.close()
          self.csvfile = None
          print(f"[KyudoGRU]:close_csv:{self.csvpath}")
#eof 