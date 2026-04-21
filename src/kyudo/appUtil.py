#
"""
"""
# appUtil
#     
import os
import pandas as pd
import math
from datetime import datetime
import time
from PIL import Image, ImageFont, ImageDraw
#
# local package
from  kyudo.env import * 
from  kyudo.param import * 
from  mysqlite3.mysqlite3 import MyDb

# アプリ専用のロガー設定
import logging
DEBUG = logging.DEBUG
INFO = logging.INFO
ERROR = logging.ERROR
mylog = logging.getLogger(__name__)
filehandler = logging.FileHandler('./log/appUtil.log', mode='w')    # ログファイルの設定
formatter = logging.Formatter('%(message)s')                        # ログフォーマットの設定
filehandler.setFormatter(formatter)                                 # フォーマッタをハンドラに設定
mylog.addHandler(filehandler)                                       # ログハンドラを追加

# ログレベルをDEBUGに設定（必要に応じて変更）
mylog.setLevel(INFO)  

#
# リングバッファのクラス定義
#
class RingBuffer:
    def __init__(self, size):
        self.size = size
        self.buffer = []
        self.index = 0      # 書き込みインデックス
        self.length = 0

    def append(self, item):
        if len(self.buffer) < self.size:
            self.buffer.append(item)
            self.length = self.length + 1
        else:
            self.buffer[self.index] = item
        self.index = (self.index + 1) % self.size

    def get(self, ipos=None):
        # ipos=None(0)のとき、最後の書き込みitemを返す
        if ipos is None: ipos = 0
        ipos = abs(ipos) + 1
        if ipos > self.length:
            return None
        
        idx = self.index - ipos 
        if idx < 0: idx = self.length - (ipos - self.index)
        return self.buffer[idx]
    
    def clear(self):
        self.buffer = []
        self.index = 0      # 書き込みインデックス
        self.length = 0
        
    def len(self):
        return self.length
#    
# 動作解析パラメータ設定用スタッククラス
#
class StackActParam:
    def __init__(self):
        self.pars = []   # 動作解析パラメータ（番号、値）のリスト
    def push(self, list):
        self.clear()
        for no, val in list:
            self.pars.append( (no, val) )
    def pop(self, idx=None):
        if len(self.pars) == 0:
            return None
        return self.pars.pop() if idx is None else self.pars.pop(idx)
    def get(self, idx):
        if len(self.pars) == 0 or idx >= len(self.pars):
            return None
        return self.pars[idx]
    def clear(self):
        self.pars = []
    def len(self):
        return len(self.pars)
#
#    閾値の計算を行うクラス    
#   
class Threshold:
    """
    :param block_height: ブロックの高さ（画像の高さ）
    """
    def __init__(self, block_height):
        self.block_height = block_height
    def __call__(self, ratio):
         return int(self.block_height * ratio)     # 閾値を計算して返す
    def ratio(self, val):
        return val / self.block_height             # 閾値の比率を計算して返す
#
#
#    キーポイントの解析データを操作するクラス定義
#
class Keypoint:
    """
    :param result: 解析データ:Tensor
    :param boxid: 解析対象バウンダリーボックスのID:int 
    """
    def __init__(self, result, boxid):
        self.keypoints = result.keypoints               # キーポイントリスト(Tensor)
        self.boxes = result.boxes                       # バウンダリーボックスリスト(Tensor)
        self.boxid = boxid                              # 解析対象のボックスID
        self.block_height = self.boxes.xywh[boxid][3]   # 解析対象のボックスの高さ
    
    def xy(self, pnt_name):
        """
        :param pnt_name: キーポイント名
        :return: キーポイントの座標 [x, y]ndarray
        """
        if pnt_name in Kn2idx: 
            return self.keypoints.xy[self.boxid][Kn2idx[pnt_name]]  # キーポイント名が定義されている場合、座標を返す
        else:
            mylog.log(ERROR, f"Keypoint.xy: キーポイント名 {pnt_name} は定義されていません")
            return None
        
    def conf(self, pnt_name):
        """
        :param pnt_name: キーポイント名
        :return: キーポイントの信頼度(float)
        """
        if pnt_name in Kn2idx:
            return self.keypoints.conf[self.boxid][Kn2idx[pnt_name]].item()  # キーポイント名が定義されている場合、信頼度を返す
        else:
            mylog.log(ERROR, f"Keypoint.conf: キーポイント名 {pnt_name} は定義されていません")
            return None
    
    def norm(self, pnt1_name, pnt2_name):
        """
        :param pnt1_name: キーポイント名1
        :param pnt2_name: キーポイント名2
        :return: キーポイント間の移動ベクトルの長さと角度 (norm, angl)
        """
        
        if pnt1_name in Kn2idx and pnt2_name in Kn2idx:
            pnt1 = self.keypoints.xy[self.boxid][Kn2idx[pnt1_name]]
            pnt2 = self.keypoints.xy[self.boxid][Kn2idx[pnt2_name]]
            vect = pnt2 - pnt1                                      # 2点のベクトルを計算
            norm, angl = vector_length_angle(vect.numpy())
            return norm, angl  # キーポイント名が定義されている場合、移動ベクトルの長さと角度を返す
        else:
            mylog.log(ERROR, f"Keypoint.norm: キーポイント名 {pnt1_name} または {pnt2_name} は定義されていません")
            return None
