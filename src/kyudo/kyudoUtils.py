import torch
import torch.nn as nn
from torch import optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from torch.optim import lr_scheduler
import numpy as np
#import matplotlib.pyplot as plt
from datetime import datetime

import logging
DEBUG = logging.DEBUG
INFO = logging.INFO
ERROR = logging.ERROR
# local package
from kyudo.env import * 

LOG_FILE_MODE = 'w'
CSV_FILE_MODE = 'a'
LOSS_FILE_MODE = 'w'

ulog = logging.getLogger(__name__)
filehandler = logging.FileHandler('./log/kyudoApp.log', mode=LOG_FILE_MODE)  # ログファイルの設定
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # ログフォーマットの設定
formatter = logging.Formatter('%(message)s')  # ログフォーマットの設定
filehandler.setFormatter(formatter)  # フォーマッタをハンドラに設定
ulog.addHandler(filehandler)  # ログハンドラを追加
ulog.setLevel(DEBUG)    # ログレベルの設定
ulog.setLevel(INFO)     # ログレベルの設定
DF2CSV_enabled = True

# モデル保存用のファイル名
MODEL_NAME = 'kyudo_model'

# GPUチェック
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
#
# ログ出力関数
# fmtmsg: フォーマット済みメッセージ
# ログは標準出力とログファイルへ出力する
def log_write(fmtmsg, print_enabled=True):
    if print_enabled: print(fmtmsg)
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
    else: out_csv = f"./log/kyudo_debug_{case_name}.csv"
    # CSVファイルのヘッダー出力
    if title is not None:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f = open(out_csv, CSV_FILE_MODE)
        f.write(f"# {title}: {timestamp}\n")
        f.close()
    # CSVファイルのデータ出力  
    if file is not None:
        df.to_csv(out_csv, mode='w', float_format='%.4f', na_rep='NaN', sep='\t')
    elif DF2CSV_enabled:    
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
        print(f"[get_hyper_parameters]:params={params}")
        if len(params) > 0:
          values = [None] * len(def_parameters)
          for i, p in enumerate(params):
            p = p.strip()
            if p.isnumeric(): values[i] = int(p)
            elif p.replace('.','',1).isnumeric(): values[i] = float(p)
            else: values[i] = def_parameters[i]
          parameters = tuple( values )
    
    return parameters
#
# 特徴量カラム名取得関数
# features: 特徴量リスト
def get_feature_colnames( features ):
    colnames = []
    for f in features:
        items = f.split(' ')
        try:
            idx = items.index('as')
            if idx > 0 and (idx + 1) < len(items):
                colname = items[idx + 1]
                colnames.append( colname )
        except ValueError:
            pass
    return colnames
#    
# デバイスの取得
# 戻り値: device
def get_device():
    print(f"[get_device]:device={device}")
    return device
#
# セクションと完了状態の更新関数
# action: モデルの出力アクション  
# section: 現在のセクション
# completed: 現在の完了状態
# output_size: モデルの出力サイズ
# 戻り値: 更新後の(section, completed)  
def update_section_completed( action, section, completed, output_size):
    #
    if output_size == 3:
        if action == 1:       # 動作完了
            completed = 1
        elif action == 2:     # 動作開始
            #section = min(section + 1, 9) 
            if section == 9: section = 2
            else: section = section + 1 
            completed = 0
    #
    elif output_size == 19:
        if action == 0:         # 完了への移行
            completed = 0
        elif action % 2 == 0 :  # 動作完了
            section = action / 2
            completed = 1
        else:                   # 動作開始
            section = (action + 1) / 2
            completed = 0
    return section, completed
      
        
