import torch
import torch.nn as nn
from torch import optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

import logging
DEBUG = logging.DEBUG
INFO = logging.INFO
ERROR = logging.ERROR
ulog = logging.getLogger(__name__)
filehandler = logging.FileHandler('kyudo_util.log', mode='a')  # ログファイルの設定
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # ログフォーマットの設定
formatter = logging.Formatter('%(message)s')  # ログフォーマットの設定
filehandler.setFormatter(formatter)  # フォーマッタをハンドラに設定
ulog.addHandler(filehandler)  # ログハンドラを追加
ulog.setLevel(DEBUG)  # ログレベルの設定

# モデル保存用のファイル名
MODEL_NAME = 'kyudo_model'

# GPUチェック
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
#
# ログ出力関数
# fmtmsg: フォーマット済みメッセージ
# ログは標準出力とログファイルへ出力する
def log_write(fmtmsg):
    print(fmtmsg)
    ulog.info(fmtmsg)
#
# デバッグ用CSV出力関数
# df: 出力するDataFrame
# case_name: ケース名
# title: CSVファイルのタイトル（ヘッダー）
# file: 出力ファイル名（Noneの場合はデフォルト名）
def df2csv(df, case_name='none', title=None, file=None):
    # CSV出力ファイルの作成
    if file is not None: out_csv = file
    else: out_csv = f"kyudo_debug_{case_name}.csv"
    # CSVファイルのヘッダー出力
    if title is not None:
      timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      f = open(out_csv, 'a')
      f.write(f"# {title}: {timestamp}\n")
      f.close()
    # CSVファイルのデータ出力      
    df.to_csv(out_csv, mode='a', float_format='%.4f', na_rep='NaN', sep='\t')
#
# ハイパーパラメータの取得関数
# cmds: コマンドライン引数リスト
# def_parameters: デフォルトのハイパーパラメータタプル
# 戻り値: ハイパーパラメータタプル
def get_hyper_parameters(cmds, def_parameters):
    parameters = def_parameters
    i = cmds.index('-hparam')
    if len(cmds) > (i + 1):
        params = cmds[i+1][1:-1].split(',')   # (1,2,3,4,5)の形式で指定
        if len(params) > 0:
          values = [None] * len(def_parameters)
          for i, p in enumerate(params):
            if not p.isnumeric(): 
              if i < 3: values[i] = def_parameters[i]
            else: values[i] = int(p)
          parameters = tuple( values )
    
    return parameters
#    
# デバイスの取得
# 戻り値: device
def get_device():
    print(f"[get_device]:device={device}")
    return device
#  
# GRUモデルの学習を実行する関数
# model: GRUモデル
# np_x: 入力データ (input_frames, input_size)
# np_yact: 正解データ (input_frames,)
# s_frames: 1セットのフレーム数 
def train_Kyudo( model , np_x, np_yact, s_frames, batch_size=256, n_epoch=501, pth=None):
  
  input_frames, input_size = np_x.shape
  log_write(f"[train_Kyudo]:np_x={np_x.shape}, np_yact={np_yact.shape}")   
  # 訓練データ
  #
  # 先頭s_frames分のデータを1セット（ゼロ値データ）として扱う
  #input_frames -= s_frames
  x_zeros = np.zeros( (s_frames, input_size) )
  y_zeros = np.zeros( (s_frames, 1) )
  x = np.vstack( [x_zeros, np_x] )
  y_act = np.vstack( [y_zeros, np_yact] )
  log_write(f"[train_Kyudo]:x={x.shape}, y_act={y_act.shape}")   
  #
  x_data = np.zeros( (input_frames, s_frames, input_size) )
  y_data = np.zeros( (input_frames, 1) )  
  for i in range(input_frames):
    x_data[i] = x[i:i + s_frames].reshape(-1, input_size)
    y_data[i] = y_act[i + s_frames]
  #
  x_data = torch.tensor(x_data, dtype=torch.float32).to(device )
  y_data = torch.tensor(y_data, dtype=torch.int64).to(device )
  log_write(f"[train_Kyudo]:x_data={x_data.shape}")
  log_write(f"[train_Kyudo]:y_data={y_data.shape}")
  
  dataset = TensorDataset(x_data, y_data)
  loader = DataLoader(dataset, batch_size, shuffle=False)

  # 損失関数と最適化手法の定義
  criterion = nn.CrossEntropyLoss()
  optimaizer = optim.Adam(model.parameters(), lr=0.001 )
  
  #record_loss_train = []  # list to record loss value
  model.open_csv( ['epoch','loss_train'], path="./", fname='loss_train' )
  
  # 学習ループ
  for i in range(n_epoch):
    model.train()
    loss_train = 0
    for j, (x, t) in enumerate(loader):
      # 順伝搬、損失計算、逆伝搬、パラメータ更新
      y = model(x)                        # y: (batch, output_size)
      loss = criterion( y, t.squeeze() )  # t: (batch, 1) -> (batch,)
      loss_train += loss.item()
      # 勾配の初期化
      optimaizer.zero_grad()
      # 
      loss.backward()
      optimaizer.step()
    #  
    # calculate average loss
    #loss_train /= (j + 1)                 
    #record_loss_train.append(loss_train)  # record loss to list
    
    model.write_csv( [i, loss_train] )    # 学習過程をCSVファイルに出力
    if i%20 == 0:
      # 20エポックごとに学習過程を表示
      #log_write(f'epoch:{i:3d}, iter={j}, loss_train={loss_train:.4f},y={y[0]}')
      log_write(f'epoch:{i:3d}, iter={j}, loss_train={loss_train:.4f}')
      
  model.close_csv()      
  #  学習結果のモデルを保存する
  class_name:str = model.get_class_name()
  log_write(f"[train_Kyudo]:model class={class_name}")
  model_name = f'{MODEL_NAME}{class_name[-1]}'
  output_size = model.output_size
  model_pth = pth if pth is not None else f"./{model_name}_{input_size}-{s_frames}-{output_size}.pt"
  torch.save(model.state_dict(), model_pth)
  #
  ulog.debug(model.state_dict())
  log_write(f"[train_Kyudo]:model saved as {model_pth}")
  
  return #record_loss_train