#
#
# 例外クラス
class BoundaryBoxError(Exception):
    pass
# キーポイント解析クラスの拡張クラス定義
class MyResult(Keypoint):
    MaxBox_id:int = None
    XYWH:int = [None, None, None, None]
    Skip:bool = False
    
    def __init__(self, result, frame, boxid=None):
        if boxid is None:
            # 検出結果から最大（対象）のボックスを取得
            boxno = self.get_max_box(result)
            if boxno == 0: 
                raise BoundaryBoxError('Target boundary-box can not be found.')
            else: boxid = boxno - 1
        super().__init__(result, boxid)
        
        self.result = result
        self.confs = result.keypoints.conf[boxid].numpy()   # 対象ボックスのキーポイントの信頼度リスト
        self.points = result.keypoints.xy[boxid].numpy()    # 対象ボックスのキーポイントの座標リスト
        self.xywh = result.boxes.xywh[boxid].numpy()        # バウンディングボックスの座標リスト [x, y, w, h]

        # 対象ボックスの合理性検証
        if boxid != MyResult.MaxBox_id or MyResult.Skip == True:
            mylog.log(DEBUG, f"[MyResult]:frame={frame}, "\
                            f" MaxBox_id changed.[{MyResult.MaxBox_id} -> {boxid}], xywh={self.xywh}") 
            if MyResult.MaxBox_id != None and abs(int(self.xywh[0]) - int(MyResult.XYWH[0])) > int(MyResult.XYWH[2]):
                # 前のボックスと現在のボックスの位置が大きくずれている場合、スキップ
                MyResult.Skip = True
                # 例外を発生させる
                raise BoundaryBoxError('Target boundary-box can not be found.')
            
            # クラス変数の初期化a5
            MyResult.Skip = False
            MyResult.MaxBox_id = boxid
        #
        MyResult.XYWH = self.xywh
        
        # 各キーポイントの移動ベクトルの長さの加重平均を格納するリスト（calc_moving_averageで作成_）
        self.arrow_moving_ave = np.zeros(len(Kn2idx))  
        # 過去のサンプルキーポイントの現在位置までの移動ベクトルの長さと角度のタプルを格納するリスト（calc_arrow_length_anglesで作成_）  
        self.arrow_length_angles = [None] * Sample_lag_Max
             
    #    検出結果から最前面のボックスを取得する関数
    def get_max_box(self,result):
        """
        :param result: YOLOv8の検出結果
        :return: 最大のボックスの番号（0は検出失敗）
        """
        if len(result.boxes) == 0: return 0  # 検出結果がない場合は0を返す
        
        boxes = result.boxes    # 検出されたバウンディングボックスの取得
        max_box_no = 0          # ボックスの番号
        mylog.log(DEBUG, f"[get_max_box]: {type(boxes)},{boxes.shape}:{len(boxes)}個のボックス")
        
        # 最前面の物体を決定（面積が最も大きいものを選択）
        area = np.array([])
        for i in range(len(boxes)):        #バウンディングボックスの面積をareaに格納
            if result.boxes.conf[i].item() < 0.3: 
                mylog.log(DEBUG, f"[get_max_box]: boxid={i}, conf={result.boxes.conf[i].item():.3f}  skip....")
                continue  # 信頼度が低いボックスは無視
            _, _, w, h = map(int, boxes.xywh[i])
            area = np.append(area, w * h)                   # 面積を計算して追加
        if len(area) > 0:
            # 最大のボックスのインデックスを取得
            max_box_no = area.argmax()           
            # 最大のボックスの情報を表示
            # インデックスは0から始まるため、1を加算
            conf = result.boxes.conf[max_box_no].item()  # 最大ボックスの信頼度を取得    
            max_box_no += 1  
            mylog.log(DEBUG, f"[get_max_box]: max_box_no={max_box_no}, conf={conf:.3f}, area:{area}, xywh:{boxes.xywh[max_box_no-1]}")             
        return max_box_no

    #　指定キーポイントの移動ベクトルの長さ（加重平均値）と角度をタプルで返す
    def tuple_ave_angle(self, idx):
        _, angle = self.arrow_length_angles[0][idx]         # idxの移動ベクトルの長さと角度を取得
        return self.arrow_moving_ave[idx], angle            # 移動ベクトルの長さ（加重平均値）と角度を返す
    
    # 指定キーポイントの移動ベクトルの長さ、角度を計算する            
    def vector_length(self, idx, points):
        """
        :param idx: キーポイントのインデックス
        :param points: リングバッファから取得した過去のポイント座標リスト
        :return: 各キーポイントの移動ベクトルの長さを格納するリスト
        """
        arrow_length = []                       # 各キーポイントの移動ベクトルのNorm
        points.append(self.points[idx])         # 現在のポイントを追加
        
        for i in range(len(points) - 1):        # リストの最後の要素までループ
            length, _ = vector_length_angle( (points[i + 1] - points[i]) )    
            arrow_length.append(length)         # 移動ベクトルの長さを追加
            
        mylog.log(DEBUG, f"[vector_length]: idx={idx}, points={points}, arrow_length={arrow_length}")
        return arrow_length  # 移動ベクトルの長さのリストを返す            
                
    # 移動ベクトルの長さの移動平均を計算する    
    def calc_moving_average(self, prePointsBuffer:RingBuffer, weights):        
        """
        :param prePointsBuffer: リングバッファ
        :return: None
        """
        window = len(weights)  # ウィンドウサイズを取得
        if prePointsBuffer.len() < window:
            mylog.log(INFO, f"[calc_moving_average]:バッファ数={prePointsBuffer.len()}, prePointsBuffer is insufficient.")
            return
        
        # リングバッファからキーポイントの時系列データを取得して、各点の移動ベクトルの長さの加重平均を計算
        for _, idx in Kn2idx.items():
            # リングバッファから過去のポイント座標を取得
            points = []
            for i in range(window):
                points.append( prePointsBuffer.get(i).points[idx] )         
                
            # 移動ベクトルの長さを格納するリストを作成する
            arrow_length = self.vector_length(idx, points)                  
            # 重みをつけて平均を計算
            self.arrow_moving_ave[idx] = np.average(arrow_length, weights=weights)  
    
    # 各キーポイントの過去から現在位置への移動ベクトルの長さと角度を計算する                    
    def calc_arrow_length_angles(self, prepointsBuffer:RingBuffer):
        for i in range(0, prepointsBuffer.length):              # 直近のポイント(=0)から始める
            preResult = prepointsBuffer.get( i )                # 過去のキーポイントデータを取得     
            arrow_points = self.points - preResult.points       # 過去のキーポイントと現在位置の差分ベクトルを計算
            # 各ベクトルの長さと角度を計算してリストにタプルとして格納
            self.arrow_length_angles[i] = [vector_length_angle(vect) for vect in arrow_points]   
            mylog.log(DEBUG, f"arrow_length_angles[{i}]: {self.arrow_length_angles[i]}") 
                     
                     
    def xy(self, pnt_name):
        """
        :param pnt_name: キーポイント名
        :return: キーポイントの座標 [x, y]ndarray
        """
        if pnt_name in Kn2idx: 
            return self.points[Kn2idx[pnt_name]]  # キーポイント名が定義されている場合、座標を返す
        else:
            mylog.log(ERROR, f"Keypoint.xy: キーポイント名 {pnt_name} は定義されていません")
            return None
        
    def conf(self, pnt_name):
        """
        :param pnt_name: キーポイント名
        :return: キーポイントの信頼度(float)
        """
        if pnt_name in Kn2idx:
            return self.confs[Kn2idx[pnt_name]]  # キーポイント名が定義されている場合、信頼度を返す
        else:
            mylog.log(ERROR, f"Keypoint.conf: キーポイント名 {pnt_name} は定義されていません")
            return None
    
    def norm(self, pnt1_name, pnt2_name):
        """
        :param pnt1_name: キーポイント名1
        :param pnt2_name: キーポイント名2
        :return: キーポイント間の移動ベクトルの長さと角度 (norm, angl)
        """
        
        if pnt1_name in Kn2idx and pnt2_name in Kn2idx:
            pnt1 = self.points[Kn2idx[pnt1_name]]
            pnt2 = self.points[Kn2idx[pnt2_name]]
            vect = pnt2 - pnt1                                      # 2点のベクトルを計算
            norm, angl = vector_length_angle(vect)
            return norm, angl  # キーポイント名が定義されている場合、移動ベクトルの長さと角度を返す
        else:
            mylog.log(ERROR, f"Keypoint.norm: キーポイント名 {pnt1_name} または {pnt2_name} は定義されていません")
            return None