#
# earlystoppingクラス
# patience: 最小値の非更新数カウンタ
# verbose: 表示設定 
# path: モデル格納path
class EarlyStopping:
    def __init__(self, patience=5, delta=0, verbose=False, path=None):
        self.patience = patience        #設定ストップカウンタ
        self.delta = delta              #スコアの最小更新幅
        self.verbose = verbose          #表示の有無
        self.counter = 0                #現在のカウンタ値
        self.best_score = None          #ベストスコア
        self.early_stop = False         #ストップフラグ
        self.val_loss_min = np.Inf      #前回のベストスコア記憶用
        self.path = path                #ベストモデル格納path
        
    #    特殊(call)メソッド
    #    実際に学習ループ内で最小lossを更新したか否かを計算させる部分
    #    val_loss: 検証用のloss値
    #    model: 学習中のモデル"""
    def __call__(self, epoch, val_loss, model):
        score = -val_loss   #スコアはlossのマイナス値（lossが小さいほどスコアが高い）
        if self.best_score is None:         
            #1Epoch目の処理
            self.best_score = score     
            self.checkpoint(val_loss, model)    #記録後にモデルを保存してスコア表示する
        elif score < self.best_score + self.delta:       
            # ベストスコアを更新できなかった場合
            self.counter += 1                   #ストップカウンタをインクリメント
            if not self.verbose:  
                print(f'epoch:{epoch:3d}, stopping counter: {self.counter} out of {self.patience}')  #現在のカウンタを表示する 
            if self.counter >= self.patience:   #設定カウントを上回ったらストップ
                self.early_stop = True
        else:  
            #ベストスコアを更新した場合
            self.best_score = score             #ベストスコアを上書き
            self.checkpoint(val_loss, model)    #モデルを保存してスコア表示
            self.counter = 0                    #ストップカウンタリセット

    # 
    # ベストスコア更新時に実行されるチェックポイント関数
    # val_loss: 検証用のloss値
    # model: 学習中のモデル
    def checkpoint(self, val_loss, model):
        if self.verbose:  #表示を有効にした場合は、前回のベストスコアからどれだけ更新したか？を表示
            print(f'Validation loss decreased ({self.val_loss_min:.6f} -> {val_loss:.6f}).  Saving model ...')
        if self.path is not None:
            torch.save(model.state_dict(), self.path)  #ベストモデルを指定したpathに保存
        self.val_loss_min = val_loss  #その時のlossを記録する

#
# GRUモデルの学習用TensorDatasetを編集する関数
#
def edit_TesorDataset( np_x, np_yact, s_frames ):
    input_frames, input_size = np_x.shape
    # 先頭s_frames分のデータを1セット（ゼロ値データ）として扱う
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
    
    return TensorDataset(x_data, y_data)

