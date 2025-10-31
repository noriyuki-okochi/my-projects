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
  def __init__(self, input_size, hidden_size, n_layers,
               section_vocab_size=10,
               section_embed_dim=8,
               completed_vocab_size=3,
               completed_embed_dim=4):
    super(KyudoGRU, self).__init__() 
    #
    self.csvfile = None
    self.csvpath = None 
    # GPUチェック
    self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    self.n_layers = n_layers
    self.hidden_size = hidden_size 
    self.embed = False
    if section_embed_dim is not None:
      self.embed = True
      self.section_embed = nn.Embedding(section_vocab_size, section_embed_dim)
      self.completed_embed = nn.Embedding(completed_vocab_size, completed_embed_dim)

      # GRU入力サイズ：YOLO解析ベクトル + section埋め込み + completed埋め込み
      self.gru_input_size = (input_size - 2) + section_embed_dim + completed_embed_dim
    else:
      self.gru_input_size = input_size
    #    
    self.gru = nn.GRU(self.gru_input_size, hidden_size, n_layers, batch_first=True)
  
  def get_class_name(self):
    return self.__class__.__name__
  
  def forward(self, x):
    pass
  
  # 初期隠れ状態の生成
  def init_hidden(self, batch_size):
    return torch.zeros(self.n_layers, batch_size, self.hidden_size).to(self.device)
  
  # 出力マスク
  def mask_output(self, y, section):
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
#
# GRU(single-head)モデルの定義
#
class KyudoGRUs(KyudoGRU):
  def __init__(self, input_size=7, hidden_size=64, output_size=3, n_layers=1,
               section_embed_dim=8,
               completed_embed_dim=4):
    super(KyudoGRUs, self).__init__(input_size, hidden_size, n_layers,
                                   section_embed_dim=section_embed_dim,
                                   completed_embed_dim=completed_embed_dim) 
    #
    self.output_size = output_size
    self.fc = nn.Linear(hidden_size, output_size)
    #self.softmax = nn.Softmax(dim=1)
  
  def forward(self, x):
    """
    x: [batch, seq_len, input_size]
    - x[:, :, :5] → YOLO解析ベクトル
    - x[:, :, -2] → section（整数）
    - x[:, :, -1] → completed（整数）
    """
    batch_size, seq_len, featues_size = x.size()

    #section_no = int(x[0, -1, -2])          # section
    if self.embed is True:
      section_ids   = x[:, -1, -2].long()     # [batch]
      completed_ids = x[:, -1, -1].long()     # [batch]

      # 埋め込み 
      section_emb = self.section_embed(section_ids)       # [batch, section_embed_dim]
      completed_emb = self.completed_embed(completed_ids) # [batch, completed_embed_dim]
      # 時系列全体に複製
      section_emb_expanded = section_emb.unsqueeze(1).repeat(1, seq_len, 1)
      completed_emb_expanded = completed_emb.unsqueeze(1).repeat(1, seq_len, 1)

      # YOLO解析ベクトルのみ抽出
      featues_size -= 2
      yolo_features = x[:, :, :featues_size]  # [batch, seq_len, 5]
      # 結合してGRUへ
      x_concat = torch.cat([yolo_features, section_emb_expanded, completed_emb_expanded], dim=-1)
    else:
      x_concat = x
    #
    inith = self.init_hidden(batch_size)
    #out, _ = self.gru(x, inith)
    #y = self.fc(out[:,-1,:])
    _, hidden = self.gru( x_concat, inith )
    y = self.fc( hidden.squeeze(0) )
    return y
#
# GRU(multi-heads)モデルの定義
#
class KyudoGRUm(KyudoGRU):
  def __init__(self, input_size=7, hidden_size=64, output_size=3, n_layers=1,
               section_embed_dim=8,
               completed_embed_dim=4):
    super(KyudoGRUm, self).__init__(input_size, hidden_size, n_layers,
                                    section_embed_dim=section_embed_dim,
                                   completed_embed_dim=completed_embed_dim) 
    self.output_size = output_size
    # 複数の全結合層を用意（section数分）
    self.heads = nn.ModuleList([ nn.Linear(hidden_size, output_size) for _ in range(10) ])
  
  def forward(self, x):
    """
    x: [batch, seq_len, input_size]
    - x[:, :, :5] → YOLO解析ベクトル
    - x[:, :, -2] → section（整数）
    - x[:, :, -1] → completed（整数）
    """
    batch_size, seq_len, featues_size = x.size()

    section_no = int(x[0, -1, -2])            # section
    #
    if self.embed is True:
      section_ids   = x[:, -1, -2].long()     # [batch]
      completed_ids = x[:, -1, -1].long()     # [batch]

      # 埋め込み 
      section_emb = self.section_embed(section_ids)       # [batch, section_embed_dim]
      completed_emb = self.completed_embed(completed_ids) # [batch, completed_embed_dim]
      # 時系列全体に複製
      section_emb_expanded = section_emb.unsqueeze(1).repeat(1, seq_len, 1)
      completed_emb_expanded = completed_emb.unsqueeze(1).repeat(1, seq_len, 1)

      # YOLO解析ベクトルのみ抽出
      featues_size -= 2
      yolo_features = x[:, :, :featues_size]  # [batch, seq_len, 5]
      # 結合してGRUへ
      x_concat = torch.cat([yolo_features, section_emb_expanded, completed_emb_expanded], dim=-1)
    else:
      x_concat = x   
    #
    inith = self.init_hidden(batch_size)
    _, hidden = self.gru( x_concat, inith )
    y = self.heads[section_no]( hidden.squeeze(0) )   
    #   
    #y = self.mask_output( y, section )
    return y  
#
#eof 