##    特徴量のデータフレームクラス
class FeaturePdf:
    # 入力データ次元数に応じた特徴量のカラム名リスト
    # ・env.py定義の読み込みリストの別名と一致させる
    Features_list_60 = [ 'rw_ratio', 'rl_ratio', 'eyes_ratio',\
                        'hr_ratio',\
                        'section','completed' ]
    Kyudo_index_60   = { 4:'h', 8:'h', 20:'w',\
                        10:'h'}
    Features_list_61 = [ 'rw_ratio', 'rl_ratio', 'hr_ratio',\
                        'face',\
                        'section','completed' ]
    Kyudo_index_61   = { 4:'h', 8:'h', 10:'h',\
                        22:''}

    Features_list_70 = [ 'rw_ratio', 'lw_ratio', 'eyes_ratio',\
                        'hr_ratio', 'hr_deg',\
                        'section','completed' ]
    Kyudo_index_70   = { 4:'h', 6:'h', 20:'w',\
                        10:'h', 11:'d'}

    Features_list_71 = [ 'rw_ratio', 'rl_ratio', 'hr_ratio',\
                        'hr_deg', 'face',\
                        'section','completed' ]
    Kyudo_index_71   = { 4:'h', 8:'h', 10:'h',\
                        11:'d', 22:''}

    Features_list_72 = [ 'rw_ratio', 'rl_ratio', 'hr_ratio',\
                        'body', 'face',\
                        'section','completed' ]
    Kyudo_index_72   = { 4:'h', 8:'h', 10:'h',\
                        23:'', 22:''}


    Features_list_80 = [ 'rw_ratio', 'rl_ratio', 'hr_ratio',\
                        'hr_deg', 'body', 'face',\
                        'section','completed' ]
    Kyudo_index_80   = { 4:'h', 8:'h', 10:'h',\
                        11:'d', 23:'', 22:'' }

    Features_list_81 = [ 'rw_ratio', 'lw_ratio', 'eyes_ratio',\
                        'rl_ratio', 'hr_ratio', 'hr_deg',\
                        'section','completed' ]
    Kyudo_index_81   = { 4:'h', 6:'h', 20:'w',\
                         8:'h', 10:'h', 11:'d' }

    Features_list_90 = [ 'rw_ratio', 'lw_ratio', 'eyes_ratio',\
                        'rl_ratio', 'hr_ratio', 'hr_deg', \
                        'face', \
                        'section','completed' ]
    Kyudo_index_90   = { 4:'h', 6:'h', 20:'w',\
                         8:'h', 10:'h', 11:'d',\
                         22:'' }
    
    Features_index = { 60: (Features_list_60, Kyudo_index_60),
                       61: (Features_list_61, Kyudo_index_61), 
                       70: (Features_list_70, Kyudo_index_70), 
                       71: (Features_list_71, Kyudo_index_71), 
                       72: (Features_list_72, Kyudo_index_72), 
                       80: (Features_list_80, Kyudo_index_80), 
                       81: (Features_list_81, Kyudo_index_81), 
                       90: (Features_list_90, Kyudo_index_90) 
                       }
    
    def __init__(self, input_key:int=Current_feature_key, seq_frames:int=Input_dim):
        self.seq_size = seq_frames
        self.kyudo_data_list = [None]*len(Kyudo_data_names)
        self.curPdf:pd.DataFrame = None
        self.prePdf:pd.DataFrame = None
        
        self.input_key = input_key                          # 6 or 7 or 8
        features, _ = FeaturePdf.Features_index[input_key]
        self.input_dim = len(features)                      # 入力データ次元数
        self.features_list = [None]*self.input_dim          # 特徴量データリスト
    
    def set_kyudo_data_list(self, data_list):
        self.kyudo_data_list = data_list
        
    def get_kyudo_data_list(self):
        return self.kyudo_data_list

    def set_current_pdf(self, section_no, completed):
        pre_features_list = self.features_list.copy()       # 直前の特徴量リストを保存
        column_names, kyudo_index = FeaturePdf.Features_index[self.input_key]
        #
        box_w = self.kyudo_data_list[2]    # box_width 
        box_h = self.kyudo_data_list[3]    # box_height 
        i = 0
        for idx, c in kyudo_index.items():
            if c == 'h':   # heightで正規化
                self.features_list[i] = self.kyudo_data_list[idx]/box_h
            elif c == 'w': # widthで正規化
                self.features_list[i] = self.kyudo_data_list[idx]/box_w
                if Eyes_ratio_threshold > 0.0 and column_names[i] == 'eyes_ratio':
                    # 目の横幅を0.01/0.1に補正
                    self.features_list[i] = Eyes_ratio_min if self.features_list[i] < Eyes_ratio_threshold \
                                            else Eyes_ratio_max
            elif c == 'd': # degreeで正規化
                self.features_list[i] = self.kyudo_data_list[idx]/180.0
            else:          # 正規化なし
                self.features_list[i] = self.kyudo_data_list[idx]
                
            #  正規化後の値が1.0を超えた場合、エラーコード（リスト番号）を返す
            #  ー＞　直前の特徴量データを採用する
            if c != '' and self.features_list[i] > 1.0:
                if pre_features_list[i] is None or pre_features_list[i] > 1.0:
                    # 直前の特徴量データも不正な場合、エラーコード（リスト番号）を返す
                    return (i + 1)   
                else:
                    mylog.log(INFO, f"[set_current_pdf]: "\
                        + f"invalid_value({i}) {self.features_list[i]:.4f} replaced by {pre_features_list[i]:.4f}")
                    # 直前の特徴量データを採用する
                    self.features_list[i] = pre_features_list[i]                     
            i += 1
        #
        self.features_list[i] = section_no                          # section
        i += 1
        self.features_list[i] = 1 if completed else 0               # completed 
          
        mylog.log(DEBUG, f"[set_current_pdf]: {self.features_list}")
        
        narray = np.array(self.features_list).reshape(1, -1)
        self.curPdf = pd.DataFrame(narray, columns=column_names)
        return 0
    
    def add_previous_pdf(self):
        if self.prePdf is None:
            self.prePdf = self.curPdf.copy()                        # カレントデータで初期作成
        else:
            self.prePdf = pd.concat([self.prePdf, self.curPdf])     # 過去データに結合
            
    def update_previous_pdf(self):
        self.prePdf = self.prePdf.iloc[1:]                          # 先頭行を削除
        self.prePdf =  pd.concat([self.prePdf, self.curPdf])        # カレントデータを追加
        
    def get_input_pdf(self):
        return pd.concat([self.prePdf, self.curPdf])                # 現在と過去のデータを結合して返す
    
    def is_ready(self):
        if self.prePdf is None: return False
        elif len(self.prePdf) < self.seq_size - 1: return False
        else:                                                       # 十分なデータが揃っている場合
            return True
    
    def set_zero_previous_pdf(self, rate:float = 1.0):
        zero_data_list = [0.0]*len(Kyudo_data_names)
        zero_data_list[3] = 1.0     # box_height(any not zero)
        for _ in range( int(self.seq_size*rate) ):
            self.set_kyudo_data_list( zero_data_list )
            self.set_current_pdf(0, 0)
            self.add_previous_pdf()