# GRUモデルの学習を実行する関数
# model: GRUモデル
# s_frames: 1セットのフレーム数 
# np_train: 学習入力データ (input_frames, input_size)
# np_valid: 検証データ (input_frames,)
# batch_size: バッチサイズ
# n_epoch: エポック数
# pth: 学習結果のモデルを保存するファイルパス（Noneの場合はデフォルト名）
def train_Kyudo( model ,s_frames, np_train, np_valid=None,  batch_size=32, n_epoch=280, r_factor=1.0, pth=None):
    # 学習結果のモデル保存用ファイル名の決定
    if pth is not None:
        model_pth = pth
    else:
        class_name:str = model.get_class_name()
        model_name = f'{MODEL_NAME}{class_name[-1]}'
        model_name +=  'e' if model.embed else 'n'
        output_size = model.output_size
        model_pth = pth if pth is not None else f"./{model_name}_{input_size}-{s_frames}-{output_size}.pt"
    log_write(f"[train_Kyudo]:model will be saved as {model_pth}")

    # 学習用TensorDatasetを編集する
    np_x, np_yact = np_train
    _, input_size = np_x.shape
    log_write(f"[train_Kyudo]:np_x={np_x.shape}, np_yact={np_yact.shape}")

    dataset = edit_TesorDataset( np_x, np_yact, s_frames )
    loader = DataLoader(dataset, batch_size, shuffle=False)

    # 検証TensorDatasetを編集する
    if np_valid is not None:
        np_valid_x, np_valid_yact = np_valid
        valid_dataset = edit_TesorDataset( np_valid_x, np_valid_yact, s_frames )
        valid_loader = DataLoader(valid_dataset, batch_size, shuffle=False)

    # 損失関数と最適化手法の定義
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=Learning_rate)
    model.open_csv( ['epoch','loss_train'], path="./", fname='loss_train',mode=LOSS_FILE_MODE )
    
    # 学習率のスケジューラー
    if np_valid is None:
        # 学習率を 1/10 に
        # 3エポック改善しなければ発動
        if r_factor < 1.0:
            scheduler = lr_scheduler.ReduceLROnPlateau(optimizer,mode = 'min',factor = r_factor,patience = 3)
            # 10エポックごとに学習率を0.95倍に減衰
            #scheduler = lr_scheduler.StepLR(optimizer, step_size = 10, gamma = r_factor)  
    else:
        if r_factor < 1.0:
            scheduler = lr_scheduler.ReduceLROnPlateau(optimizer,mode = 'min',factor = r_factor,patience = 3)
        # EarlyStoppingのインスタンスを作成
        earlystop = EarlyStopping(patience = 7, delta = 0, path = model_pth, verbose = False)  
      
    # 学習ループ
    for i in range( n_epoch ):
        model.train()
        loss_train = 0
        for j, (x, t) in enumerate(loader):
            # 順伝搬、損失計算、逆伝搬、パラメータ更新
            y = model(x)                        # y: (batch, output_size)
            loss = criterion( y, t.squeeze() )  # t: (batch, 1) -> (batch,)
            
            # L2正則化の追加            
            if L2_lambda > 0.0:
                l2_norm = sum(p.pow(2.0).sum() for p in model.parameters())
                loss = loss + L2_lambda * l2_norm
            # accumulate loss
            loss_train += loss.item()
            # 勾配の初期化
            optimizer.zero_grad()
            # 
            loss.backward()
            optimizer.step()
        # calculate average loss
        loss_train /= (j + 1)                 
        #record_loss_train.append(loss_train)   # record loss to list    
        model.write_csv( [i, loss_train] )      # 学習過程をCSVファイルに出力
        if i%20 == 0 or i == (n_epoch - 1):
            # 20エポックごとに学習過程を表示
            #log_write(f'epoch:{i:3d}, iter={j}, loss_train={loss_train:.4f},y={y[0]}')
            log_write(f'epoch:{i:3d}, iter={j}, loss_train={loss_train:.4f},lr={optimizer.param_groups[0]['lr']:.8f}')
        #
        if np_valid is None:
            if r_factor < 1.0:
                scheduler.step(loss_train)      # 学習率の更新
        else:  
            model.eval()
            loss_valid = 0
            with torch.no_grad():
                for j, (x, t) in enumerate(valid_loader):
                    y = model(x)
                    loss = criterion( y, t.squeeze() )
                    loss_valid += loss.item()
            loss_valid /= (j + 1)
            #log_write(f'epoch:{i:3d}, iter={j}, loss_valid={loss_valid:.4f},lr={optimizer.param_groups[0]['lr']:.8f}')
            if r_factor < 1.0:
                scheduler.step(loss_valid)      # 学習率の更新
            earlystop(i, loss_valid, model)        # EarlyStoppingの呼び出し
            if earlystop.early_stop:
                log_write(f"Early stopping at epoch {i:3d}")
                break
        #
        
    model.close_csv()      
    if np_valid is None:
        #  学習結果のモデルを保存する
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
def predict_Kyudo( model, np_x, s_frames, log_print=True):
    # 予測データ
    input_frames, input_size = np_x.shape
    #ulog.debug(f"[predict_Kyudo]:np_x={np_x.shape}") 
        
    immediately = True if input_frames == s_frames else False
    if not immediately:
        # 先頭s_frames分のデータを1セット（ゼロ値データ）として扱う
        #input_frames -= s_frames
        x_zeros = np.zeros( (s_frames, input_size) )
        x = np.vstack( [x_zeros, np_x] )
    else:
        x = np_x
        input_frames = 1
    #ulog.debug(f"[predict_Kyudo]:x={x.shape}")     
    #ulog.debug(f"[predict_Kyudo]:x={x}")
    #
    x_data = np.zeros( (input_frames, s_frames, input_size) )
    for i in range(input_frames):
        x_data[i] = x[i:i + s_frames].reshape(-1, input_size)
        
    if immediately:
        section = x_data[0:,-1, -2]
        completed = x_data[0:,-1, -1]
    else:
        section = x_data[1,-1, -2]
        completed = x_data[1,-1, -1]        
        x_data[1:,:, -2] = 0.0   # section
        x_data[1:,:, -1] = 0.0   # completed
          
    x_data = torch.tensor(x_data, dtype=torch.float32).to(device )
    ulog.debug(f"[predict_Kyudo]:x_data={x_data.shape}")
    
    y_data = np.zeros( (input_frames, 1) ,dtype=np.int64)
    #print(y_data.shape)  
    i = 0
    model.eval()
    for t in range(input_frames):
        x = x_data[t].reshape(1, s_frames, input_size)
        ulog.debug(f"[predict_Kyudo]:t={t}:{x}")
        with torch.no_grad():
            y_pred = model(x)
            action = torch.argmax( y_pred, dim=1).item()
        #
        if action != 0:
            i += 1
            log_write(f"[predict_Kyudo]:({i:2d}) not zero action={action}, t={t}", log_print)    
        ulog.debug(f"[predict_Kyudo]:action={action}")
        y_data[t] = action
        
        if not immediately:
            # セクションと完了状態の更新
            section, completed = update_section_completed( action, section, completed, model.output_size)
            ulog.debug(f"[predict_Kyudo]:section={section}:completed={completed}")
                
            # 状態を次の入力データに埋め込む
            for k in range(1, s_frames):
                if (t + k) < input_frames:
                    x_data[t + k, -k, -2] = float(section)
                    x_data[t + k, -k, -1] = float(completed)
    #        
    y_data = y_data.reshape(-1)  
    ulog.debug(f"[predict_Kyudo]:y_pred={y_data.shape}")   
    return y_data 
  
  

