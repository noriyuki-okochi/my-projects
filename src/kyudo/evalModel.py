import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from datetime import datetime

#
# NNモデルの定義
#
class EvalNN(nn.Module):
  def __init__(self, input_dim=10, s_frames=40,  output_size=11,
                     section_vocab_size=10, section_embed_dim=8 
                     #completed_vocab_size=3,
                     #completed_embed_dim=4
                     ):

    super(EvalNN, self).__init__() 

    self.csvfile = None
    self.csvpath = None 

    # GPUチェック
    self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    self.section_embed = nn.Embedding(section_vocab_size, section_embed_dim)
    #self.completed_embed = nn.Embedding(completed_vocab_size, completed_embed_dim)
    if section_embed_dim > 0:
        self.embed = True
    # NN入力サイズ：EVAL解析ベクトル + section埋め込み + completed埋め込み
    #self.input_size = (input_dim - 2) + section_embed_dim + completed_embed_dim
    self.input_dim = input_dim
    self.s_frames = s_frames
    if self.embed:
        self.input_size = s_frames*((input_dim - 1) + section_embed_dim)
    else:
        self.input_size = s_frames*input_dim
    self.output_size = output_size
    
    self.fc1 = nn.Linear(self.input_size, 256)
    self.fc2 = nn.Linear(256, 128)
    self.fc3 = nn.Linear(128, output_size)
  
  def get_class_name(self):
    return self.__class__.__name__

  def forward(self, x):
    _, s_frames, input_dim = x.size()
    if self.embed:
        input_dim -= 1                                  # sectionとcompletedを除いた入力次元数
        x  = x[:,:,:input_dim]                          # EVAL解析ベクトル部分を抽出
        #print(f"[EvalNN]:forward:input x1={x.shape}")
        
        sect_ids = x[:,-1,-2].long()                    # section列のインデックス
        #comp_ids = x[:,-1,-1].long()                   # completed列のインデックス
        sect_embed = self.section_embed(sect_ids)       # (batch_size, section_embed_dim)
        #comp_embed = self.completed_embed(comp_ids)    # (batch_size, completed_embed_dim)
        sect_embed_exp = sect_embed.unsqueeze(1).repeat(1, s_frames, 1)  # (batch_size, s_frames, section_embed_dim)
        #comp_embed_exp = comp_embed.unsqueeze(1).repeat(1, s_frames, 1) # (batch_size, s_frames, completed_embed_dim)
        
        x = torch.cat([x, sect_embed_exp], dim = -1)
        input_dim += sect_embed.size(1)

    # バッチサイズを維持して、特徴量をフラット化
    x = x.reshape(-1, s_frames*input_dim )          
    
    #x = F.relu(self.fc1(x))
    x = torch.tanh(self.fc1(x))
    x = torch.tanh(self.fc2(x))
    x = self.fc3(x)
    return x
#
# CSVファイルのオープン、書き込み、クローズ
# CSVファイルは、モデルの学習や評価の過程で、損失値や精度などの指標を記録するために使用されます。
# CSVファイルのオープンは、指定されたパスとファイル名で新しいCSVファイルを作成し、カラム名をヘッダーとして書き込みます。
# 書き込みは、指定された値をCSVファイルに行として追加します。クローズは、CSVファイルを閉じてリソースを解放します。
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
          print(f"[EvalNN]:close_csv:{self.csvpath}")
#
#
# NNモデルの定義
#
class EvalCNN(nn.Module):
  def __init__(self, input_dim=10, s_frames=40,  output_size=11):

    super(EvalCNN, self).__init__() 

    self.csvfile = None
    self.csvpath = None 

    # GPUチェック
    self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    #self.completed_embed = nn.Embedding(completed_vocab_size, completed_embed_dim)
    # NN入力サイズ：EVAL解析ベクトル + section埋め込み + completed埋め込み
    #self.input_size = (input_dim - 2) + section_embed_dim + completed_embed_dim
    self.input_dim = input_dim
    self.s_frames = s_frames
    self.output_size = output_size
    self.in_ch = 1
    self.out_ch = 8
    
    self.cnn1 = nn.Conv2d(self.in_ch, self.out_ch, kernel_size=3, padding=1)
    self.act1 = nn.ReLU()
    self.flat = nn.Flatten()
    self.fc1 = nn.Linear(self.out_ch * self.s_frames * self.input_dim, 128)
    self.fc2 = nn.Linear(128, output_size)
  
  def get_class_name(self):
    return self.__class__.__name__

  def forward(self, x):
    _, s_frames, input_dim = x.size()

    out = torch.tanh(self.cnn1(x.unsqueeze(1)))     # (batch_size, in_ch, s_frames, input_dim)
    # バッチサイズを維持して、特徴量をフラット化
    #x = x.reshape(-1, s_frames*input_dim ) 
    x = self.flat(out)                              # (batch_size, out_ch * s_frames * input_dim)         
    
    out = torch.tanh(self.fc1(x))
    out = self.fc2(out)
    return out
#
# CSVファイルのオープン、書き込み、クローズ
# CSVファイルは、モデルの学習や評価の過程で、損失値や精度などの指標を記録するために使用されます。
# CSVファイルのオープンは、指定されたパスとファイル名で新しいCSVファイルを作成し、カラム名をヘッダーとして書き込みます。
# 書き込みは、指定された値をCSVファイルに行として追加します。クローズは、CSVファイルを閉じてリソースを解放します。
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
          print(f"[EvalCNN]:close_csv:{self.csvpath}")
#
#eof 