#
# 日本語テキストの描画
#    color = (r, g, b)
#
def draw_text(imag, message, point, color , font_size=20):
    #font_path = 'C:/Windows/Fonts/meiryo.ttc'
    font_path = 'meiryob.ttc'
    font = ImageFont.truetype( font_path, font_size )
    font_color = color
    #
    img_pil = Image.fromarray( imag )
    draw = ImageDraw.Draw( img_pil )
    _, y1, _, y2 = draw.textbbox( point, message, font )
    h = y2 - y1
    x, y = point
    draw.text( (x, y - h), message, font_color, font )
    return np.array( img_pil )            
#
#    射法八節姿勢解析評価点数のクラス定義
#
class MyEval:
    """
    :param result: 解析データ:Tensor
    :param boxid: 解析対象バウンダリーボックスのID:int 
    """
    def __init__(self):
        self.eval = { # 現在セクションの評価データ
                      'completed': 0,'score': 10 , 'split_tm': 0.0, \
                      'rl_angle' : 0.0, 'er_angle': 0.0, 'sl_angle': 0.0, \
                      'push_cnt' : 0, 'pull_cnt': 0, 'alart_cnt': 0 \
                      }              
        self.section: int = -1              # 現在のセクション（節） 番号(0-9)
        self.completed: int = 0             # 現在の完了状態(0/1)
        self.step: int = -1                 # ステップ番号
        self.evals: list = []               # 評価データリスト(9節分)
        self.alarts: list = []              # 警告リスト
        self.deduct_msgs: list = []         # 減点リスト
        self.score_on: bool = False         # 総合評価点数表示のON/OFF
        self.score_text: str = ""           # 総合評価点数表示用のテキスト
        self.csvpath: str = None            # 評価結果保存用のCSVファイルパス
        self.csvfd = None                   # 評価結果保存用のCSVファイルオブジェクト
        self.case_name: str = None          # 評価ケース名
        self.frame_no: int = -1             # フレーム番号
        self.lv_no: int = 0                 # レベル番号
        self.cycle: int = 0                 # セクションのサイクル
            
    # CSVファイルを開いてヘッダーを書き込む
    def open_csv(self,case_name: str, lv_no: int, path: str):
        self.case_name = case_name
        self.lv_no = lv_no
        self.csvpath = path.replace('track', 'eval')
        #print(f"[open_csv]: csvpath={self.csvpath}")
        self.csvfd = open(self.csvpath, 'w', newline='', encoding='utf-8')
        # CSVファイルにヘッダーを書き込む
        header = "case_name,lv,frame_no,section,completed,step,score,split,rl,er,sl,push,pull,alart,inserted_at,time_epoch\n"
        self.csvfd.write(header)
        self.csvfd.flush()
        
    # CSVファイルに評価データを書き込む
    def out_csv(self, score=None):
        if self.csvfd is None:
            return        
        d = datetime.now()
        timestamp = d.strftime('%Y-%m-%d %H:%M:%S')
        time_epoc = int(time.mktime(d.timetuple()))
        values = f"{self.case_name},{self.lv_no},{self.frame_no},{self.section+10*self.cycle},{self.completed},{self.step},"
                            
        for i, value in enumerate(self.eval.values()):
            if i == 0: continue               # completed
            elif i > 1 and i < 6:             # split, rl,er,sl
                values += f"{value:.3f},"
            elif i == 1:                      # score          
                values += f"{score if score is not None else value},"
            else:
                values += f"{value},"
            
        values += f"'{timestamp}',{time_epoc}"            
        self.csvfd.write(f"{values}\n")
        self.csvfd.flush()
        
    # 評価データの初期化
    def reset(self):
        self.section = -1               # 現在のセクション（節） 番号(0-9)
        self.completed = 0              # 現在の完了状態(0/1)
        self.step = -1                  # ステップ番号
        # 評価データの初期化
        self.eval = { 'completed': 0, 'score': 10, 'split_tm': 0, \
                      'rl_angle': 0.0, 'er_angle': 0.0, 'sl_angle': 0.0, \
                      'push_cnt': 0, 'pull_cnt': 0, 'alart_cnt': 0 \
                    }
        # 評価データリストの初期化    
        self.evals.clear()                                        
        for i in range(9): 
            self.evals.append(self.eval.copy())                 
        # 警告リストの初期化
        self.alarts.clear()  
        #self.deduct_msgs.clear()                                      
        print(f"[my_evaluate]: reset.")
        
    # 評価点数の減算条件をチェックして減点数を計算する    
    def check_deduction(self, section: int):
        deduction = 0

        if self.eval['alart_cnt'] > 0:
            # 警告の有無をチェックして減点する
            deduction += 10
            mylog.log(INFO, f"[my_evaluate]: section({section}) alart_cnt={self.eval['alart_cnt']}  deduction=10")            
        #
        # セクションごとの減点条件をチェックして減点数を計算する
        for key_nm, data in Diduct_params.items():  # key_nm: 's<section_no>_<key of check data>'
            sect_no = int(key_nm[1])                # セクション番号を取得（例: 's8_rl_angle' -> 8）
            key = key_nm[3:]                        # 評価データのキーを取得（例: 's8_rl_angle' -> 'rl_angle'）
            if sect_no == section:
                # セクションに対応する減点条件をチェックして減点する
                (ope, value, score), msg = data
                if ope == '<'   : bret = True if self.eval[key] < value else False
                elif ope == '>' : bret = True if self.eval[key] > value else False
                else: continue
                if bret == True: 
                    deduction += score
                    mess = msg.split('.')  # メッセージを'.'でリスト分割
                    self.deduct_msgs.append(f"{mess[0]}({self.eval[key]:.2f}{mess[1]})")
                    mylog.log(INFO, f"[my_evaluate]:section({section}) {key}={self.eval[key]:.2f} {ope} {value} deduction={score}")   
        #
        # その他のセクションの減点条件をチェックして減点数を計算する
        #
        return deduction
         
    # 評価結果の表示
    def print(self):
        if not self.score_on: 
            # セクションごとの評価点数の合計を計算
            score = 0
            score_str = ""
            for i in range(8): 
                score += self.evals[i]['score']
                score_str += f",{self.evals[i]['score']}"
            #
            score_str = score_str[1:]   # 先頭のカンマを削除                    
            self.score_text = f"total score:{score}({score_str}), alart:{len(self.alarts)}"
            print(f"[my_evaluate]: {self.score_text}, alarts={self.alarts}")
            mylog.log(INFO, f"[my_evaluate]: {self.score_text}, alarts={self.alarts}")
        return 
    #
    # 評価データの更新
    #
    def __call__(self, frame_no:int=-1,section:int=-1, completed:int=0, step:int=0, split:float=0, \
                       rl_angle:float=0.0, er_angle:float=0.0, sl_angle:float=0.0, alart:int=0):
        # 
        self.frame_no = frame_no
        
        if alart != 0:
            # 警告がある場合、警告カウントを増やして、警告リストに追加
            self.eval['alart_cnt'] += 1
            self.alarts.append(alart)
        if section != self.section:
            # セクションが変わった場合
            if (section == 0) or (section < self.section):
                if section != 0 : 
                    # セクションが0以外で前のセクションより小さい場合、
                    # 評価点数を表示してから初期化
                    if self.score_on is False: 
                        self.print()
                        self.score_on = True
                    self.cycle += 1
                # 評価データの初期化
                self.reset()

            elif self.section > 0:
                # 評価点数の減算
                deduction = self.check_deduction(self.section)  # 減点数の計算                
                self.eval['score'] -= deduction if deduction <= self.eval['score'] else 0                                            # その他の減点
                print(f"[my_evaluate]: section({self.section})  evaluated.(deduction={deduction})") 
                mylog.log(INFO, f"[my_evaluate]:section={self.section}  score={self.eval['score']}  alart={self.eval['alart_cnt']}"\
                                f"  split={self.eval['split_tm']:.2f}"\
                                f"  rl={self.eval['rl_angle']:.2f}  er={self.eval['er_angle']:.2f}  sl={self.eval['sl_angle']:.2f}"\
                                f"  push={self.eval['push_cnt']}    pull={self.eval['pull_cnt']}")
                if self.csvfd is not None:
                    self.out_csv()  # CSVファイルに評価データを書き込む
                              
                # 現在の評価データを保存
                self.evals[self.section - 1] = self.eval.copy()
                self.eval['score'] = 10         # スコアはセクションごとにリセット（10点満点）   
                self.eval['alart_cnt'] = 0      # 警告カウントはセクションごとにリセット   
                self.eval['push_cnt'] = 0
                self.eval['pull_cnt'] = 0
                
        elif completed != self.completed:
            # 完了状態が変わった場合
            if self.csvfd is not None:
                # 完了ステータスの変化でCSVファイルに評価データを書き込む
                self.out_csv(score=0)       
            if completed == 1:
                self.eval['completed'] = 1
                if section == 9:
                    self.print() 
                    self.score_on = True
                    self.reset()  # 9節完了で評価データを初期
                
        elif self.section > 0:
            if step != self.step and self.csvfd is not None: 
                # ステップの変化でCSVファイルに評価データ(score=0)を書き込む
                self.out_csv(score=0)
            # 評価データの設定
            self.eval['split_tm'] = split
            if completed == 0:
                # 移行中の角度データを更新
                self.eval['rl_angle'] = rl_angle
                self.eval['er_angle'] = er_angle
                self.eval['sl_angle'] = sl_angle
            # 5節のとき、引き分けの「押し」／「引き」回数をカウント
            if section == 5:
                if step == 11:      self.eval['push_cnt'] += 1
                elif step == 12:    self.eval['pull_cnt'] += 1
        # 
        if self.score_on: 
            # 評価点数の表示
            self.print()
        # 現在のステートに更新
        self.section = section
        self.completed = completed
        self.step = step
    
