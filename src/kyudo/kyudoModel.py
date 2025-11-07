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
               completed_vocab_size=3,
               section_embed_dim=8,
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
  def open_csv(self, headers='', path="./", fname='model', mode='w'):
      # CSV出力ファイルの作成
      timestamp = datetime.now().strftime('%Y%m%d')
      self.csvpath = path[:path.rfind('/')+1] + f"{fname}_{timestamp}.csv"
      self.csvfile = open( self.csvpath, mode)
      # カラム名を出力
      line = ''
      for name in headers:
          if len(line) > 0: line += f"\t{name}"
          else: line += name
      self.csvfile.write(line + "\n")
      self.csvfile.flush()
      
  def write_csv(self, values):
      if self.csvfile is None: return
      line = ''
      for v in values:
          if len(line) > 0: line += f"\t{v:.4f}"
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
                section_vocab_size=10, completed_vocab_size=3,
                section_embed_dim=8, completed_embed_dim=4):
    super(KyudoGRUs, self).__init__(input_size, hidden_size, n_layers,
                                    section_vocab_size=section_vocab_size,
                                    completed_vocab_size=completed_vocab_size,
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
    _, hidden = self.gru( x_concat, inith )
    y = self.fc( hidden.squeeze(0) )
    #y = self.mask_output( y, section )
    return y
#
# GRU(multi-heads)モデルの定義
#
class KyudoGRUm(KyudoGRU):
  def __init__(self, input_size=7, hidden_size=64, output_size=3, n_layers=1,
               section_vocab_size=10, completed_vocab_size=3,
               section_embed_dim=8, completed_embed_dim=4):
    super(KyudoGRUm, self).__init__(input_size, hidden_size, n_layers,
                                    section_vocab_size=section_vocab_size, 
                                    completed_vocab_size=completed_vocab_size,
                                    section_embed_dim=section_embed_dim, 
                                    completed_embed_dim=completed_embed_dim) 
    self.output_size = output_size
    '''
    # 複数の全結合層を用意（section数分）
    self.heads = nn.ModuleList([ nn.Linear(hidden_size, output_size) for _ in range(10) ])
    '''
    # 複数のGRU層を用意（section数分）
    self.heads = nn.ModuleList([ self.gru for _ in range(section_vocab_size) ])
    self.fc = nn.Linear(hidden_size, output_size)
  
  def forward(self, x):
    """
    x: [batch, seq_len, input_size]
    - x[:, :, :5] → YOLO解析ベクトル
    - x[:, :, -2] → section（整数）
    - x[:, :, -1] → completed（整数）
    """
    batch_size, seq_len, featues_size = x.size()

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
    # 連続するセクション（ブロック単位）情報を作成   
    blocks =[]
    no = int(x[0, -1, -2])                              # サンプルのセクション番号
    ii, section, nn = 0, no, 0
    for i in range(batch_size):
        no = int(x[i, -1, -2])
        if no != section:
            blocks.append((ii, section, nn))
            ii, section, nn = i, no, 1
        else: nn += 1
    if nn > 0 : blocks.append((ii, section, nn))
    
    # 連続するセクション（ブロック単位）毎に一括処理   
    y  = []
    for block in blocks:
        i, section_no, block_size = block
        x = x_concat[i:i+block_size]
        inith = self.init_hidden(block_size)
        _, hidden = self.heads[section_no]( x, inith )      # hidden: [block_size. 1, hidden_size]
        yi = self.fc( hidden.squeeze(0) )                   # [block_size, output_size]
        y.append(yi)
    #　バッチ単位にまとめる
    return torch.cat(y, dim=0)                              # [batch_size, output_size]  
##   
    '''
    # 複数のGRU層を適用（サンプル毎のループ処理） ：処理負荷が大きい
    inith = self.init_hidden(1)
    y = []
    for i in range(batch_size):
        section_no = int(x[i, -1, -2])                      # section
        xi = x_concat[i].unsqueeze(0)                       # [1, seq_len, featues_size]
        _, hidden = self.heads[section_no]( xi, inith )     # hidden: [1. 1, hidden_size]
        yi = self.fc( hidden.squeeze(0) )                   # [1, output_size]
        y.append(yi)
    return torch.cat(y, dim=0)                              # [batch_size, output_size]  
    '''
##   
    '''
    # 複数のGRU層を適用（一括処理） ：サンプルに対するセクション番号が適合していない不合理が存在
    section_no = int(x[0, -1, -2])                          # 先頭サンプルのセクション番号
    inith = self.init_hidden(batch_size)
    _, hidden = self.heads[section_no]( x_concat, inith )   # hidden: [1. 1, hidden_size]
    y = self.fc( hidden.squeeze(0) )                        # [1, output_size]
    return y                                                # [batch_size, output_size]  
    '''
##   
##   
    '''
    # 複数の全結合層を適用 ：精度が悪い
    inith = self.init_hidden(batch_size)
    _, hidden = self.gru( x_concat, inith )
    y = self.heads[section_no]( hidden.squeeze(0) )   
    return y                                                # [batch_size, output_size]  
    '''
    # 複数のGRU層を適用（同一セクション単位で一括処理）　
    # 連続するセクションの情報（開始、セクション番号、サンプル数）を収集する
#
#eof 