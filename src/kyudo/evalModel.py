import torch
import torch.nn as nn
#import torch.nn.functional as F
import torch.utils.tensorboard as tb
#import numpy as np
from datetime import datetime
''''''
# 規定モデル(Module)の定義
''''''
class EvalModule(nn.Module):
  def __init__(self, input_dim=9, s_frames=48,  output_size=6 ):

    super(EvalModule, self).__init__()     
    self.input_dim = input_dim
    self.s_frames = s_frames
    self.output_size = output_size
  
    # GPUチェック
    self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    self.csvfile = None
    self.csvpath = None 
    self.tb_writer = None
    
  def get_class_name(self):
    return self.__class__.__name__

  def forward(self, x):
    pass
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
      #
      if self.tb_writer is None:
         # TensorBoardのログディレクトリを指定して、SummaryWriterを作成
         tb_dir = path[:path.rfind('/')+1] + f"{fname}_{timestamp}_tb"
         self.tb_writer = tb.SummaryWriter(log_dir=tb_dir)  

  ## valuesを指定されたkeyでTensorBoardに記録
  def write_tb(self, values, key, step=None):
      if self.tb_writer is not None and key is not None:
        step = step if step is not None else values[0]
        self.tb_writer.add_scalar(key, values[1], step)  
  #
  def write_csv(self, values, key=None, step=None):
      if self.csvfile is not None:
        line = ''
        for v in values:
            if len(line) > 0: line += f"\t{v:.4f}"
            else: line += f"{v}"
        self.csvfile.write(line + "\n")
      
      if self.tb_writer is not None and key is not None:
          self.write_tb(values, key, step)  

  def close_csv(self):
      if self.csvfile is not None:
          self.csvfile.close()
          self.csvfile = None
          print(f"[EvalNN]:close_csv:{self.csvpath}")
      #      
      if self.tb_writer is not None:
          self.tb_writer.close()

''''''
# NNモデルの定義
''''''
class EvalNN(EvalModule):
  def __init__(self, input_dim=9, s_frames=40,  output_size=6,
                     section_vocab_size=10, section_embed_dim=8 
                     ):

    super(EvalNN, self).__init__(
        input_dim=input_dim, s_frames=s_frames, output_size=output_size
    ) 

    self.section_embed = nn.Embedding(section_vocab_size, section_embed_dim)
    #self.completed_embed = nn.Embedding(completed_vocab_size, completed_embed_dim)
    if section_embed_dim > 0:
        self.embed = True
    # NN入力サイズ：EVAL解析ベクトル + section埋め込み + completed埋め込み
    #self.input_size = (input_dim - 2) + section_embed_dim + completed_embed_dim
    if self.embed:
        self.input_size = s_frames*((input_dim - 1) + section_embed_dim)
    else:
        self.input_size = s_frames*input_dim
    
    self.fc1 = nn.Linear(self.input_size, 256)
    self.fc2 = nn.Linear(256, 128)
    #self.fc3 = nn.Linear(128, output_size)
    self.fc3 = nn.Linear(128, output_size - 1)          # 損失関数をCoralLossに変更

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
''''''
# CNNモデルの定義
''''''
# （試作版）
class EvalCN_(EvalModule):
  def __init__(self, input_dim=9, s_frames=48,  output_size=6):

    super(EvalCN, self).__init__(
        input_dim=input_dim, s_frames=s_frames, output_size=output_size
    )
    self.in_ch = 1
    self.out_ch = 8
    
    self.cnn1 = nn.Conv2d(self.in_ch, self.out_ch, kernel_size=3, padding=1)
    self.act1 = nn.ReLU()
    self.flat = nn.Flatten()
    self.fc1 = nn.Linear(self.out_ch * self.s_frames * self.input_dim, 128)
    #self.fc2 = nn.Linear(128, output_size)
    self.fc2 = nn.Linear(128, output_size - 1)      # 損失関数をCoralLossに変更

  def forward(self, x):
    _, s_frames, input_dim = x.size()

    x = self.act1(self.cnn1(x.unsqueeze(1)))     # (batch_size, in_ch, s_frames, input_dim)
    # バッチサイズを維持して、特徴量をフラット化
    #x = x.reshape(-1, s_frames*input_dim ) 
    x = self.flat(x)                              # (batch_size, out_ch * s_frames * input_dim)         
    
    #x = torch.tanh(self.fc1(x))
    x = torch.relu(self.fc1(x))
    x = self.fc2(x)
    return x
#
#（改良版）
class EvalCN(EvalModule):
  def __init__(self, input_dim=9, s_frames=48,  output_size=6):

    super(EvalCN, self).__init__(
        input_dim=input_dim, s_frames=s_frames, output_size=output_size
    )
    self.in_ch = 1
    self.out_ch = 16
    
    self.cnn1 = nn.Conv2d(self.in_ch, self.out_ch, kernel_size=3, padding=1)
    self.act1 = nn.ReLU()
    self.pool1 = nn.MaxPool2d(kernel_size=(2, 2))   # 時間x特徴量を圧縮
    
    # Global Average Pooling（Flatten の代わり）
    self.gap = nn.AdaptiveAvgPool2d((1, 1))

    # 全結合
    self.fc1 = nn.Linear(self.out_ch, 64)
    #self.fc2 = nn.Linear(64, output_size)
    self.fc2 = nn.Linear(64, output_size - 1)       # 損失関数をCoralLossに変更

  def forward(self, x):
    # x: (batch, s_frames, input_dim)
    x = x.unsqueeze(1)              # → (batch, 1, s_frames, input_dim)
    x = self.act1(self.cnn1(x))
    x = self.pool1(x)               # → (batch, out_ch, s_frames/2, input_dim/2)

    x = self.gap(x)                 # → (batch, out_ch, 1, 1)
    x = x.squeeze(-1).squeeze(-1)   # → (batch, out_ch)

    x = torch.relu(self.fc1(x))
    #x = torch.tanh(self.fc1(x))
    x = self.fc2(x)
    return x
#
#eof 