#
# 動作解析パラメータ取得関数
# action_param_tbls: 動作解析パラメータテーブルリスト
# param_nm: パラメータ名(frame)
# step_no: ステップ番号(step)
def get_action_param(action_param_tbls, param_nm, step_no):
    for tbl in action_param_tbls:
        if param_nm == tbl['frame'] and step_no == tbl['step']:
            return tbl['param'], tbl
    return None, None
#
# ベクトルの長さ、角度を計算する関数
#    vectの座標 [x, y]ndarray
def vector_length_angle(vect):
    return np.linalg.norm(vect), math.degrees(np.arctan2(vect[1], vect[0]))  # (長さ, 角度（ラジアン -> 角度）)
#
# 2点の座標が近いかどうかを判定する関数
#    p1, p2の座標 [x, y]ndarray
def near_points(p1, p2, threshold=10):
    ans = False
    '''
    :param p1: 点1の座標 [x, y]ndarray
    '''
    vect = p1 - p2  # 2点のベクトルを計算
    length, x = vector_length_angle(vect.numpy())  # ベクトルの長さと角度を計算
    if abs(length) < threshold:
        # ベクトルの長さが閾値以下の場合、近いと判断
        ans = True
    return ans

#
# CSVデータのインポート関数
# db: MyDbデータベースオブジェクト
# cmds: コマンドライン引数リスト
# case_name: ケース名   
# 戻り値: 成功=True, 失敗=False
#
def import_tracking_data(db:MyDb, cmds:list, case_name:str):
    if case_name == '' : 
        return False
    db.case_name = case_name 
    _, count = db.get_fps()
    csvfile = ''
    i = cmds.index('-import')
    if len(cmds) > (i + 1):
        # トラッキングCSVファイルの切り出し
        if not cmds[i+1].startswith('-'): csvfile = cmds[i+1]
    
    # コマンドラインで指定のない時はframe_infoテーブルから取得
    if csvfile == '':
        _, csvfile = db.get_file_path()
        if csvfile == '' :
            print(f"[import_tracking_data]error:No tracking data. you must import csv-file.")
            return (0,0,0)
    
    if csvfile == '' or os.path.isfile(csvfile) == False:
        # ファイルが存在しないとき終了
        print(f"[import_tracking_data]error: csv-file({csvfile}) not found.")
        return (0,0,0)
    # CSVファイルを読み込む
    df = pd.read_csv(csvfile)
    print(f"[import_tracking_data]:read_csv:{df.shape}, case_name:{df['case_name'][0]}")
    if df['case_name'][0] != case_name:
        print(f"[import_tracking_data]:case_name:{df['case_name'][0]} changed to '{case_name}'")
        df['case_name'] = case_name
    
    # DBへトラッキングデータ登録
    db.delete_tracking_data()      # 登録済データの削除
    df.to_sql('tracking_data', db.conn, if_exists='append', index=None, method='multi', chunksize=1024)
    print(f"[import_tracking_data]info:import '{csvfile}' to 'tracking_data'{df.shape}.")
    count_t = df.shape[0]
    # インポート実行回数更新
    count += 1
    db.update_frame_info('import', count)
    
    # 姿勢解析データをkyudo_dataテーブルへ登録
    csvfile = csvfile.replace('track','kyudo')
    if csvfile == '' or os.path.isfile(csvfile) == False:
        # ファイルが存在しないとき終了
        print(f"[import_kyudo_data]error: csv-file({csvfile}) not found.")
        return (count_t,0,0)    
    # CSVファイルを読み込む
    df = pd.read_csv(csvfile)
    print(f"[import_kyudo_data]:read_csv:{df.shape}, case_name:{df['case_name'][0]}")
    if df['case_name'][0] != case_name:
        print(f"[import_kyudo_data]:case_name:{df['case_name'][0]} changed to '{case_name}'")
        df['case_name'] = case_name
    
    db.delete_kyudo_data()         # 登録済データの削除
    df.to_sql('kyudo_data', db.conn, if_exists='append', index=None, method='multi', chunksize=1024)
    print(f"[import_kyudo_data]info:import '{csvfile}' to 'kyudo_data'{df.shape}.")
    count_k = df.shape[0]
    
    # 評価データをeval_dataテーブルへ登録
    csvfile = csvfile.replace('kyudo','eval')
    if csvfile == '' or os.path.isfile(csvfile) == False:
        # ファイルが存在しないとき終了
        print(f"[import_eval_data]error: csv-file({csvfile}) not found.")
        return (count_t, count_k, 0)
    # CSVファイルを読み込む
    df = pd.read_csv(csvfile)
    print(f"[import_eval_data]:read_csv:{df.shape}, case_name:{df['case_name'][0]}")
    if df['case_name'][0] != case_name:
        print(f"[import_eval_data]:case_name:{df['case_name'][0]} changed to '{case_name}'")
        df['case_name'] = case_name
    
    db.delete_eval_data()         # 登録済データの削除
    df.to_sql('eval_data', db.conn, if_exists='append', index=None, method='multi', chunksize=1024)
    print(f"[import_eval_data]info:import '{csvfile}' to 'eval_data'{df.shape}.")
    return (count_t, count_k, df.shape[0])