#  
# GRUモデルを使って予測を実行する関数
# np_x: 入力データ (input_frames, input_size)
# s_frames: 1セットのフレーム数
# 戻り値: 予測データ (input_frames,)
#
def predict_Kyudo( model, np_x, s_frames):
  # 予測データ
  input_frames, input_size = np_x.shape
  log_write(f"[predict_Kyudo]:np_x={np_x.shape}")     
  
  # 先頭s_frames分のデータを1セット（ゼロ値データ）として扱う
  #input_frames -= s_frames
  x_zeros = np.zeros( (s_frames, input_size) )
  x = np.vstack( [x_zeros, np_x] )
  log_write(f"[predict_Kyudo]:x={x.shape}")     
  #ulog.debug(f"[predict_Kyudo]:x={x}")
 #
  x_data = np.zeros( (input_frames, s_frames, input_size) )
  for i in range(input_frames):
    x_data[i] = x[i:i + s_frames].reshape(-1, input_size)
  x_data[1:,:, -2] = 0.0   # section
  x_data[1:,:, -1] = 0.0   # completed
  
  x_data = torch.tensor(x_data, dtype=torch.float32).to(device )
  log_write(f"[predict_Kyudo]:x_data={x_data.shape}")
  
  y_data = np.zeros( (input_frames, 1) )
  print(y_data.shape)  
  section = 0
  completed = 0
  model.eval()
  for t in range(input_frames):
      x = x_data[t].reshape(1, s_frames, input_size)
      ulog.debug(f"[predict_Kyudo]:t={t}:{x}")
      with torch.no_grad():
          y_pred = model(x)
          action = torch.argmax( y_pred, dim=1).item()
      #
      if action != 0:
          log_write(f"[predict_Kyudo]:not zero action={action}, t={t}")    
      ulog.debug(f"[predict_Kyudo]:action={action}")
      y_data[t] = action
      '''
      if action == 1:       # 動作完了
          completed = 1
      elif action == 2:     # 動作開始
          section = min(section + 1, 9) 
          completed = 0
      '''
      if action == 0:         # 完了への移行
          completed = 0
      elif action % 2 == 0 :  # 動作完了
          section = action / 2
          completed = 1
      else:                   # 動作開始
          section = (action + 1) / 2
          completed = 0    
          
      ulog.debug(f"[predict_Kyudo]:section={section}:completed={completed}")
          
      # 状態を次の入力データに埋め込む
      for k in range(1, s_frames):
        if (t + k) < input_frames:
          x_data[t + k, -k, -2] = float(section)
          x_data[t + k, -k, -1] = float(completed)
        
  y_data = y_data.reshape(-1)  
  log_write(f"[predict_Kyudo]:y_pred={y_data.shape}")   
  return y_data 
  
  