#
# 登録ケースの削除関数
# db: MyDbデータベースオブジェクト
# case_name: 削除ケース名 
def delete_frame_info(db:MyDb, case_name):
    _,csvfile = db.get_file_path(case_name)
    if csvfile is not None:
        if db.delete_case(case_name) == True:
            print(f"[delete_frame_info]:info: case_name='{case_name}' deleted.")
            rcnt = db.delete_case_records('tracking_data', case_name)
            print(f"[delete_frame_info]:info: {rcnt} records deleted from tracking_data.")
            rcnt = db.delete_case_records('kyudo_data', case_name)
            print(f"[delete_frame_info]:info: {rcnt} records deleted from kyudo_data.")
        #
        print(f"> '{csvfile}' will be deleted. continue?. [y/n].")
        ans = input('>>')
        if ans == 'y': 
            try:
                os.remove( csvfile )
                print(f"[delete_frame_info]:info: '{csvfile}' deleted.")
                csvfile = csvfile.replace('track', 'kyudo')
                os.remove( csvfile )
                print(f"[delete_frame_info]:info: '{csvfile}' deleted.")
            except:
                print(f"[delete_frame_info]:info: '{csvfile}' not found.")
    
    else:
        print(f"[delete_frame_info]:error: case_name='{case_name}' not found.")
    return            
#
# 登録ケース名の変更関数
# db: MyDbデータベースオブジェクト
# from_name: 変更前ケース名 
# to_name: 変更後ケース名
def rename_frame_info(db:MyDb, from_name, to_name):
    fps,_ = db.get_fps(from_name)
    if fps is None:
        print(f"[rename_frame_info]:error: case_name='{from_name}' not found.")
    else:
        tables = [ 'tracking_data', 'kyudo_data' , 'frame_info' ]
        for tbl in tables:
            rcnt = db.copy_case(tbl, from_name, to_name)
            if rcnt is None:
                # コピー対象ケース名が存在しないとき
                continue
            if rcnt < 0:
                # コピー件数不一致エラーのとき
                db.delete_case_records(tbl, to_name)    # 変更後ケース名の登録データを削除
                continue
            #
            i = db.delete_case_records(tbl, from_name)      # 変更前ケース名の登録データを削除
            #print(f"[rename_frame_info]:info: {tbl}:{rcnt} records  deleted. {from_name}.")
            print(f"[rename_frame_info]:info: {tbl}:{rcnt} records  renamed from {from_name} to {to_name}.")
        #
    return None            
#
def print_eval_data(db:MyDb, case_names:list):
    
    eval_sections = [ 5, 6, 8]
    headers = [
                " <section>  <case>        <pull(%)>  <sl(°)>   <rl(°)>",
                " <section>  <case>      <split(sec.)> <sl(°)>  <rl(°)>",
                " <section>  <case>      <split(sec.)> <sl(°)>  <rl(°)>"
            ]

    if case_names[0] == '*':
        case_names.clear()
        # 全ケース名を取得してリストに格納する
        fdf = db.pandas_read_frame()
        rows,_ = fdf.shape
        for i in range(rows):
            case_names.append(fdf.iloc[i]['case_name'])
    
    for i, section in enumerate(eval_sections):
        print(f"\n{headers[i]}")
        for case_name in case_names:
            eval_data_l = db.get_print_eval_data(section, case_name)
            for line in eval_data_l:
                print(f"{line}")
#eof
