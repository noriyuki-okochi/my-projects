import cv2
from ultralytics import YOLO
import ultralytics

import tkinter.filedialog as filedialog
import sys
import os
import time
from datetime import datetime
from copy import copy 
from PIL import Image, ImageFont, ImageDraw
import numpy as np
import pandas as pd
import copy

# local package
from kyudo.env import * 
from kyudo.param import * 
from kyudo.appUtil import * 
from kyudo.kyudoModel import * 
from kyudo.kyudoUtils import *
from mysqlite3.mysqlite3 import MyDb

# Ultralytics YOLOv8とアプリ専用のロガー設定
import logging
DEBUG = logging.DEBUG
INFO = logging.INFO
ERROR = logging.ERROR

logger = logging.getLogger('ultralytics')
logger.disabled = True  # ログ出力を無効化

mylog = logging.getLogger(__name__)
filehandler = logging.FileHandler('yoloApp.log', mode='w')  # ログファイルの設定
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # ログフォーマットの設定
formatter = logging.Formatter('%(message)s')  # ログフォーマットの設定
filehandler.setFormatter(formatter)  # フォーマッタをハンドラに設定
mylog.addHandler(filehandler)  # ログハンドラを追加

#　アプリケーションのグローバル変数の定義
Debug_opt:int = 0           # デバッグレベル
Frame_counter:int = 0       # フレームカウンター
Fps:float = 30              # フレームレート
Section_no:int = 0          # セクション番号
Split_sec:float = 0.0       # スプリット秒
Split_start:int = 0         # スプリットベースフレームカウント
Lap_sec:float = 0.0         # ラップ秒 
Lap_start:int = 0           # ラップベースフレームカウント
Action_start:float = 0.0    # アクションベース時間
Action:int = 0              # アクション（予測結果）
Completed:bool = False      # 完了フラグ
Step_counter:int = 0        # セクション内のステップカウンター
Nop_counter:int = 0         # スキップカウンター
Step_error:bool = False     # 不正な動作フラグ
Alart_section:int = 0       # アラート発生セクション番号
Alart_id:int = 0            # アラート番号
Alart_message:str = ''      # アラートメッセージ
Section_color:list = YELLOW # セクションの色（黄色）BGR
RL_angle:float = 0.0        # 右手首ー＞左手首の角度
SL_angle:float = 0.0        # 左腕の角度
ER_angle:float = 0.0        # 右肘ー＞右手首の角度

# カメラの位置を定義
Camera_position:int = 0     # カメラの位置（0:未定義、1:前面、2:右側面、3:上面）
CameraPos:str = ''          # カメラの位置名
CameraPos_name = ['', 'Front-side', 'Right-side', 'Upper-side']  # カメラの位置

# トラッキングフラグ
Tracking_only:bool = False      # トラッキングフラグ
Tracking_enabled:bool = False   # トラッキングオン
Tracking_onece:bool = False     # トラッキング開始済
Update_tracking:bool = False    # DBのトラッキングデータ(section,completed)更新
Update_enabled:bool = False     # DBのトラッキングデータ更新オン
# データベースのインスタンスを作成
Db = MyDb(DB_PATH)  
Db.mode = 'csv'                 # 解析結果のトラッキングデータをCSVファイルに出力する
# GRUモデル
Input_key:int = Current_feature_key  # 使用する特徴量の個数(6,7,8)
Num_input:int = Input_dim       # 入力データ次元数
Num_frames = Sequence_frames    # 入力シーケンスのフレーム数
Num_classes:int = Output_dim    # 出力クラス数（ラベル[0=移行,1=完了,2=開始]の区分数）
Hybrid_model:bool = False       # GRUモデルとロジック解析の併用フラグ
# YOLOv8モデル
V8_model:str = 'v8s'            # YOLOv8のモデルファイル名
# ビデオ出力設定
Cv2Video = None                 # OpenCVのビデオライターインスタンス
#
# YOLOv8とOpenPoseの組み合わせ例（Ultralytics YOLOv8 + YOLOv8-poseモデル利用）
# このコードは、YOLOv8を使用してカメラまたは動画ファイルから骨格検出を行うものです。
# YOLOv8-poseモデルは、Ultralyticsの事前学習済みモデルを使用しています。
def help():
    print(" --- command ---")
    print(" python ./src/yoloApp.py [<Camera-ID>]|[-a] [-clip]|[-multi]|[-r]|[-m|[-t|-u] <case_name>\n"\
        + "                         [-gru <model-path> [inputkey=6|7|8]] [classes=3|19]]\n"\
        + "                         [-f'<frame_count>[.<lag>]'] [-W<window_size>] [-V8{s|n}] [-w] [-z]\n"\
        + "                         [{-{p|P}'(<section-no>,<index>)=<value>'}...] [{-S(<section-no>}...] [-s<step-no>]\n"\
        + "                         [-I ['<frame_name>']] [-h] [-g[<level>[<color>]]] [-v] [-d<debug-level>] [--]")
    print(" --- Option ---")
    print(" -a(ll-video-file)")
    print(" -m(anual-plot::dont use YOLO plot)")
    print(" -gru(:analize with NN-model)")
    print(" -r(aw-video)")
    print(" -clip(raw-video)")
    print(" -multi(video-layer display)")
    print(" -t(racking::create-csvfile)")
    print(" -u(pdate tracking_data in table)")
    print(" -f(rame-count) and lag for sampling data: default=1.7")
    print(" -W(window-size::ring-buffer-size: default=8)")
    print(" -V(8-pose model-file):default=v8s")
    print(" -w(rite-video-file)")
    print(" -z(:hide the faces by mosaic)")
    print(" -p(arameter set in StartAction_parames)")
    print(" -P(arameter set in CompletedAction_parames)")
    print(" -S(kip illegal-action-check")
    print(" -s(kill):skill-level default=1")
    print(" -I(nitial entry to act_table from Actin_params::<frame_name><step-no>')")
    print(" -h(elp)")
    print(" -g(uidance)<level><color>::[0|1|2|3]:0=dont display(default=3):[Y|G|B|W]: yellow, green, black, white")
    print(" -v(erborse)")
    print(" -d(ebug-level)<0-3>: 0:none, 1:info, 2:debug, 3:more-debug")
    print(" --(auto-pouse imidiately after start)")
    print(" --- Key Operation ---")
    print(" s :スナップショットファイルの作成")
    print(" w :出力ファイルへの書き込み開始／停止")
    print(" t :トラッキング開始／停止（姿勢解析開始後、有効）")
    print(" u :トラキングデータのDB更新")
    print(" b :トラッキング動作完了のタグ更新（'-u'時、有効）")
    print(" n :トラッキング動作開始（節移行）のタグ更新（'-u'時、有効）")
    print(" a :ログファイルへのアテンションメッセージ出力")
    print(" I :アクティブな動作解析パラメータのDB登録（'-m'時、有効）")
    print(" f :パラメータ（実数値）入力開始：(0-9.)[,(0-9.)]...:'m'キー押下で終了")
    print(" m :アクティブな動作解析パラメータの更新（'-m'時、有効）更新データ値は数値入力キー’i’で指定")
    print(" i :整数値入力開始:(0-9)...:タイマーで終了")
    print(" j :指定フレームへジャンプ（ジャンプ先フレームは数値入力キー’i’で指定：：(<フレームカウント>)）")
    print(" r :繰り返し再生開始／停止（'-r'時のみ有効）,’i’キー押下後のとき、停止中は開始、開始中は停止フレームを設定")
    print(" R :繰り返し再生開始フレームに戻る")
    print(" g :グリッド表示・非表示（分割数は数値入力キー’i’で指定：：(0|1)(<分割数>)）,'-r'時不可")
    print(" G :グリッド表示シフト（シフト量は数値入力キー’i’で指定：：(0|1)(グリッド幅の割合<分子><分母>)）")
    print(" 0 :姿勢解析開始")
    print(" 1-8:節の開始")
    print(" k(K) :再生速度アップ")
    print(" l(L) :再生速度ダウン")
    print(" p :一時停止／再開")
    print(" .(>):スキップ")
    print(" ,(<):巻き戻し")
    print(" c :警告メッセージ、その他、キー設定値のクリア")
    print(" ? :キー操作制御パラメータの表示")
    print(" q :処理の終了")
    '''
    print(" --- example ---")
    print("例)カメラID 1 を指定             : python yoloApp.py 1")  
    print("例)当日作成の動画ファイルから選択 : python yoloApp.py")  
    print("例)YOLOのplot機能で解析結果を描画: python yoloApp.py")  
    print("例)全ての動画ファイルタイプから選択: python yoloApp.py -a")  
    print("例)選択した動画ファイルをRAWモードで再生: python yoloApp.py -a -r")  
    print("例)ローカルのplot機能で解析結果を描画: python yoloApp.py -a -m")  
    '''
    return
#
# 動作解析パラメータ設定用のスタック   
Stkp = StackActParam()  
#
# 動作解析パラメータテーブルをログファイルに出力する
def print_param(tbl):
    mylog.log(INFO, f"frame:{tbl['frame']}, step = {tbl['step']}, act = {tbl['act']}")
    for sect, raw_vals in enumerate(tbl['param']):
        mylog.log(INFO, f"({sect:2d}): {raw_vals}") 
#
#    検出結果から最前面のボックスを取得する関数
def get_max_box(result):
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
#
# カメラの位置を取得する関数
def get_camera_pos(myResult):
    global Camera_position
    """
    :param result: YOLOv8の検出結果
    :param ibox: ボックスのインデックス
    :return: カメラの位置（’’）
    """
    keyPoints = myResult                        # キーポイントのデータ解析インスタンス
    thsd = Threshold(keyPoints.block_height)    # バウンディングボックスの高さを基準に閾値設定インスタンス

    length, angle = keyPoints.norm('right_shoulder', 'left_shoulder')       # 右肩と左肩のベクトルの長さと角度を計算
    l_conf = keyPoints.conf('left_shoulder')
    length_h, _ = keyPoints.norm('right_hip', 'left_hip')                   # 右腰と左腰のベクトルの長さと角度を計算

    ipos = 0
#    if length < thsd(0.120) and l_conf < 0.96:  # 右肩と左肩のベクトルの長さが100未満の場合
    if length < thsd(0.120) and length_h < thsd(0.08):  # 右肩と左肩のベクトルの長さが100未満の場合
        ipos = 2    # Right-side
    elif angle > -45 and angle < 45 :  # 
        ipos = 1    # Front
    else:  # 
        ipos = 3    # Upper    
    
    if ipos != Camera_position:
        # カメラの位置が変更された場合、ログに記録
        mylog.log(INFO,  f"[get_camera_pos]: conf-R={keyPoints.conf('right_shoulder'):.3f}, conf-L={l_conf:.3f},"\
                       + f" length-S={length:.2f}({thsd.ratio(length):.3f}), angle-S={angle:.2f}°, length-H={length_h:.2f}({thsd.ratio(length_h):.3f})")
        mylog.log(INFO, f"[get_camera_pos]: [ length-S < {thsd(0.120):.3f} and length-H < {thsd(0.08):.3f} ]")
        mylog.log(INFO, f"[get_camera_pos]: Camera_position={ipos}({CameraPos_name[ipos]})")

        Camera_position = ipos
    return CameraPos_name[ipos]
#
#
#    キーポイントのデータ解析をする関数
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
# 例外クラス
class BoundaryBoxError(Exception):
    pass
# キーポイント解析クラスの拡張クラス定義
class MyResult(Keypoint):
    MaxBox_id:int = None
    XYWH:int = [None, None, None, None]
    Skip:bool = False
    # 補正対象のキーポイントの信頼度閾値テーブル
    # --'nose', 
    #   'left_eye',             'right_eye',                'left_ear',             'right_ear', 
    #   'left_shoulder',        'right_shoulder',           'left_elbow',           'right_elbow', 
    #   'left_wrist',           'right_wrist',              'left_hip',             'right_hip',
    #   'left_knee',            'right_knee',               'left_ankle',           'right_ankle'--
    Limit_val = [ {'valid':0, 'limit':0.0}, 
        {'valid':0, 'limit':0.0}, {'valid':0, 'limit':0.0}, {'valid':0, 'limit':0.0}, {'valid':0, 'limit':0.0}, 
        {'valid':0, 'limit':0.0}, {'valid':0, 'limit':0.0}, {'valid':0, 'limit':0.85}, {'valid':0, 'limit':0.0}, 
        {'valid':0, 'limit':0.85}, {'valid':0, 'limit':0.92},{'valid':0, 'limit':0.0}, {'valid':0, 'limit':0.0},
        {'valid':0, 'limit':0.0}, {'valid':0, 'limit':0.0}, {'valid':0, 'limit':0.0}, {'valid':0, 'limit':0.0}]
    
    def __init__(self, result, boxid=None):
        if boxid is None:
            # 検出結果から最大（対象）のボックスを取得
            boxno = get_max_box(result)
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
            mylog.log(INFO, f"[MyResult]:フレーム={Frame_counter}, "\
                        + f" MaxBox_id changed.[{MyResult.MaxBox_id} -> {boxid}], xywh={self.xywh}") 
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
        self.arrow_length_angles = [None] * Window_size
             
    #　指定キーポイントの移動ベクトルの長さ（加重平均値）と角度をタプルで返す
    def tuple_ave_angle(self, idx):
        _, angle = self.arrow_length_angles[0][idx]         # idxの移動ベクトルの長さと角度を取得
        return self.arrow_moving_ave[idx], angle            # 移動ベクトルの長さ（加重平均値）と角度を返す
    
    # 信頼度の低いキーポイントの座標を直前の値で置き換える    
    def adjust_points(self, prePoints):
        for key, idx in Kn2idx.items():
            # 有効なデータが出現したかどうかを判定
            if self.confs[idx] > MyResult.Limit_val[idx]['limit']:  MyResult.Limit_val[idx]['valid'] = 1
                
            if self.Limit_val[idx]['valid'] == 1 and self.confs[idx] < MyResult.Limit_val[idx]['limit']:
                self.points[idx] = prePoints[idx]           
                mylog.log(INFO, f"[adjust_points]:フレーム={Frame_counter}, Key={key},"\
                              + f" conf={self.confs[idx]:.3f}({MyResult.Limit_val[idx]['limit']:.3f})")
     
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
    Features_list_6 = [ 'rw_ratio', 'rl_ratio', 'eyes_ratio',\
                        'hr_ratio',\
                        'section','completed' ]
    Kyudo_index_6   = { 4:'h', 8:'h', 20:'w',\
                        10:'h'}

    Features_list_7 = [ 'rw_ratio', 'lw_ratio', 'eyes_ratio',\
                        'hr_ratio', 'hr_deg',\
                        'section','completed' ]
    Kyudo_index_7   = { 4:'h', 6:'h', 20:'w',\
                        10:'h', 11:'d'}

    Features_list_8 = [ 'rw_ratio', 'rl_ratio', 'hr_ratio',\
                        'eyes_ratio', 'sr_deg', 'se_deg',\
                        'section','completed' ]
    Kyudo_index_8   = { 4:'h', 8:'h', 10:'h',\
                        20:'w', 13:'d', 17:'d' }
    
    Features_index = { 6: (Features_list_6, Kyudo_index_6),
                       7: (Features_list_7, Kyudo_index_7), 
                       8: (Features_list_8, Kyudo_index_8) }
    
    def __init__(self, input_key:int=Input_key, seq_frames:int=Num_frames):
        self.seq_size = seq_frames
        self.kyudo_data_list = [None]*len(Kyudo_data_names)
        self.curPdf:pd.DataFrame = None
        self.prePdf:pd.DataFrame = None
        
        self.input_key = input_key                          # 6 or 7 or 8
        features, _ = FeaturePdf.Features_index[input_key]
        self.input_dim = len(features)                      # 入力データ次元数
        self.features_list = [None]*self.input_dim          # 特徴量リスト
    
    def set_kyudo_data_list(self, data_list):
        self.kyudo_data_list = data_list
        
    def get_kyudo_data_list(self):
        return self.kyudo_data_list

    def set_current_pdf(self, section_no, completed):
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
            elif c == 'd': # degreeで正規化
                self.features_list[i] = self.kyudo_data_list[idx]/180.0
            i += 1
        #
        self.features_list[i] = section_no                          # section
        i += 1
        self.features_list[i] = completed                           # completed   
        
        narray = np.array(self.features_list).reshape(1, -1)
        self.curPdf = pd.DataFrame(narray, columns=column_names)

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

# ハイブリッドモデルの場合、動作予測結果を補正
def correct_action_by_rules(action, section, completed):
    global Step_counter
    r_action = action
    if completed == True and action == 1:
        # 「動作完了」で「動作完了」が認識された場合、
        r_action = 0
    elif completed == False and action == 2:
        # 「動作未完了」で「動作開始」が認識された場合、
        r_action = 0
    else:
        # 動作解析ステップに応じた補正ルール
        if section == 2:        # 「胴づくり」
            if action == 1 and Step_counter < 20:   # 動作完了が早すぎる（一回目の腰）
                r_action = 0
    #
    if r_action != action:
        mylog.log(INFO, f"[correct_action_by_rules]: action corrected {action} to {r_action}")
    return r_action
            
#
# GRUモデルによる動作予測関数
def gru_analize(section, completed, model, input_pdf:pd.DataFrame):
    global Split_start, Split_sec, Lap_start, Action_start, Step_counter
    
    mylog.log(DEBUG, f"[gru_analize]: input_pdf.shape={input_pdf.shape}")
    mylog.log(DEBUG, f"[gru_analize]: {input_pdf.tail()}")
    
    x = input_pdf.to_numpy(dtype=np.float32)
    s_frames = len(input_pdf)
    
    # GRUモデルによる動作解析
    y = predict_Kyudo( model, x, s_frames)
    mylog.log(DEBUG, f"[gru_analize]: y.shape={y.shape}")
    action = y[0]
    if action != 0 and Hybrid_model == True:
        mylog.log(INFO, f"[gru_analize]: not zero action={action}, section={section}, completed={completed}, counter={Step_counter}")
        # ハイブリッドモデルの場合、動作認識結果を補正
        action = correct_action_by_rules(action, section, completed)
    # タイマー情報の更新
    if action == 2:
        Action_start = Lap_sec
        Split_start = Frame_counter                         # スプリット開始時間を記録
        Split_sec = 0.0
    elif action == 1:
        Action_start = Lap_sec
        if section != 6 and section != 8:                   # 「会」、「残身」はスプリットを計測
            Split_start = 0                                 # スプリット開始時間をリセット
        if section == 9:                                    # 退場動作の場合、解析終了 
            Lap_start = 0
    #
    ival = 1 if completed == True else 0
    rslt = update_section_completed(action, section, ival, output_size=Num_classes)
    if action != 0:
        mylog.log(INFO, f"[gru_analize]: フレーム={Frame_counter}")
        if action == 1:
            mylog.log(INFO, f"[gru_analize]: section({section}), completed=True")
            print(f"[gru_analize]: section({section}), completed=True")
        else:
            mylog.log(INFO, f"[gru_analize]: section({section}), strated=True")
            print(f"[gru_analize]: section({section}), strated=True")
        mylog.log(INFO, f"[gru_analize]: section={rslt[0]}, completed={rslt[1]}")
        #
        if section == 9 and action == 2: Step_counter = 30
        else: Step_counter = 0
    #
    return rslt[0], (True if rslt[1] == 1 else False), action
#
# 解析結果をトラッキングする関数              
def tracking_result( myResult:MyResult ,inputPdf:FeaturePdf, output_dim, csvout=True):
    boxes = myResult.boxes                              # バウンダリーボックスリスト(Tensor)
    box_id = myResult.boxid
    
    # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
    arrow = myResult.arrow_length_angles[Sample_lag]  
    
    box_h = boxes.xywh[box_id][3].item()                # 解析対象のボックスの高さ
    box_w = boxes.xywh[box_id][2].item()                # 解析対象のボックスの幅
    box_conf = boxes.conf[box_id].item()                # 解析対象の信頼度

    keyPoints = myResult                                # キーポイントのデータ解析インスタンス    
    if csvout == True:
        # トラッキングデータ
        for name, idx in Kn2idx.items():
            key_id = idx
            if idx > 12: continue
            
            key_name = name
            x = keyPoints.points[idx][0]                    # キーポイントX座標(Numpy)
            y = keyPoints.points[idx][1]                    # キーポイントY座標(Numpy)
            xy_conf = keyPoints.confs[idx]                  # キーポイントの信頼度(Numpy)
            norm, angle = arrow[idx]                        # 移動ベクトルの長さと角度
            ratio = norm/box_h                              # ボックスの高さに対する比率
                    
            data_list = [key_id, key_name, box_id, box_w, box_h, x, y, xy_conf, norm, ratio, angle]            
            # CSVファイルに書き込み
            Db.outcsv_tracking_data( data_list )        
            Db.csvfile1.flush()

        # 姿勢解析データ
        data_list = inputPdf.get_kyudo_data_list()
        # CSVファイルに書き込み
        Db.outcsv_kyudo_data( data_list, output_dim )  
        Db.csvfile2.flush()
    else:    
        # 姿勢解析データ
        rw_norm, rw_angle = arrow[Kn2idx['right_wrist']]                    # 右手首移動ベクトルの長さと角度
        lw_norm, lw_angle = arrow[Kn2idx['left_wrist']]                     # 左手首移動ベクトルの長さと角度
        rl_norm, rl_angle = keyPoints.norm('right_wrist','left_wrist')      # 右手首から左手首のベクトルの長さと角度を計算
        hr_norm, hr_angle = keyPoints.norm('right_hip','right_wrist')       # 右腰から右手首のベクトルの長さと角度を計算
        sr_norm, sr_angle = keyPoints.norm('right_shoulder','right_wrist')  # 右肩から右手首ベクトルの長さと角度を計算
        sl_norm, sl_angle = keyPoints.norm('left_shoulder','left_wrist')    # 左肩から左手首ベクトルの長さと角度を計算
        _, rew_angle = keyPoints.norm('right_elbow','right_wrist')          # 右肘から右手首のベクトルの長さと角度を計算
        _, lew_angle = keyPoints.norm('left_elbow','left_wrist')            # 左肘から左手首のベクトルの長さと角度を計算
        _, rse_angle = keyPoints.norm('right_shoulder','right_elbow')       # 右肩から右肘のベクトルの長さと角度を計算
        _, lse_angle = keyPoints.norm('left_shoulder','left_elbow')         # 左肩から左肘のベクトルの長さと角度を計算
        eyes_norm, _ = keyPoints.norm('right_eye','left_eye')               # 右目から左目のベクトルの長さと角度を計算
        hips_norm, _ = keyPoints.norm('right_hip','left_hip')               # 右腰から左腰のベクトルの長さと角度を計算        
        # アクション発生後の経過時間（x10秒）
        act_sec = int( (Lap_sec - Action_start)*10 ) if Action_start > 0.0 else 0
        #print(f"act_sec={act_sec}")                   
        
        data_list = [box_id, box_conf, box_w, box_h,\
                    rw_norm, rw_angle,\
                    lw_norm, lw_angle,\
                    rl_norm, rl_angle,\
                    hr_norm, hr_angle,\
                    sr_norm, sr_angle,\
                    sl_norm, sl_angle,\
                    rew_angle, rse_angle,\
                    lew_angle, lse_angle,\
                    eyes_norm, hips_norm,\
                    act_sec]
        # データリストをセット
        inputPdf.set_kyudo_data_list( data_list )  
    
    return
#
# 次のセクションが開始したかどうかを判定する関数
#
def section_started(section_no, myResult:MyResult):
    global Step_counter, Step_error, Alart_id
    
    keyPoints = myResult                            # キーポイントのデータ解析インスタンス
    ibox = myResult.boxid
    
    thsd = Threshold(keyPoints.block_height)        # バウンディングボックスの高さを基準に閾値設定インスタンス
    
    # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
    arrow = myResult.arrow_length_angles[Sample_lag]

    normR, anglR = arrow[Kn2idx['right_wrist']]                     # 右手首の移動ベクトルの長さと角度
    normL, anglL = arrow[Kn2idx['left_wrist']]                      # 左手首の移動ベクトルの長さと角度
    normS, _ = arrow[Kn2idx['right_shoulder']]                      # 右肩の移動ベクトルの長さと角度
    xy_wristR = keyPoints.xy('right_wrist')                         # 右手首の座標
    _, RL_angle = keyPoints.norm('right_wrist', 'left_wrist')       # 右手首から左手首へのベクトルの長さと角度を計算
    
    started = False
    # 共通の開始条件を取得
    PRM = StartAction_param['param'][10]        # 10は共通の開始条件     
    conf = keyPoints.conf('right_wrist')                            # 右手首の座標の信頼度
    
    if conf < PRM[0] and (section_no > 0 and section_no < 8):
        # 右手首の信頼度が低い
        mylog.log(INFO, f"started({section_no}): right-wrist-conf={conf:.2f}({PRM[0]:.2f}), "\
                      + f" skip....")
        return started

    mylog.log(INFO, f"started ({section_no}):フレーム={Frame_counter}\n"\
            + f"    boxid={ibox}, H={int(thsd.block_height)}:  wristR=[{int(xy_wristR[0])}, {int(xy_wristR[1])}],"\
            + f"    normR={int(normR)}({thsd.ratio(normR):.3f}), anglRL={int(RL_angle)}°, conf={conf:.2f}, counter={Step_counter}")
    #
    # 次の節への移行条件を判定
    #
    # セクションごとの開始条件を取得
    PRM = StartAction_param['param'][section_no]  
    # 0-Start  ->  1-Asi-bumi
    if section_no == 0:    
        lenS, _ = keyPoints.norm('left_shoulder', 'right_shoulder')          # 右肩と左肩のベクトルの長さと角度を計算
        mylog.log(INFO, f">>>   lenS={int(lenS)}({thsd.ratio(lenS):.3f}), normS={(int(normS))}({thsd.ratio(normS):.3f})")
        mylog.log(INFO, f">>>   [ lenS < {int(thsd(PRM[0]))} and normS > {int(thsd(PRM[1]))} ]")

        Stkp.push([ (0,PRM[0]), (1,PRM[1]) ])  
        if lenS < thsd(PRM[0]) and  normS > thsd(PRM[1]):
            # 右肩と左肩のベクトルの長さが80未満、右肩の移動ベクトルの長さが50以上の場合（射位へ移動）
            started = True
    
    # 1-Asi-bumi  ->  2-Dou-zukuri        
    elif section_no == 1:  
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} ]")

        Stkp.push( [(0,PRM[0])] )  
        if normR > thsd(PRM[0]):
            # 右手首の移動ベクトルの長さが50以上の場合（矢つがえ動作開始）
            Step_counter += 1
            if Step_counter == PRM[1]: started = True
    
    # 2-Dou-zukuri  ->  3-Yu-gamae        
    elif section_no == 2:  
        lenY, _ = keyPoints.norm('right_eye', 'left_eye')         # 右目と左目のベクトルの長さと角度を計算       
        mylog.log(INFO, f">>>   lenY={int(lenY)}({thsd.ratio(lenY):.3f})")
        mylog.log(INFO, f">>>   [ lenY > {int(thsd(PRM[0]))} and normR > {int(thsd(PRM[1]))} ]")

        if Step_counter == 0: Step_counter = 40 # 初期化（弦調べ）
        Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
        if lenY > thsd(PRM[0]) and normR > thsd(PRM[1]):
            # 右手首の移動ベクトルの長さが10以上の場合（取りかけ動作開始）
            Step_counter += 1
            Stkp.push( [(2,PRM[2])] )  
            if (Step_counter%10) == PRM[2]: started = True
        else: Step_counter = 40
    
    # 3-Yu-gamae  ->  4-Uti-okosshi        
    elif section_no == 3:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} and normL > {int(thsd(PRM[1]))} ]")

        if Step_counter == 0: Step_counter = 11 # 初期化（物見が定まる）
        Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
        if normR > thsd(PRM[0]) and normL > thsd(PRM[1]):
            # 右手首と左手首の移動ベクトルの長さが10以上の場合（打起し動作開始）
            Step_counter += 1
            Stkp.push( [(2,PRM[2])] )  
            if (Step_counter%10) == PRM[2]:   started = True
    
    # 4-Uti-okosshi  ->  5-Hiki-wake        
    elif section_no == 4:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), anglL={int(anglL)}°, anglR={int(anglR)}°")
        mylog.log(INFO, f">>>   [ (normR > {int(thsd(PRM[0]))} and anglR > {PRM[2]:.2f} and anglR < {PRM[3]:.2f})"\
                      + f" or (normL > {int(thsd(PRM[1]))} and anglL > {PRM[2]:.2f} and anglL < {PRM[3]:.2f}) ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3])] )  
        if  (normR > thsd(PRM[0]) and anglR > PRM[2] and anglR < PRM[3]) or \
            (normL > thsd(PRM[1]) and anglL > PRM[2] and anglL < PRM[3]):
            # 右手首の移動ベクトルの長さが15以上の場合（引分け大三への動作開始）
            Step_counter += 1
            Stkp.push( [(4,PRM[4])] )  
            if Step_counter == PRM[4]:   started = True
    
    # 5-Hiki-wake  ->  6-Kai        
    elif section_no == 5:  
        normER, _ = arrow[Kn2idx['right_elbow']]                    # 右肘の移動ベクトルの長さと角度
        normEL, _ = arrow[Kn2idx['left_elbow']]                     # 左肘の移動ベクトルの長さと角度
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                        + f" normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ (normR < {int(thsd(PRM[0]))} and normL < {int(thsd(PRM[1]))}) and (normER < {int(thsd(PRM[2]))} and normEL < {int(thsd(PRM[3]))}) ]")

        if Step_counter > 90 :  # 離れアラート設定（仮）
            _, angER = keyPoints.norm('right_elbow', 'right_wrist')     # 右肘から右手首へのベクトルの角度を計算
            mylog.log(INFO, f">>>   angER={angER:.1f}°")
            if angER > 145 or angER < -145: 
                # 右肘の角度が伸展している場合（会なしで離れ）
                Alart_id = Alart_KaiNasi
                Step_error = True
            else: Step_counter = Step_counter%10
        else:    
            Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3])] )  
            if (normR < thsd(PRM[0]) and normL < thsd(PRM[1])) and (normER < thsd(PRM[2]) and normEL < thsd(PRM[3])) :
                # 右手首の移動ベクトルの長さが10以下の場合（引分けの完了）
                Step_counter = Step_counter + 1
                Stkp.push( [(4,PRM[4])] )  
                if Step_counter == PRM[4]: started = True    #  停止状態の５回保持で完了
            else:
                mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[5]))} ]")
                Stkp.push( [(5,PRM[5])] )  
                if normR > thsd(PRM[5]):
                    # 右手首の移動ベクトルの長さが大きい（会なしで離れ）
                    Step_counter += 90              # 離れアラート設定（仮）
    
    # 6-Kai  ->  7-Hanare        
    elif section_no == 6:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} and normL > {int(thsd(PRM[1]))} ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
        if normR > thsd(PRM[0]) and normL > thsd(PRM[1]):
            # 右手首の移動ベクトルの長さが10以上の場合（離れ）
            started = True
        elif normR > thsd(PRM[0]):
            Step_counter += 1
            Stkp.push( [(2,PRM[2])] )  
            if Step_counter > PRM[2]:
                # 左手首（弓手）の押しタイミングズレ
                Alart_id = Alart_Hanare
                Step_error = True
                started = True
        elif Step_counter > 0: 
            # 左手首（弓手）の動き検知なし
            started = True
    
    # 7-Hanare  ->  8-Zan-shin        
    elif section_no == 7:  
        mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[0]))} ]")

        Stkp.push( [(0,PRM[0])] )  
        if normR < thsd(PRM[0]) :
            started = True

    # 8-Zan-shin  ->  9-''(弓倒し)
    elif section_no == 8:  
        mylog.log(INFO, f">>>   normR={int(normR)}({thsd.ratio(normR):.3f}), normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} and normL > {int(thsd(PRM[1]))} ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
        if normR > thsd(PRM[0]) and normL > thsd(PRM[1]):
            # 右手首と左手首の移動ベクトルの長さが大きい場合（弓だおし開始）
            started = True
    
    # 9-''(弓倒し)  ->  0-Start
    elif section_no == 9:  
        if Step_counter == 0: Step_counter = 10
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), normSR={int(normS)}({thsd.ratio(normS):.3f})")

        mylog.log(INFO, f">>>   [ normS > {int(thsd(PRM[0]))} ]")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[2]))} ]")

        Stkp.push( [(0,PRM[0])] )  
        if normS > thsd(PRM[0]):
            # 右腰の移動ベクトルの長さが大きい場合（退場）
            if Step_counter/10 == 1: Step_counter = 20
            Step_counter += 1
            Stkp.push( [(1,PRM[1])] )  
            if Step_counter%10 == PRM[1]: started = True
        else:
            Stkp.push( [(2,PRM[2])] )  
            if normR > thsd(PRM[2]):
                # 右手首と左手首の移動ベクトルの長さが大きい場合（矢つがえ開始）
                if Step_counter/10 == 2: Step_counter = 10
                Step_counter += 1
                Stkp.push( [(3,PRM[3])] )  
                if Step_counter%10 == PRM[3]: started = True
    else:
        mylog.log(ERROR, f">>> section_no={section_no}は未定義のセクションです")
        started = False
    #
    mylog.log(INFO, f">>>   started  ({section_no}): started={started}")
    return started
#
#セクションが完了したかどうかを判定する関数
#
def section_completed(section_no, myResult:MyResult):
    global Step_counter, Step_error, Alart_id
    global RL_angle, SL_angle, ER_angle
    
    keyPoints = myResult                            # キーポイントのデータ解析インスタンス
    ibox = myResult.boxid
    
    thsd = Threshold(keyPoints.block_height)        # バウンディングボックスの高さを基準に閾値設定インスタンス

    # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
    arrow = myResult.arrow_length_angles[Sample_lag]  
    
    normR, anglR = arrow[Kn2idx['right_wrist']]                     # 右手首の移動ベクトルの長さと角度
    normL, _ = arrow[Kn2idx['left_wrist']]                          # 左手首の移動ベクトルの長さと角度
    normER, _ = arrow[Kn2idx['right_elbow']]                        # 右肘の移動ベクトルの長さと角度
    normEL, _ = arrow[Kn2idx['left_elbow']]                         # 左肘の移動ベクトルの長さと角度
    
    xy_wristR = keyPoints.xy('right_wrist')                         # 右手首の座標
    xy_wristL = keyPoints.xy('left_wrist')                          # 左手首の座標
    xy_nose = keyPoints.xy('nose')                                  # 鼻の座標

    lenY, _ = keyPoints.norm('right_eye', 'left_eye')               # 右目と左目のベクトルの長さと角度を計算
    _, RL_angle = keyPoints.norm('right_wrist', 'left_wrist')       # 右手首から左手首へのベクトルの長さと角度を計算
        
    completed = False
    # 共通の開始条件を取得
    PRM = CompleteAction_param['param'][10]    # 10は共通の開始条件 
    conf = keyPoints.conf('right_wrist')                                # 右手首の座標の信頼度
    
    if conf < PRM[0]  and (section_no > 1 and section_no < 9):
        # 右手首の信頼度が低い
        mylog.log(INFO, f"completed({section_no}): right-wrist-conf={conf:.2f}({PRM[0]:.2f}), "\
                      + f" skip....")
        return completed

    mylog.log(INFO, f"completed({section_no}):フレーム={Frame_counter}\n"\
            + f"    boxid={ibox}, H={int(thsd.block_height)}, wristR=[{int(xy_wristR[0])}, {int(xy_wristR[1])}],"\
            + f"    normR={int(normR)}({thsd.ratio(normR):.3f}), anglRL={int(RL_angle)}°, conf={conf:.2f}, counter={Step_counter}")
    
    #
    # 節の動作完了（次節への移行体制）条件を判定
    #    
    # セクションごとの開始条件を取得
    PRM = CompleteAction_param['param'][section_no]  
    # 1-Asi-bumi
    if section_no == 1:  
        if Step_counter == 0:
            lenY, _ = keyPoints.norm('right_eye', 'left_eye')         # 右目と左目のベクトルの長さと角度を計算
            conf= keyPoints.conf('left_eye')       
            mylog.log(INFO, f">>>   lenY={int(lenY)}({thsd.ratio(lenY):.3f}), conf={conf:.2f}")
            mylog.log(INFO, f">>>   [  lenY > {int(thsd(PRM[0]))} and conf > {PRM[1]:.2f} ]")
            
            Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
            if lenY > thsd(PRM[0]) and conf > PRM[1]:
                # 右目と左目のベクトルの長さが10以上、左目の信頼度が0.5以上の場合（正面を向く）
                Step_counter = 10
        else:
            normN, _ = arrow[Kn2idx['nose']]                        # 鼻の移動ベクトルの長さと角度
            normHR, _ = arrow[Kn2idx['right_hip']]                  # 左腰の移動ベクトルの長さと角度
            normHL, _ = arrow[Kn2idx['left_hip']]                   # 左腰の移動ベクトルの長さと角度
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), normN={int(normN)}({thsd.ratio(normN):.3f}), "\
                            + f" normHR={int(normHR)}({thsd.ratio(normHR):.3f}), normHL={int(normHL)}({thsd.ratio(normHL):.3f})") 

            mylog.log(INFO, f">>>   [ (normR <= {int(thsd(PRM[2]))} and normL <= {int(thsd(PRM[3]))}) and"\
                        + f" (normHR <= {int(thsd(PRM[4]))}) and (normHL <= {int(thsd(PRM[5]))}) and (normN <= {int(thsd(PRM[6]))}) ]")
            
            Stkp.push( [(2,PRM[2]), (3,PRM[3]), (4,PRM[4]), (5,PRM[5]), (6,PRM[6])] )  
            if (normR <= thsd(PRM[2]) and normL <= thsd(PRM[3])) and (normHR <= thsd(PRM[4]) and normHL <= thsd(PRM[5])) and (normN <= thsd(PRM[6])):
                # 右手首と左手首、右腰骨と左腰骨の移動ベクトルの長さが10未満、鼻の移動ベクトルの長さが10未満、
                Step_counter += 1
                if (Step_counter%10) == PRM[7]: completed = True
                
        if not completed and CameraPos == 'Front-side':
            xy_hipL = keyPoints.xy('left_hip')                         # 右腰の座標
            mylog.log(INFO, f">>>   x_wristR={int(xy_wristR[0])}, x_hipL={int(xy_hipL[0])}")
            mylog.log(INFO, f">>>   int(x_wristR) > int(x_hipL")
            if int(xy_wristR[0]) > int(xy_hipL[0]):
                # 右手首が左腰の前にある（足踏み完了なしで矢番え動作（胴作り）へ）
                Alart_id = Alart_Asibumi
                Step_error = True
            
    # 2-Dou-zukuri            
    elif section_no == 2:  
        if Step_counter == 0: Step_counter = 1  # 初期化（矢番え動作開始）
        
        if Step_counter == 10:
            mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[5]))} ]")
            
            Stkp.push( [(5,PRM[5])] )  
            if normR > thsd(PRM[5]): Step_counter = 20
            # 右手首の移動ベクトルの長さが大きい場合（取り矢動作開始）
        else:
            _, angER = keyPoints.norm('right_elbow', 'right_wrist')     # 右肘から右手首へのベクトルの角度を計算
            _, angSE = keyPoints.norm('right_shoulder', 'right_elbow')  # 右肩から右肘へのベクトルの角度を計算
            mylog.log(INFO, f">>>   angER= {angER:.1f}°, angSE= {angSE:.1f}°")
            mylog.log(INFO, f">>>   [ (angER > {PRM[0]:.1f} and angER < {PRM[1]:.1f}) and angSE > {PRM[2]:.1f} ]")
            
            Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2])] )  
            if ( (angER > PRM[0] and angER < PRM[1]) and (angSE > PRM[2]) ):
                # 右手首と右肘を結ぶベクトルの角度が65度から95度の範囲内の場合
                mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[3]))} ]")
            
                Stkp.push( [(3,PRM[3])] )  
                if ( normR <= thsd(PRM[3]) ) : 
                    if Step_counter < 10:
                        # 右手首と左手首の移動ベクトルの長さが10未満の場合（矢つがえ動作完了）
                        Step_counter += 1
                        Stkp.push( [(4,PRM[4])] )  
                        if (Step_counter%10) == PRM[4]: Step_counter = 10        #２回保持
                    elif Step_counter >= 20:
                        # 右手首と左手首の移動ベクトルの長さが10未満の場合（胴作り完了）
                        Step_counter += 1
                        Stkp.push( [(6,PRM[6])] )  
                        if (Step_counter%10) == PRM[6]: completed = True         #５回保持
            else:
                Step_counter = int(Step_counter/10)*10 + 1 # 連続回数をリセット
                        
    # 3-Yu-gamae            
    elif section_no == 3:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), normER={int(normER)}({thsd.ratio(normR):.3f}),"\
                      + f" normEL={int(normEL)}({thsd.ratio(normEL):.3f}), lenY={int(lenY)}({thsd.ratio(lenY):.3f})")
        if Step_counter < 10:
            mylog.log(INFO, f">>>   [ (normR < {int(thsd(PRM[0]))} and normL < {int(thsd(PRM[1]))})"\
                            + f" and (normER < {int(thsd(PRM[2]))} and normEL < {int(thsd(PRM[3]))}) ]")

            Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3])] )  
            if (normR < thsd(PRM[0]) and normL < thsd(PRM[1])) and (normER < thsd(PRM[2]) and normEL < thsd(PRM[3])) :
                # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満の場合
                Step_counter = Step_counter + 1
                Stkp.push( [(4,PRM[4])] )  
                if Step_counter >= PRM[4]: Step_counter = 10
            else: Step_counter = 0
        else:            
            mylog.log(INFO, f">>>   [ lenY < {int(thsd(PRM[5]))} ]")
            
            Stkp.push( [(5,PRM[5])] )  
            if lenY < thsd(PRM[5]):  
                # 物見を定める
                Step_counter = Step_counter + 1
            Stkp.push( [(6,PRM[6])] )  
            if Step_counter%10 >= PRM[6]: completed = True   # 
            else:
                mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[7]))} and normL > {int(thsd(PRM[7]))} ]")
                Stkp.push( [(7,PRM[7])] )  
                if normR > thsd(PRM[7]) and normL > thsd(PRM[7]):
                    # 右手首と左手首の移動ベクトルの長さが大きい（物見なしで打ちおこし）
                    Alart_id = Alart_Monomi
                    Step_error = True                
                
    # 4-Uti-okosshi        
    elif section_no == 4:
        if Step_counter < 10:  
            mylog.log(INFO, f">>>   xy_nose={int(xy_nose[1])}, xy_wristR={int(xy_wristR[1])}, xy_wristL={int(xy_wristL[1])}")
            mylog.log(INFO, f">>>   [ (xy_wristR[1] < xy_nose[1] and xy_wristL[1] < xy_nose[1] ]")
            if (xy_wristR[1] < xy_nose[1] and xy_wristL[1] < xy_nose[1]):
                # （右手首と左手首が鼻より高い位置（Y軸は下方が正）
                Step_counter = 10
        else:
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                          + f"normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normEL)}({thsd.ratio(normEL):.3f})")
            mylog.log(INFO, f">>>   [ (normR < {int(thsd(PRM[0]))} and normL < {int(thsd(PRM[1]))}) and (normER < {int(thsd(PRM[2]))} and normEL < {int(thsd(PRM[3]))}) ]")

            Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3])] )  
            if (normR < thsd(PRM[0]) and normL < thsd(PRM[1])) and (normER < thsd(PRM[2]) and normEL < thsd(PRM[3])):
                # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満
                Step_counter = Step_counter + 1
                Stkp.push( [(4,PRM[4])] )  
                if (Step_counter%10) == PRM[4]: completed = True   # ３回保持で完了                
    
    # 5-Hiki-wake        
    elif section_no == 5:  
        xy_shouderR = keyPoints.xy('right_shoulder')                # 右腰の座標
        mylog.log(INFO, f">>>   y_nose={int(xy_nose[1])}, y_wristR={int(xy_wristR[1])}, y_shoulR={int(xy_shouderR[1])}")

        mylog.log(INFO, f">>>   [ y_wristR < y_nose ]")
        if  xy_wristR[1] < xy_nose[1]  :
            # 右手首が鼻より高い位置（Y軸は下方が正）
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
            if Step_counter < 10:   # 「打越し」から「大三」への移行
                mylog.log(INFO, f">>>   [ normL < {int(thsd(PRM[0]))} ]")
                Stkp.push( [(0,PRM[0])] )  
                if normL < thsd(PRM[0]):  Step_counter += 1
                Stkp.push( [(1,PRM[1])] )  
                if Step_counter > PRM[1]: Step_counter = 10
            elif PRM[2] > 0.0:  # 「大三」から「引き分け」完了への移行
                mylog.log(INFO, f">>>   [ normL > {int(thsd(PRM[2]))} ]")
                Stkp.push( [(2,PRM[2])] )  
                if normL > thsd(PRM[2]):  Step_counter = 11         # 「押し」
                    # 「押し」を優先的に判定する
                else:
                    mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[2]))} ]")
                    Stkp.push( [(2,PRM[2])] )  
                    if normR > thsd(PRM[2]):  Step_counter = 12     # 「引き」
            else: Step_counter = 13

        elif  xy_wristR[1] < xy_shouderR[1] :
            # （右手首が右肩より高い位置で停止）
            if Step_counter < 20: Step_counter = 20
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                          + f" normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normL)}({thsd.ratio(normEL):.3f})")
            mylog.log(INFO, f">>>   [ (normR < {int(thsd(PRM[3]))} and normL < {int(thsd(PRM[4]))}) and (normER < {int(thsd(PRM[5]))} and normEL < {int(thsd(PRM[6]))}) ]")

            if Step_counter > 90 :  # 離れアラート設定（仮）
                _, angER = keyPoints.norm('right_elbow', 'right_wrist')     # 右肘から右手首へのベクトルの長さと角度を計算
                mylog.log(INFO, f">>>   angER={angER:.1f}°")
                if angER > 145 or angER < -145: 
                    Alart_id = Alart_KaiNasi
                    Step_error = True
                else: Step_counter = 20 + Step_counter%10
            else:    
                Stkp.push( [(3,PRM[3]), (4,PRM[4]), (5,PRM[5]), (6,PRM[6])] )  
                if (normR < thsd(PRM[3]) and normL < thsd(PRM[4])) and (normER < thsd(PRM[5]) and normEL < thsd(PRM[6])) :
                    # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満（姿勢の保持で完了）
                    Step_counter = Step_counter + 1
                    Stkp.push( [(7,PRM[7])] )  
                    if (Step_counter%10) == PRM[7]:  completed = True
                else:
                    # 右手首の移動ベクトルの長さが大きい（会なしで離れ）
                    mylog.log(INFO, f">>>   [ (Step_counter%10) > {PRM[8]} and (normR > {int(thsd(PRM[9]))}) ]")
                    Stkp.push( [(8,PRM[8]), (9,PRM[9])] )  
                    if (Step_counter%10) > PRM[8] and normR > thsd(PRM[9]):
                        Step_counter = 90 + Step_counter%10         # 離れアラート設定（仮）
    # 6-Kai            
    elif section_no == 6:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                      + f" normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normEL)}({thsd.ratio(normEL):.3f}) ")
        mylog.log(INFO, f">>>   [ (normR < {int(thsd(PRM[0]))} and normL < {int(thsd(PRM[1]))}) and (normER < {int(thsd(PRM[2]))} and normEL < {int(thsd(PRM[3]))}) ]")

        if Step_counter == 0: Step_counter = 1  # 初期化（口割）
        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3])] )  
        if (normR < thsd(PRM[0]) and normL < thsd(PRM[1])) and (normER < thsd(PRM[2]) and normEL < thsd(PRM[3])) :
            # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満（姿勢の保持で完了）
            Step_counter = Step_counter + 1
            Stkp.push( [(4,PRM[4])] )  
            if Step_counter == PRM[4]:  completed = True
        else:
            mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[5]))} and normL > {int(thsd(PRM[6]))} ]")

            Stkp.push( [(5,PRM[5]), (6,PRM[6])] )  
            if normR > thsd(PRM[5]) and normL > thsd(PRM[6]):
                # 右手首の移動ベクトルの長さが大きい（会不十分で離れ）
                Alart_id = Alart_KaiFusoku
                Step_error = True
    
    # 7-Hanare        
    elif section_no == 7:  
        _, ER_angle = keyPoints.norm('right_elbow', 'right_wrist')   # 右肘から右手首へのベクトルの長さと角度を計算
        _, SL_angle = keyPoints.norm('left_shoulder', 'left_wrist')     # 左肩から左手首へのベクトルの長さと角度を計算
        mylog.log(INFO, f">>>   angR-ELWR={ER_angle:.1f}°, angL-SHWR={SL_angle:.1f}°")
        
        Step_counter = Step_counter + 1
        Stkp.push( [(0,PRM[0])] )  
        if Step_counter > PRM[0]: completed = True
    
    # 8-Zan-shin    
    elif section_no == 8:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[0]))} and normL < {int(thsd(PRM[1]))} ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
        if normR < thsd(PRM[0]) and normL < thsd(PRM[1]):
            # 右手首と左手首の移動ベクトルの長さが50以下の場合（姿勢の保持で完了）
            Step_counter = Step_counter + 1
            Stkp.push( [(2,PRM[2])] )  
            if Step_counter == PRM[2]:  completed = True
    
    # 8-Zan-shin(弓倒し)        
    elif section_no == 9:  
        _, angER = keyPoints.norm('right_elbow', 'right_wrist')             # 右肘から右手首へのベクトルの長さと角度を計算
        normS, _ = arrow[Kn2idx['right_shoulder']]                          # 右肩の移動ベクトルの長さと角度
        mylog.log(INFO, f">>>   angER= {angER:.1f}°, normSR={int(normS)}({thsd.ratio(normS):.3f})")
        mylog.log(INFO, f">>>   [ angER > {PRM[0]:.1f} and angER < {PRM[1]:.1f} ]")
        
        if Step_counter == 0: Step_counter = 1
        Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
        if ( angER > PRM[0] and angER < PRM[1] ):
            # 右手首と右肘を結ぶベクトルの角度が65度から95度の範囲内の場合
            mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[2]))} ]")

            Stkp.push( [(2,PRM[2])] )  
            if normR <= thsd(PRM[2]) : 
                Step_counter = Step_counter + 1
                Stkp.push( [(3,PRM[3])] )  
                if Step_counter == PRM[3]: completed = True

        mylog.log(INFO, f">>>   [ normS > {int(thsd(PRM[4]))} ]")

        Stkp.push( [(4,PRM[4])] )  
        if normS > thsd(PRM[4]):
            # 右腰の移動ベクトルの長さが大きい場合（退場）
            Step_counter = 0
            completed = True
            
    else:
        mylog.log(ERROR, f">>>  section_no={section_no}は未定義のセクションです")
        completed = False
    #
    mylog.log(INFO, f">>>   completed({section_no}): completed={completed}")
    return completed
#
#キーポイントをフレームに描画する関数
'''
    #:param annotated_frame: 描画対象のフレーム
    #:param points: キーポイントの座標
    #:param idxs: キーポイントのインデックスリスト
    #:param color: キーポイントの色
    #:param weight: 線の太さ
    #:param radius: キーポイントの半径（Noneの場合は描画しない）
'''
def draw_kpt_line(annotated_frame, points, idxs,  color=(0, 255, 0), weight=2, radius=None):
    for i, idx  in enumerate(idxs):
        if i == 0:
            x1, y1 = map(int, points[idx])
            if x1 == 0 or y1 == 0: break
        else:
            x2, y2 = map(int, points[idx])
            if x2 == 0 or y2 == 0: break
            cv2.line(annotated_frame, (x1, y1), (x2, y2), color, weight)  # 緑色のライン
            x1, y1 = x2, y2  # 次のラインの始点を更新
        if radius is not None:
            # キーポイントの半径が指定されている場合、キーポイントを描画
            cv2.circle(annotated_frame, (x1, y1), radius, color, -1)
#
# キーポイントの接続ラインを描画する関数
#
#def draw_kpts_line(annotated_frame, keypoints, ibox):
def draw_kpts_line(annotated_frame, points):
    # キーポイントの接続ラインを定義
    arm_line = [Kn2idx['right_wrist'], 
                Kn2idx['right_elbow'], 
                Kn2idx['right_shoulder'],
                Kn2idx['left_shoulder'], 
                Kn2idx['left_elbow'],
                Kn2idx['left_wrist']]       # 右手首ー＞左手首のキーポイントインデックス
    body_line = [Kn2idx['right_shoulder'], 
                Kn2idx['right_hip'], 
                Kn2idx['left_hip'], 
                Kn2idx['left_shoulder']]    # 胴体のキーポイントインデックス
    legR_line = [Kn2idx['right_hip'], 
                Kn2idx['right_knee']] 
#                Kn2idx['right_ankle']]      # 右脚のキーポイントインデックス
    legL_line = [Kn2idx['left_hip'], 
                Kn2idx['left_knee']] 
#                Kn2idx['left_ankle']]       # 左脚のキーポイントインデックスhhhqq
    
    eye_line = [Kn2idx['right_eye'], 
                Kn2idx['left_eye']]         # 目のキーポイントインデックス
    
    # キーポイントの接続ラインを描画
    draw_kpt_line(annotated_frame, points, arm_line,  color=(0, 255, 0), weight=2, radius=3)    # 右手首ー＞左手首 
    draw_kpt_line(annotated_frame, points, body_line, color=(0, 255, 0), weight=2, radius=3)    # 胴体
    #draw_kpt_line(annotated_frame, points, legR_line, color=(255, 0, 0), weight=2, radius=3)   # 右脚
    #draw_kpt_line(annotated_frame, points, legL_line, color=(255, 0, 0), weight=2, radius=3)   # 左脚
    draw_kpt_line(annotated_frame, points, eye_line,  color=(255, 0, 0), weight=2, radius=3)    # 目
#
# 日本語テキストの描画
#
def draw_text(imag, message, point, color ):
    #font_path = 'C:/Windows/Fonts/meiryo.ttc'
    font_path = 'meiryob.ttc'
    font_size = 20
    '''
    b, g, r = color
    font_color = (r, g, b)
    '''
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
# 表示セクション名と色を返す関数 
def edit_section_name(no, counter):
    # セクション名を編集する
    name = Section_names[no]    
    if counter > 0:                     # セクション内の動作カウンターが1以上の場合、セクション名にカウンターを追加
        stepKey = no*100 + counter
        #print(f"stepKey={stepKey}")
        if stepKey in Step_names:
            name += f"（{Step_names[stepKey]}）"            # 大三
        else :
            if Debug_opt > 1 : name += f"（{counter}）"     # その他
            else : pass   
    # セクションの色を設定    
    if Step_error or Section_color == RED: 
        if Section_no > Alart_section + 1:
            # セクション番号がアラートセクション番号より2以上大きい場合、アラート表示をクリア
            color = YELLOW
        else:  color = RED                      # 不正な動作のセクションの色（赤色）BGR
    else:
        color =  YELLOW                         # セクションの色（黄色）BGR
        if Completed: color = GREEN             # 完了したセクションの色（緑色）BGR

    return name, color
#
# 動作の開始を判定する関数
#  
def manual_analize_start(section_no, myResult:MyResult):
    global Section_no, Split_start, Split_sec, Lap_start, Lap_sec, Action_start
    global Completed, Step_counter, Nop_counter
    global Step_error, Alart_section, Alart_id
    
    # 動作の開始を判定
    if section_started(section_no, myResult):
        print(f"[manual_analize_]: Section({section_no}), strated=True")
        Action_start = Lap_sec
        Split_start = Frame_counter                         # スプリット開始時間を記録
        Split_sec = 0.0
        Completed = False                                   # セクションが開始されたら完了フラグをリセット    
        Nop_counter = 0                                     # セクション内の動作が完了しない場合のカウンター
        if Section_no != 9: 
            Section_no = Section_no + 1                     # セクション番号をインクリメント
            Step_counter = 0                                # セクション内の動作カウンター
        else: 
            counter = int(Step_counter/10)      
            mylog.log(INFO, f"[manual_analize_]: Step_counter={Step_counter}, {counter}") 
            if counter == 2: 
                Lap_start = 0                               # 退場動作開始の場合、解析終了
                Split_sec = 0.0
                Split_start = 0
            else:                                           # 乙矢の矢つがえ動作開始
                # セクション番号を2にリセット、動作カウンターを30に設定
                Section_no = 2
                Step_counter = 30
                mylog.log(INFO, f"[manual_analize_]: Next {Section_names[Section_no]} Sction_no={Section_no}, Step_counter={Step_counter}") 
        #
    else:
        Nop_counter += 1
        if Step_error:
            # セクション内の動作が不正な場合
            Alart_section = Section_no
            mylog.log(INFO, f"[manual_analize_start]: Step_error={Step_error}, Alart_id={Alart_id}")
            if Alart_id == Alart_Hanare:   # 弓手押しタイミングの遅れ
                Section_no += 1                             # セクション番号をインクリメント
            if Alart_id == Alart_KaiNasi: Section_no += 1   # 会なしで離れた場合
            Step_counter = 0
            Nop_counter = 0                                 # セクション内の動作が完了しない場合のカウンター
        #
    return Section_no, Completed  
#
# 動作の完了を判定する関数
#
def manual_analize_completed(section_no, myResult:MyResult):
    global Section_no, Split_start, Split_sec, Lap_start, Lap_sec, Action_start
    global Completed, Step_counter, Nop_counter
    global Step_error, Alart_section, Alart_id
    
    # 動作の完了を判定
    if section_completed(section_no, myResult):
        print(f"[manual_analize_]: Section({section_no}), completed=True")
        Action_start = Lap_sec
        Completed = True 
        if Section_no != 6 and Section_no != 8:             # 「会」、「残身」はスプリットを計測
            Split_start = 0                                 # スプリット開始時間をリセット
        if Section_no == 9 and Step_counter == 0:           # 退場動作の場合、解析終了 
            Lap_start = 0
        Step_counter = 0
        Nop_counter = 0
    else:
        Nop_counter += 1
        if Step_error:
            # セクション内の動作が不正な場合
            Alart_section = Section_no
            mylog.log(INFO, f"[manual_analize_completed]: Step_error={Step_error}, Alart_id={Alart_id}")
            if Alart_id == Alart_Asibumi: Section_no = 2        # 足踏み不完全で矢番えの場合
            if Alart_id == Alart_Monomi: Section_no = 4         # 物見なしで打ちおこしの場合
            if Alart_id == Alart_KaiNasi: Section_no = 7        # 会なしで離れた場合
            if Alart_id == Alart_KaiFusoku: Section_no = 7      # 会不十分で離れた場合
            Step_counter = 0
            Nop_counter = 0
        #
    return Section_no, Completed  
#
# 特徴量データフレームのインスタンス
InputPdf:FeaturePdf = None
#
# 検出結果をフレームに描画する関数
#
def plot(myResult:MyResult, annotated_frame, output_dim=None, nn_gru=False, model=None):
    global Section_no, Completed, Action, Step_counter, CameraPos, Nop_counter
    global Split_start, Split_sec, Lap_start, Lap_sec
    global Step_error, Alart_section, Alart_id, Section_color, Alart_message
    
    result = myResult.result
    mylog.log(DEBUG, f"Tracking_enabled={Tracking_enabled}")
    mylog.log(DEBUG, f"[plot]: {type(result.keypoints)},{len(result.keypoints)}個のキーポイント")

    #if annotated_frame is None:
        # YOLOv8のplot関数を使用してフレームに描画  
        # 　kpt_line=False： キーポイントのマークのみを描画）
        #annotated_frame = result.plot(boxes=True, labels=False, kpt_line=True, kpt_radius=3)
    #else:    
    # 対象ボックスのキーポイントの接続ラインを描画
    draw_kpts_line(annotated_frame, myResult.points)   

    if Section_no < 2: 
        # カメラの位置取得（足踏み完了まで）
        CameraPos = get_camera_pos(myResult)                

    # セクション情報を更新
    arrows = myResult.arrow_length_angles       # キーポイントの移動ベクトルの長さと角度を取得
    
    if CameraPos in ['Right-side', 'Front-side'] and arrows[Sample_lag] is not None:
        if Tracking_enabled or nn_gru:
            # 姿勢解析入力データリストを作成、保存しておく
            tracking_result(myResult, InputPdf, output_dim, csvout=False)
        # 姿勢解析結果のキーポイントの座標変位から、射法八節の動作の開始、完了を判定する
        if Lap_start > 0:    
            # 射法八節の動作開始、完了を判定する（キー'0'の押下で判定を開始する）
            Step_error = False
            Alart_id = 0
            if nn_gru:
                # GRUモデルによる姿勢解析
                # カレントのデータフレームを作成、保存
                InputPdf.set_current_pdf(Section_no, Completed)
                mylog.log(DEBUG, f"[plot]: curPdf.shape={InputPdf.curPdf.shape}")
                mylog.log(DEBUG, f"[plot]: {InputPdf.curPdf.tail()}")
                if not InputPdf.is_ready():
                    # シーケンスデータの準備をする
                    InputPdf.add_previous_pdf()
                    mylog.log(DEBUG, f"[plot]: prePdf.shape={InputPdf.prePdf.shape}")
                    mylog.log(DEBUG, f"[plot]: {InputPdf.prePdf.tail()}")
                else:
                    # 入力データフレームを取得
                    input_pdf = InputPdf.get_input_pdf()
                    # GRUモデルによる動作解析
                    Section_no, Completed, Action = gru_analize(Section_no, Completed, model, input_pdf)
                    InputPdf.update_previous_pdf()
                
            # ハイブリッドモデルの場合、プログラムロジックによる姿勢解析も行う
            if not nn_gru or Hybrid_model:
                # プログラムロジックによる姿勢解析
                if Section_no == 0 or Completed:
                    # 動作の開始を判定
                    Section_no, Completed = manual_analize_start(Section_no, myResult)
                else:
                    # 動作の完了を判定
                    Section_no, Completed = manual_analize_completed(Section_no, myResult)
            #
            Db.section = Section_no        # トラッキングデータのセクション番号を設定              
            Db.completed = 1 if Completed else 0

            if Tracking_enabled:
                # 解析結果のデータをCSVに出力する
                tracking_result(myResult, InputPdf, output_dim, csvout=True)
            if Update_enabled:
                # トラッキングデータのテーブル（'section'/'completed'）を更新する
                Db.update_tracking_section()  
                if Step_error: Db.update_tracking_tag( 'tag1', 9 ) # 不正動作を登録
    #
    # セクション情報をフレームに描画
    if Lap_start > 0:   Lap_sec = (Frame_counter - Lap_start)/Fps         # ラップ秒を計算
    if Split_start > 0: Split_sec = (Frame_counter - Split_start)/Fps     # スプリット秒を計算

    # セクション名を編集
    section_name, Section_color = edit_section_name(Section_no, Step_counter)   
    others_color =  WHITE                       # その他の色（白）

    if Alart_id > 0: 
        #　警告メッセージ（全角文字）取得
        Alart_message = Alart_msg[Alart_id*10]
        print(f"フレーム({Frame_counter}):{Alart_msg[Alart_id*10]}")
        mylog.log(INFO, f">>> {Alart_msg[Alart_id*10]}")
        
    # テキストの描画 （カメラ位置、セクション名、スプリット秒、ラップ秒、角度）          
    cv2.putText(annotated_frame, f"camera: {CameraPos}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 1)
    #cv2.putText(annotated_frame, f"section: {section_name}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, Section_color, 2)
    annotated_frame = draw_text(annotated_frame, f"Section : {section_name}", (10, 40),  Section_color)
    cv2.putText(annotated_frame, f"split   : {Split_sec:6.2f}sec.", (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 1)
    cv2.putText(annotated_frame, f"lap    : {Lap_sec:6.2f}sec.", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 1)
    if Section_no == 4 or Section_no == 5 or Section_no == 6:
        cv2.putText(annotated_frame, f"angle  : {-1*RL_angle:6.1f}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 1)
    if Section_no == 7 or Section_no == 8:
        cv2.putText(annotated_frame, f"angle  : {-1*ER_angle:6.1f}  {-1*SL_angle:6.1f}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 1)
    # 警告メッセージの描画
    annotated_frame = draw_text(annotated_frame, Alart_message, (10, 110), RED)
    #
    return annotated_frame
#
# キー入力の現在モード('PWR','PWT'）を編集する関数
#
def edit_key_mode(frame_height, iwait, out_file, videoWriteEnabled, raw_video, clip_video, repeat_mode ):
 
        mode_str = 'P' if  iwait == 0 else 'p'
        if raw_video and not clip_video: mode_str += 'R' if repeat_mode else 'r'
        if out_file != '':  mode_str += 'W' if videoWriteEnabled else 'w'
        if Tracking_only:   mode_str += 'T' if Tracking_enabled else 't'
        if Update_tracking: mode_str += 'U' if Update_enabled else 'u'
        return (10, frame_height - 20), mode_str
#
# キー入力のガイダンスを編集する関数
#
def edit_key_ope(out_file, raw_video, clip_video):
 
        ope_str = '(q)uit:(p)ause:(<)back:(>)forward:(k)fast:(l)slow:(s)nap'
        if out_file != '':  ope_str += ':(w)rite-video'
        if Tracking_only:   ope_str += ':(t)racking'
        if Update_tracking: ope_str += ':(u)pdate-tracking'
        if raw_video and (not clip_video):   ope_str += ':(r)epeat-play'
        return  ope_str
#
#    画像のコントラストと明るさを調整する関数
#
def adjust_frame_contrast(frame, alpha=1,beta=0):
    """
    :param frame: 入力画像
    :param alpha: コントラスト係数（1.0で元のコントラスト、0.0でコントラストなし）
    :param beta: 明るさ係数（0で元の明るさ、正の値で明るく、負の値で暗く）
    :return: 調整後の画像
    """
    #
    table = np.array([np.clip((i * alpha + beta), 0, 255) for i in range(256)], dtype=np.uint8)
    adjusted_frame = cv2.LUT(frame, table)  # ルックアップテーブルを使用してコントラストと明るさを調整
    return adjusted_frame
#
# モザイク処理
#
def mosaic_area( src, y, x, height, width, ratio=0.1):
    #print(f"[mosice_area]:({y}, {x}), height={height}, width={width}, shape={src.shape}")
    if y <= 0 or (y + height) >= src.shape[0]: return src
    x = 0 if x < 0 else x
    x = src.shape[1] - width if (x + width) >= src.shape[1] else x
    #print(f"[mosice_area]:({y}, {x})")
    
    dst_area = src[y:y + height, x:x + width]
    small = cv2.resize(dst_area, dsize=None, fx=ratio, fy=ratio, interpolation=cv2.INTER_NEAREST)
    zoom = cv2.resize(small, dsize=(width, height), interpolation=cv2.INTER_NEAREST)
    src[y:y + height, x:x + width] = zoom
    return src
#
# モザイク処理エリアを取得する関数
#
def get_mosaic_areas(myResult):
    areas = []
    boxes = myResult.boxes              # 検出されたバウンディングボックスの取得
    keypoints = myResult.keypoints      # 検出されたキーポイントの取得
    max_box_no = myResult.boxid         # 対象ボックスの番号
    
    # 対象ボックス以外の顔エリアの矩形を求める
    for i in range(len(boxes.xywh)):        
        if i == max_box_no: continue 
        _, _, w, _ = map(int, boxes.xywh[i])                                # ボックスの幅を取得
        x, y = map(int, keypoints.xy[i][Kn2idx['nose']]) 
        x1, _ = map(int, keypoints.xy[i][Kn2idx['left_eye']]) 
        x2,_ = map(int, keypoints.xy[i][Kn2idx['right_eye']]) 
        if x == 0: x = x1 if x1 > 0 else x2
        #conf = keypoints.conf[i][Kn2idx['nose']].item()
        #mylog.log(DEBUG, f"[get_mosaic_areas]:{i}:({y}, {x}, {conf:.3f}, {x1}, {x2}, {w})")
        mylog.log(DEBUG, f"[get_mosaic_areas]:{i}:({y}, {x}, {x1}, {x2}, {w})")
        areas.append( [int(y - w/4), int(x - w/3), int(w/1.5), int(w/1.5)] )    # 矩形情報を追加
    return areas
#
# 2つのフレームを重ねて表示する関数
#
def multi_frame_display(frame1, frame2):
    h1, w1 = frame1.shape[0:2]
    h2, w2 = frame2.shape[0:2]
    h = min(h1, h2)
    w = min(w1, w2)
    frame1 = cv2.resize(frame1, (w, h))
    frame2 = cv2.resize(frame2, (w, h))
    # 画像を重ねて表示
    return cv2.addWeighted(frame1, 0.5, frame2, 0.5, 0) 
#
# グリッド線を描画する関数 
def draw_grid(img, grid_shape, grid_shift, color=(0, 255, 0), thickness=1):
    h, w, _ = img.shape
    rows, cols = grid_shape
    dy, dx = h / rows, w / cols
    # グリッド線のシフト
    sy, sx = grid_shift
    sy = int(round(dy*sy)) if sy > 0 else 0
    sx = int(round(dx*sx)) if sx > 0 else 0

    # draw vertical lines
    for x in np.linspace(start=dx, stop=w-dx, num=cols-1):
        x = int(round(x)) + sx
        cv2.line(img, (x, 0), (x, h), color=color, thickness=thickness)

    # draw horizontal lines
    for y in np.linspace(start=dy, stop=h-dy, num=rows-1):
        y = int(round(y)) + sy
        cv2.line(img, (0, y), (w, y), color=color, thickness=thickness)

    return img
#
# マウスドラッグ・イベント関数
#
class Rect:
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end
        self.drawing = False
        self.roi_set = False
        self.x = [None, None]
        self.y = [None, None]
    
    def clear(self):
        self.__init__()
            
    def length(self):
        vect = np.array(self.end) - np.array(self.start)    # 2点のベクトルを計算
        norm, _ = vector_length_angle(vect)                 # ベクトルの長さと角度を計算
        return norm
    
    def width_height(self):
        x1, y1 = self.start
        x2, y2 = self.end
        self.x[0], self.x[1] = sorted([x1, x2])
        self.y[0], self.y[1] = sorted([y1, y2])        
        return  (self.x[1] - self.x[0]), (self.y[1] - self.y[0])
    
# グローバル変数
Rect_area = Rect()
#RectAreas:Rect = []
#
def draw_rectangle(event, x, y, flags, param):
    global Rect_area

    if event == cv2.EVENT_LBUTTONDOWN:
        # ボタンダウン
        Rect_area.start = (x, y)
        Rect_area.drawing = True

    elif event == cv2.EVENT_MOUSEMOVE and Rect_area.drawing:
        # ドラッグ
        Rect_area.end = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        # ボタンアップ
        Rect_area.end = (x, y)
        Rect_area.drawing = False
        if Rect_area.length() > 100: Rect_area.roi_set = True
#
# クリッピング領域指定
def clip_process( frame ):
    global Rect_area
    rectAreas:Rect = []
    # クリッピング・ウィンドウとマウスイベント・コールバック登録
    cv2.namedWindow("Select ROI")
    cv2.setMouseCallback("Select ROI", draw_rectangle)
    # クリッピング処理
    while True:
        temp_frame = frame.copy()   # 読み込んだ先頭フレーム上で矩形領域を指定する
        for rect in rectAreas:
            # 指定済み矩形のライン描画
            cv2.rectangle(temp_frame, rect.start, rect.end, GREEN, 1)
            
        if Rect_area.drawing and Rect_area.start and Rect_area.end:
            # 矩形のライン描画
            cv2.rectangle(temp_frame, Rect_area.start, Rect_area.end, GREEN, 2)
        # キーオペレーションのヘルプ表示
        hight, _ = temp_frame.shape[:2]
        help_str = "r(eset)|c(onfirm)|q(uit)"
        cv2.putText(temp_frame, help_str, (10, hight - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, YELLOW, 2)
        cv2.imshow("Select ROI", temp_frame)
        #
        key_val = cv2.waitKey(1) & 0xFF 
        if Rect_area.roi_set: 
            # 連続して領域を指定する（先頭がクリッピング領域、2番目からモザイク領域）
            Rect_area.roi_set = False
            rectAreas.append( copy.copy(Rect_area) )
            continue            
        if key_val == ord("r"):
            # 全てキャンセルして指定し直す
            Rect_area.roi_set = False
            rectAreas.clear()
            continue
        if key_val == ord("q") or key_val == ord("c") :
            # 処理を中断、または継続する
            break
    #
    cv2.destroyWindow("Select ROI")
    if key_val == ord("q") : return  None   # 以降の処理を中断してプログラムを終了
    if len(rectAreas) == 0:
        print(f"クリッピング領域を指定してください。")
        return rectAreas
    return copy.deepcopy( rectAreas )
#
# キー入力操作関数
#
def key_ope(key, ctl, annotated_frame, cap, idir, out_file, raw_video, clip_video):
    global Frame_counter, Section_no, Completed, Split_sec, Split_start, Lap_sec, Lap_start
    global Step_counter, Nop_counter, Step_error, Section_color, Alart_message
    global Tracking_enabled, Update_enabled, Tracking_onece
    global Cv2Video
    
    if ctl['key_inter'] != 0 and (int(time.time()) - ctl['key_inter']) > ctl['key_wait']: 
        # キー入力の間隔が1秒経過したとき、連打タイマーをクリア
        ctl['key_inter'] = 0  
    #
    if key == ord('q'):
        # 'q'キーで終了
        return False
    
    elif key == ord('p'):
        # 'p'キーで一時停止/再開
        ctl['iwait'] = 0 if ctl['iwait'] > 0 else ctl['iwait_init']  
        if ctl['iwait'] == 0: print("一時停止しました")
        else: print(f"再開しました: {ctl['iwait']}ミリ秒")
    
    elif key == ord('k') or key == ord('K'):            
        # 'k'キーでウィンドウの更新間隔を短くする
        if key == ord('K') and len(ctl['key_data']) > 1 and ctl['key_data'][1:].isdigit():
            # キー入力データの2文字目以降をステップミリ秒として設定
            ctl['istep'] = int(ctl['key_data'][1:])
            ctl['key_data'] = ''            # キー入力データをクリア
        step = ctl['istep_init'] if key == ord('k') else ctl['istep']         
        ctl['iwait'] = ctl['iwait'] - step if ctl['iwait'] > step else ctl['iwait']
        print(f"動画の再生間隔を短くしました（早送り再生）: {ctl['iwait']}ミリ秒")
        
    elif key == ord('l') or key == ord('L'):
        # 'l'キーでウィンドウの更新間隔を長くする
        if key == ord('L') and len(ctl['key_data']) > 1 and ctl['key_data'][1:].isdigit():
            # キー入力データの2文字目以降をステップミリ秒として設定
            ctl['istep'] = int(ctl['key_data'][1:])
            ctl['key_data'] = ''            # キー入力データをクリア
        step = ctl['istep_init'] if key == ord('k') else ctl['istep']         
        ctl['iwait'] = ctl['iwait'] + step if ctl['iwait'] < (1000 - step) else ctl['iwait']  
        print(f"動画の再生間隔を長くしました（スロー再生）: {ctl['iwait']}ミリ秒")
        
    elif key == ord('t') and Tracking_only:
        # 't'キーで一開始／停止
        Tracking_enabled = True if Tracking_enabled is False else False  
        if Tracking_enabled: 
            print(f"トラッキングを開始します: {Db.csvpath1}")
            if not Tracking_onece:
                Db.update_frame_info('start_frame', Frame_counter)  # 開始フレーム番号
                Tracking_onece = True
            mylog.log(INFO, f">> Trucking start: {Db.csvpath1}")
        else: 
            print("トラッキングを停止します")
            Db.update_frame_info('stop_frame', Frame_counter)   # 停止フレーム番号
            mylog.log(INFO, ">> Trucking pause")

    elif key == ord('u') and Update_tracking:
        # 'u'キーで一開始／停止
        Update_enabled = True if Update_enabled is False else False  
        if Update_enabled: 
            print(f"トラッキングDB更新を開始します")
            mylog.log(INFO, f">> Update-Trucking start")
        else: 
            print("トラッキングDB更新を停止します")
            mylog.log(INFO, ">> Update-Trucking pause")
    
    elif key == ord('s'):
        # スクリーンショットを保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = f"{idir}screenshot_{timestamp}.png"
        cv2.imwrite(screenshot_path, annotated_frame)
        print(f"スクリーンショットを保存しました: {screenshot_path}")
    
    elif key == ord('w') and out_file != '':
        # 'w'キーで一開始／停止
        ctl['videoWrite'] = True if ctl['videoWrite'] is False else False  
        if ctl['videoWrite']: 
            print(f"出力ファイルに書き込みを開始します: {out_file}")
            mylog.log(INFO, ">> video write start")
            if Cv2Video is None:
                # 動画ファイルの書き込みオブジェクトを作成
                frame_height, frame_width = annotated_frame.shape[0:2]
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                Cv2Video = cv2.VideoWriter(out_file, fourcc, Fps, (frame_width, frame_height))
        else: 
            print(f"出力ファイルに書き込みを停止します: {out_file}")
            mylog.log(INFO, ">> video write pause")

    elif key == ord('r') and (raw_video and not clip_video):
        if ctl['key_inter'] > 0:
            if not ctl['repeat'] : ctl['start_frame'] = Frame_counter       # 繰り返し再生の開始フレームを設定
            else: ctl['stop_frame'] = Frame_counter                         # 繰り返し再生の終了フレームを設定
            print(f"繰り返し再生範囲を設定しました: {ctl['start_frame']} - {ctl['stop_frame']}")
        else:
            # 'r'キーで一開始／停止
            ctl['repeat'] = True if ctl['repeat'] is False else False  
            if ctl['repeat']: 
                print(f"繰り返し再生を開始します: {ctl['start_frame']} - {ctl['stop_frame']}")
                mylog.log(INFO, ">> repeat play-mode start")
            else: 
                print(f"繰り返し再生を終了します: {ctl['start_frame']} - {ctl['stop_frame']}")
                mylog.log(INFO, ">> repeat play-mode pause")
            #
            ctl['key_inter'] = int(time.time())  

    elif key == ord('R') and (raw_video and not clip_video):
            if ctl['start_frame'] > 0:# 'R'キーで再生開始フレームに戻る
                Frame_counter = ctl['start_frame']
                cap.set(cv2.CAP_PROP_POS_FRAMES, Frame_counter)
                print(f"再生開始フレームに戻りました: {ctl['start_frame']}")
                
    elif key == ord('g'):
        # グリッドの表示／非表示                   
        if len(ctl['key_data']) > 2 and ctl['key_data'][1:].isdigit():  
            # 'i<0|1><val>' :0=row,1=col
            rows, cols = ctl['grid_shape'] 
            rowcol = int(ctl['key_data'][1:2])
            val = int(ctl['key_data'][2:])
            if rowcol == 0 and val >= 2 : rows = val
            elif rowcol == 1 and val >= 2 : cols = val
            else: print("グリッド行数、列数は2以上の整数を指定してください")
            ctl['grid_shape'] = (rows, cols)
            ctl['key_data'] = ''            # キー入力データをクリア
        ctl['grid'] = True if ctl['grid'] is False else False

    elif key == ord('G'):
        # グリッドをシフトして表示                   
        if len(ctl['key_data']) > 3 and ctl['key_data'][1:].isdigit():
            # 'i<0|1><val1><val2>' :0=row,1=col
            rows, cols = ctl['grid_shift'] 
            rowcol = int(ctl['key_data'][1:2])
            val = int(ctl['key_data'][2:3])/int(ctl['key_data'][3:])
            if rowcol == 0 and val < 1.0 : rows = val
            elif rowcol == 1 and val < 1.0 : cols = val
            else: print("グリッドシフト割合は1.0以下の分数で指定してください")
            ctl['grid_shift'] = (rows, cols)
            ctl['key_data'] = ''            # キー入力データをクリア

    elif key >= ord('0') and key <= ord('8') \
        and (len(ctl['key_data']) == 0 and len(ctl['para_data']) == 0):
        # セクション番号を設定  
        Section_no = key - ord('0')
        if Section_no == 0: print(f"姿勢解析を開始します")
        else:  print(f"セクション番号を設定: {Section_no}")
        Completed = False
        Split_sec = 0
        Split_start = 0
        Step_counter = 0                    # セクション内の動作カウンターをリセット
        Nop_counter = 0                     # セクション内の動作カウンターをリセット
        Step_error = False                  # 不正な動作フラグ
        Section_color =  YELLOW             # セクションの色（黄色）BGR
        Alart_message = ''                  # アラートメッセージをリセット
        ctl['tag1_section'] = Section_no
        ctl['tag2_section'] = Section_no
        if Section_no == 0:
            Lap_start = Frame_counter       # ラップ開始時間を記録
            Lap_sec = 0.0
            ctl['tag1_section'] = 0         # tag登録用セクション番号
            ctl['tag2_section'] = 0         # tag登録用セクション番号
        else: 
            Split_start = Frame_counter
            if Lap_start > 0: Lap_start = Frame_counter
            if Section_no == 2 and ctl['key_inter'] != 0: 
                # セクション2の連打は動作カウンターを20に設定
                Step_counter = 20
        #
        if ctl['key_inter'] == 0: ctl['key_inter'] = int(time.time())  

    elif key == ord('9') and (len(ctl['key_data']) == 0 and len(ctl['para_data']) == 0):
        print(f"姿勢解析を停止します。")
        Lap_start = 0                       # ラップ開始時間をリセット 
        Split_start = 0                     # スプリット開始時間をリセット 
        Step_counter = 0                    # セクション内の動作カウンターをリセット              

    elif key == ord(' '):
        #  動作完了
        print(f"動作完了を設定")
        Completed = True
        if Section_no != 6 and Section_no != 8: # 「会」、「残身」はスプリットを計測
            Split_start = 0                     # スプリット開始時間をリセット
    
    elif key == ord('.') and len(ctl['para_data']) == 0: 
                                            # (.) フレームカウンターを2秒進める
        Frame_counter += int(Fps)*2     
        cap.set(cv2.CAP_PROP_POS_FRAMES, Frame_counter)
        print(f"フレーム={Frame_counter}")
        
    elif key == ord('>'):                   # (>) nフレーム進める
        if len(ctl['key_data']) > 1 and ctl['key_data'][1:].isdigit():
            # キー入力データの2文字目以降をフレーム数として設定
            ctl['skip_frames'] = int(ctl['key_data'][1:])
            ctl['key_data'] = ''            # キー入力データをクリア
        Frame_counter += ctl['skip_frames'] 
        cap.set(cv2.CAP_PROP_POS_FRAMES, Frame_counter)
        print(f"フレーム={Frame_counter}")
    
    elif key == ord(',') and len(ctl['para_data']) == 0:                   
        # (,) フレームカウンターを2秒戻す
        if Frame_counter > int(Fps)*2 :Frame_counter -= int(Fps)*2  
        else: Frame_counter = 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, Frame_counter)
        print(f"フレーム={Frame_counter}")
    
    elif key == ord('<'):                   
        # (<) nフレーム戻す
        if len(ctl['key_data']) > 1 and ctl['key_data'][1:].isdigit():
            # キー入力データの2文字目以降をフレーム数として設定
            ctl['skip_frames'] = int(ctl['key_data'][1:])
            ctl['key_data'] = ''            # キー入力データをクリア
        if Frame_counter > ctl['skip_frames'] :Frame_counter -= ctl['skip_frames']  
        else: Frame_counter = 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, Frame_counter)
        print(f"フレーム={Frame_counter}")

    elif key == ord('j'):
        # 指定フレームへジャンプ                   
        if len(ctl['key_data']) > 1 and ctl['key_data'][1:].isdigit():
            frame = int(ctl['key_data'][1:])
            if frame < 1: frame = 1
            if frame > ctl['frame_count']: frame = ctl['frame_count']
            Frame_counter = frame 
            cap.set(cv2.CAP_PROP_POS_FRAMES, Frame_counter)
            ctl['key_data'] = ''            # キー入力データをクリア
            print(f"フレーム={Frame_counter}")
                    
    elif key == ord('n') and Update_tracking:
        # 節の動作開始（次の節へ移行）を更新
        ctl['tag2_section'] += 1 
        Db.update_tracking_tag( 'tag2', ctl['tag2_section'] )  
        print(f"tag2登録(n): value={ctl['tag2_section']}")

    elif key == ord('b') and Update_tracking:
        # 節の動作完了を登録
        Db.update_tracking_tag( 'tag1', ctl['tag1_section'] )  
        print(f"tag1登録(b): value={ctl['tag1_section']}")
        ctl['tag1_section'] += 1 
        
    elif key == ord('a'):
        ctl['attention'] += 1
        mylog.log(INFO, f"!!Attention({ctl['attention']}):Section({Section_no:2d}), Frame_counter={Frame_counter}")
        print(f"アテンション({ctl['attention']}):Section({Section_no:2d}), Frame_counter={Frame_counter}")

    elif key == ord('I'):
        step = None
        if len(ctl['key_data']) > 1 and ctl['key_data'][1:].isdigit():
            # キー入力データの1文字目をステップ番号として設定
            step = int(ctl['key_data'][1:])
            ctl['key_data'] = ''

        tbl = CompleteAction_param
        if step is not None: tbl['step'] = step
        Db.insert_act_param(tbl)
        print(f"パラメータ:{tbl['frame']} step={tbl['step']},act={tbl['act']} テーブル登録完了")
        tbl = StartAction_param
        if step is not None: tbl['step'] = step
        Db.insert_act_param(tbl)
        print(f"パラメータ:{tbl['frame']} step={tbl['step']},act={tbl['act']} テーブル登録完了")
    
    elif key == ord('f') and len(ctl['para_data']) == 0:
        ctl['para_data'] = 'f'
    elif key == ord('.') and len(ctl['para_data']) > 0:
        ctl['para_data'] += '.'
    elif key == ord(',') and len(ctl['para_data']) > 0:
        ctl['para_data'] += ','
    elif key >= ord('0') and key <= ord('9') and len(ctl['para_data']) > 0:
        ctl['para_data'] += chr(key)

    elif key == ord('m') and len(ctl['para_data']) > 1:    # 現在使用中の解析パラメータを更新する
        # key_data='i[<val0>],[<val1>],[<val2>]...[,<valN>]'
        row = Section_no        
        tbl = CompleteAction_param if not Completed else StartAction_param  
        vals = ctl['para_data'][1:].split(',')
        for i in range(Stkp.len()):
            idx, _ = Stkp.get(i)
            if idx < len(vals) and vals[idx] != '':
                value = float(vals[idx]) if '.' in vals[idx] else int(vals[idx])
                tbl['param'][row][idx] = value
                print(f"パラメータ更新:[{row},{idx}]={value:.4f}")
        # キー入力データをクリア
        ctl['para_data'] = ''            
    
    elif key == ord('i'): 
        # 連打キー入力の開始
        if ctl['key_inter'] == 0:
            ctl['key_data'] = 'i'
            ctl['key_inter'] = int(time.time())  

    elif key >= ord('0') and key <= ord('9') and len(ctl['key_data']) > 0 and ctl['key_inter'] != 0:
        # キー（数字）入力データに追加
        ikey_num = key - ord('0')
        ctl['key_data'] += str(ikey_num)
        print(f"キー入力データ={ctl['key_data']}")
        
    elif key == ord('c'):
        if Alart_message != '':
            Section_color =  YELLOW             # セクションの色（黄色）BGR
            Alart_message = ''                  # アラートメッセージをリセット
        if Update_tracking and ctl['tag1_section'] > 0:
            Db.clear_tracking_tag('tag1')       # 節の動作完了をクリア
            print(f"tag1クリア")
        if Update_tracking and ctl['tag2_section'] > 0:
            Db.clear_tracking_tag('tag2')       # 節の動作開始（次の節へ移行）をクリア
            print(f"tag2クリア")
        if len(ctl['key_data']) > 0:
            ctl['key_data'] = ''                # キー入力データをクリア
            print(f"キー入力データクリア")
        if len(ctl['para_data']) > 0:
            ctl['para_data'] = ''                # キー入力データをクリア
            print(f"キー入力パラメータクリア")
        if ctl['start_frame'] != 0:              # 繰り返し再生の終了フレームをリセット
            ctl['start_frame'] = 0
            print(f"繰り返し再生の開始フレームをリセット")
        if ctl['stop_frame'] != 0:              # 繰り返し再生の終了フレームをリセット
            ctl['stop_frame'] = 0
            print(f"繰り返し再生の終了フレームをリセット")

        # グリッド表示をデフォルトにリセット
        ctl['grid_shape'] = (6, 6)              
        ctl['grid_shift'] = (0, 0)
        # フレーム間インターバルをデフォルトにリセット
        ctl['iwait'] = ctl['iwait_init']
        #
        print(f"{ctl}")
    elif key == ord('?'):
        print(f"{ctl}")
    #
    return True
    
#
# Main process to play video with form-analize by YOLOv8
#
def main(): 
    global Frame_counter, Section_no, Split_sec, Split_start, Lap_sec, Lap_start, Completed, Step_counter, Nop_counter
    global Step_error, Section_color, Alart_message
    global Tracking_only, Tracking_enabled, Update_tracking, Update_enabled
    global Window_size, Sample_frames, Sample_lag, V8_model, Debug_opt, Hybrid_model
    global StartAction_param, CompleteAction_param
    global Rect_area
    global InputPdf

    #
    # start of main
    #
    cam_id = None                                   # デフォルトのカメラID
    raw_video = False                               # 生画像を表示するオプション
    clip_video = False                              # 生画像をクリップしてファイルを作成
    manual_plot = False                             # 手動でプロット、姿勢解析するオプション
    nn_gru = False                                  # GRUによる姿勢解析オプション
    multi_frames = False                            # 2動画ファイルを重ねて再生するオプション
    mosaic = False                                  # モザイク処理を行うオプション
    guidance = True                                 # '-g'キー操作ガイダンス表示
    idir = PICT_PATH                                # 初期ディレクトリを指定
    ALL_TYPES = "*.*"                               # 動画ファイル名[*.mp4;*.avi;*.mov;*.mkv"]
    timestamp = datetime.now().strftime('%Y%m%d')
    filetypes = f"WIN_{timestamp}_*.mp4"            #'*WIN_YYYYmmdd_10_46_55_Pro.mp4'  # 動画ファイル名
    file_name = [None, None]                        # 動画ファイル名
    prePointsBuffer = RingBuffer(Window_size)       # 検出結果を保存するリングバッファ                           
    preResult = RingBuffer(2)                       # 前回の検出結果（補整済）を保存するリングバッファ                           
    preFrame = None                                 # 前回のフレームを保存する変数
    #
    case_name = None                                # ケース名（デフォルト：動画ファイル名）
    #
    # キー操作制御パラメータ
    keyCtl = {
        'iwait': 1,                                 # ウィンドウの更新間隔（ミリ秒）
        'iwait_init': 1,                            # ウィンドウの更新間隔初期値（ミリ秒）
        'istep': 16,                                # ステップカウント（ミリ秒）
        'istep_init': 32,                           # ステップカウント初期値（ミリ秒）
        'key_inter': 0,                             # 連打キー入力の経過時間（秒）
        'key_wait': 3,                              # 連打キー入力の有効期間（秒）
        'key_data':'',                              # キー入力データ（文字列）
        'para_data':'',                             # パラメータ入力データ（文字列）
        'tag1_section': 0,                          # タグ1のセクションカウンター 
        'tag2_section': 0,                          # タグ2のセクションカウンター
        'attention': 0,                             # アテンション出力カウンター
        'skip_frames': 8,                           # 早送り、巻き戻しフレーム数
        'videoWrite': False,                        # 動画ファイルへの書き込みフラグ
        'repeat': False,                            # 繰り返し再生フラグ
        'frame_count': 0,                           # 総フレーム数
        'start_frame': 0,                           # 繰り返し再生開始フレーム
        'stop_frame': 0,                            # 繰り返し再生終了フレーム
        'grid': False,                              # グリッド表示有無
        'grid_shape': (6, 6),                       # グリッド分割数(行,列)
        'grid_shift': (0, 0)                        # グリッド表示シフト量(行,列)
    }
    # print command line(arguments)
    args = sys.argv
    # コマンドライン引数を辞書に変換
    #args_dict = {arg: idx for idx, arg in enumerate(args)}

    cmdline = 'python '
    for arg in args:
        cmdline += f"{arg} "
    #    
    print(cmdline)    
    #
    # コマンド引数のチェック
    #
    ids = [id for id in args if id.isnumeric()]
    if len(ids) > 0:
        print(f"カメラID={ids[0]}")
        cam_id = int(ids[0])
    # オプションのチェック
    opts = [opt for opt in args if opt.startswith('-')]
    #
    if '-h' in opts:
        help()
        return
    
    if '-z' in opts:
        mosaic = True           # モザイク処理を行うオプション
    #
    if '-r' in opts:
        raw_video = True        # 生画像を表示するオプション
        
    if '-clip' in opts:
        clip_video = True
        raw_video = True        # 生画像を表示するオプション

    if '-multi' in opts:
        multi_frames = True     # 生画像を表示するオプション
        raw_video = True        # 生画像を表示するオプション
       
    if not raw_video and ('-m' in opts):            # 手動（OpenCV）で解析データをプロット、姿勢解析するオプション
        manual_plot = True
    
    model_pth = None
    input_key = Input_key
    input_dim = Num_input
    output_dim = Num_classes
    seq_frames = Num_frames
    _, _, _, section_dim, completed_dim = Hyper_parameters
    
    if not raw_video and ('-gru' in opts):          # GRUで姿勢解析するオプション
        nn_gru = True
        i = args.index('-gru')
        if len(args) > (i + 1) and args[i + 1][0] != '-' : model_pth = args[i +1]
        if model_pth is None:
            print("モデル名の指定がありません")
            return
        else:
            if os.path.isfile(model_pth) is False:
                print(f"[yoloApp]error:model-file({model_pth}) not found.")
                return
        # モデル名からパラメータを取得（kyudo_modelse_7-128-3-8-4.pth など）
        i = model_pth.rfind('_')
        if i > 0: 
            paramstr = model_pth[i+1:-3]
            #print(f"[yoloApp]debug:params = {paramstr}")
            params = paramstr.split('-')
            if len(params) == 3 and \
               params[0].isnumeric() and params[1].isnumeric() and params[2].isnumeric():
                input_key = int(params[0])
                seq_frames = int(params[1])
                output_dim = int(params[2])               
            if len(params) == 5 and \
               params[3].isnumeric() and params[4].isnumeric():
                section_dim = int(params[3])
                completed_dim = int(params[4])
        # モデル入力次元数を設定
        num_opts = [opt for opt in args if opt.startswith('inputkey')]
        if len(num_opts) > 0: 
            # inputdim=<no>の解析
            params = num_opts[0].split('=')
            if len(params) == 2 and params[1].isnumeric():
                input_key = int(params[1])
                if input_key < 6 or input_key > 8:
                    print("入力次元数は6～8の範囲で指定してください")
                    return
        # 特徴量データフレームのインスタンス作成
        InputPdf = FeaturePdf(input_key, seq_frames)
        input_dim = InputPdf.input_dim
        # ゼロデータで初期化
        InputPdf.set_zero_previous_pdf(0.0)

    # モデルデータ出力のケース数を設定
    num_opts = [opt for opt in args if opt.startswith('classes')]
    if len(num_opts) > 0: 
        # classes=<no>の解析
        params = num_opts[0].split('=')
        if len(params) == 2 and params[1].isnumeric():
            output_dim = int(params[1])
            if output_dim != 3 and output_dim != 19:
                print("クラス数は3か19のどちらかで指定してください")
                return
    
    if not raw_video and ( '-t' in opts) :
        manual_plot = True
        Tracking_only = True    # トラッキングのみを行うオプション
        # トラッキングデータリストのインスタンス作成
        InputPdf = FeaturePdf()
        i = args.index('-t')
    if not raw_video and ( '-u' in opts) :
        manual_plot = True
        Update_tracking = True  # トラッキングを更新するオプション
        i = args.index('-u')
    if Tracking_only or Update_tracking:
        if i + 1 < len(args) and (not args[i + 1].startswith('-')):
            case_name = args[i + 1]  # ケース名を取得
            if len(case_name) == 0:
                print("ケース名の指定がありません")
                return
            Db.case_name = case_name   
            fps, _ = Db.get_fps()
            if Update_tracking and fps is None:
                print(f"> '{case_name}' not found in frame_info table.")
                return
        else:
            print("ケース名の指定がありません")
            return
    #
    # トラッキングデータのケース名を設定
    if Tracking_only: 
        fps, x = Db.get_fps()
        if fps is not None:
            print(f"> '{case_name}' already registered. Are you sure?[y/n].")
            ans = input('>>')
            if ans != 'y': Tracking_only = False
    #
    # YOLOv8モデルファイル指定（デフォルトは'v8s'）
    if '-V8n' in opts:
        V8_model = 'v8n' # YOLOv8nモデルを使用 

    # サンプリングフレーム数を取得
    opt_val  = [opt for opt in opts if opt.startswith('-f')]
    if len(opt_val) > 0:
        if len(opt_val[0]) > 2 :
            vals = opt_val[0][2:].split('.')
            if vals[0].isnumeric(): 
                Sample_frames = int(vals[0])
            if len(vals) > 1 and vals[1].isnumeric(): 
                Sample_lag = int(vals[1])
    #print(f"frames={Sample_frames}, lag={Sample_lag}")
    #
    if Sample_lag > 0:
        param_nm = f"{Sample_frames}.{Sample_lag}-{V8_model[-1:]}"
    else:               
        param_nm = f"{Sample_frames}-{V8_model[-1:]}"
    
    # 段レベル(step)を取得
    step_no = 1
    opt_val  = [opt for opt in opts if opt.startswith('-s')]
    if len(opt_val) > 0:
        if len(opt_val[0]) > 2 and opt_val[0][2:].isnumeric():
            step_no = int(opt_val[0][2:])
            if nn_gru:
                Hybrid_model = True
    #
    if '-I' in opts:            # 動作開始解析パラメータの初期登録
        param_nms = []
        i = args.index('-I')
        if i + 1 < len(args) and (not args[i + 1].startswith('-')):
            param_nms.append( args[i + 1] )  # パラメータテーブルframe名を取得
        else:
            param_nms = list(InitAction_param_nms)
        for nm in param_nms:
            _,tbl = get_action_param(CompleteAction_params, nm, step_no)
            if tbl is None:
                print(f"パラメータ名:{nm},ステップ:{step_no} は不正です")
                continue
            Db.insert_act_param(tbl)
            print(f"パラメータ:{nm} step={tbl['step']},act={tbl['act']} テーブル登録完了")
            _,tbl = get_action_param(StartAction_params, nm, step_no)
            Db.insert_act_param(tbl)
            print(f"パラメータ:{nm} step={tbl['step']},act={tbl['act']} テーブル登録完了")
        return

    if manual_plot:
        # 動作解析パラメータをDBからロードする
        CompleteAction_param['frame'] = param_nm
        CompleteAction_param['step'] = step_no
        if Db.load_act_param(CompleteAction_param) == 0:    
            print(f"{param_nm}の動作完了解析パラメータが登録されていません")
            return
        StartAction_param['frame'] = param_nm
        StartAction_param['step'] = step_no
        if Db.load_act_param(StartAction_param) == 0:    
            print(f"{param_nm}の動作開始解析パラメータが登録されていません")
            return

    # 異常動作解析をスキップするパラメータを無効化するためのパラメータ変更オプションに変換する
    opt_vals  = [opt for opt in opts if opt.startswith('-S')]
    for opt_val in opt_vals:
        if opt_val[2:].isnumeric():
            # 異常動作解析をスキップするセクション番号を取得
            section = int(opt_val[2:])
            if not section in [3, 5]:
                print(f"有効なセクション番号(3 or 5)を指定してください: {section}")
                return
            else:
                idx = 7 if section == 3 else 6      # セクション番号に応じてインデックスを設定
                val = 1.0 if section == 3 else 1.0  # セクション番号に応じて値を設定
                opt_string = f"-P({section},{idx})={val}"
                print(f"異常動作解析をスキップするパラメータ更新に変換しました：{opt_string}")
                opts.append(opt_string)
        else:
            print(f"無効なセクション番号が指定されました: {opt_val}")
            return
        
    # 動作解析パラメータの変更
    opt_vals  = [opt for opt in opts if opt.startswith('-p') or opt.startswith('-P')]
    for opt_val in opt_vals:
        action = None
        fidx = -1
        i = opt_val.find('-p')
        if i != -1: 
            action = 'Start'
        else: 
            action = 'Complete'
        opt_str = opt_val[2:].split('=')
        if len(opt_str) > 1 and opt_str[1][0].isnumeric():
            val = float(opt_str[1][0:])
        opt_str = opt_str[0].split(',')
        if len(opt_str) > 1 and opt_str[0][1:].isnumeric() and opt_str[1][:-1].isnumeric():
            section = int(opt_str[0][1:])
            idx = int(opt_str[1][:-1])
            if section < 0 or section > 9 and idx < 0 or idx > 7:
                print(f"セクション番号またはインデックスは範囲で指定してください: {section}, {idx}")
                return
            else:
                # セクション番号とインデックスで指定されたパラメータを更新
                if action == 'Start':
                    StartAction_param['param'][section][idx] = val
                else:
                    CompleteAction_param['param'][section][idx] = val  
                print(f"{action}[セクション番号={section}, インデックス={idx}]の値={val}に更新しました")
        else:
            print("セクション番号とインデックスを指定してください: -p'([0-9],[0-7])=値'")
            return
                
    # ウィンドウサイズを取得
    opt_val  = [opt for opt in opts if opt.startswith('-W')]
    if len(opt_val) > 0:
        if len(opt_val[0]) > 2 and opt_val[0][2:].isnumeric():
            Window_size = int(opt_val[0][2:])  
    
    # キーオペレーションのガイダンス表示
    color = 'G'
    guid_color = GREEN
    guid_option = 3
    guid_opt = [opt for opt in opts if opt.startswith('-g')]
    if len(guid_opt) > 0 and guid_opt[0] != '-gru':
        #guidance = True 
        # ガイダンスの表示レベルを取得
        if len(guid_opt[0]) > 2 and guid_opt[0][2:3].isalnum():
            guid_option = int(guid_opt[0][2:3])
            if guid_option == 0: guidance = False
        else: guid_option = 2
        # ガイダンスの色を取得
        if len(guid_opt[0]) > 3: color = guid_opt[0][3].upper()
        if color == 'W': guid_color = WHITE
        elif color == 'Y': guid_color = YELLOW
        elif color == 'B': guid_color = BLACK
        else: guid_color = GREEN
        
    # YOLOV8のログレベルを設定
    if '-v' in opts:
        logger.disabled = False  # ログ出力を有効化
    
    # ログファイル出力のログレベルを設定
    dbg_opt = [opt for opt in opts if opt.startswith('-d')]
    if len(dbg_opt) > 0 and dbg_opt[0][2:].isnumeric(): Debug_opt = int(dbg_opt[0][2:])
    
    mylog_level = ERROR  # デフォルトはERROR
    if Debug_opt != 0: 
        mylog_level = INFO if Debug_opt < 3 else DEBUG 
    mylog.setLevel(mylog_level)  
    
    # 映像ソースの選択   
    if '-a' in opts:
        # ファイル選択のファイルタイプを設定        
        filetypes = ALL_TYPES
    
    cap = [None, None] 
    if cam_id is not None:
        # カメラから映像を取得  
        cap[0] = cv2.VideoCapture(cam_id) # カメラIDを指定
    else:
        # 動画ファイルを選択する
        files = 2 if multi_frames else 1
        for i in range( files ):
            file_name[i] = filedialog.askopenfilename(
                title = "動画ファイルを選択してください",
                filetypes = [("Video files", filetypes)],
                initialdir = idir
            )
            if not file_name[i]:
                print("動画ファイルの選択がキャンセルされました")
                if cap[0] is not None: cap[0].release()
                return
            
            print(f"[main]:入力ファイル：{file_name[i]}")
            cap[i] = cv2.VideoCapture(file_name[i])  # 動画ファイルのパスを指定
            
    # 動画ファイルが開けない場合のエラーハンドリング
    if not cap[0].isOpened():
        print("カメラor動画ファイルが見つかりません")
        if cap[1] is not None: cap[1].release()
        return    
    #
    # 先頭フレームを読み込み
    #
    ret, frame = cap[0].read()
    if not ret:
        print("動画ファイルの読み込みに失敗しました")
        cap[0].release()
        if cap[1] is not None: cap[1].release()
        return
    # フレームのサイズを取得
    frame_height = int(cap[0].get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_width = int(cap[0].get(cv2.CAP_PROP_FRAME_WIDTH)) 
    keyCtl['frame_count'] = int(cap[0].get(cv2.CAP_PROP_FRAME_COUNT))
    # フレームレートを取得
    Fps = cap[0].get(cv2.CAP_PROP_FPS)       
    #
    if multi_frames:
        if cap[1].isOpened():
            # 先頭フレームを読み込み
            ret, frame1 = cap[1].read()
            if not ret:
                print("動画ファイルの読み込みに失敗しました")
                cap[1].release()
                cap[1] = None
        else:
            print("動画ファイルが見つかりません")
            cap[1].release()
            cap[1] = None

    if Tracking_only:
        # トラッキングデータ、姿勢解析データの出力先CSVファイルを開く
        Db.open_csv()
        # トラッキングデータの情報テーブルに登録 
        Db.insert_frame_info( [file_name[0], Fps, frame_height, frame_width, Db.csvpath1] )     
    #---------------------------------------------------------------------  
    # クリッピング領域指定
    #---------------------------------------------------------------------  
    rectAreas:Rect = []
    if clip_video:
        while( True ): 
            rectAreas = clip_process( frame )
            if rectAreas is  None: return           # 'q'押下で終了
            elif len(rectAreas) > 0:                # 'c'押下で処理継続
                # クリッピング領域座標の取得
                rect = rectAreas.pop(0)
                frame_width, frame_height = rect.width_height()
                frame_x = rect.x[0]
                frame_y = rect.y[0]
                break
    #------------------------------------------------------------------------
    # 映像出力ファイルの設定
    #------------------------------------------------------------------------
    keyCtl['videoWrite'] = False
    out_file = ''
    if ('-w' in opts) or clip_video:
        if file_name[0] is None:
            out_file = f"{idir}YOLO_{timestamp}_{datetime.now().strftime('%H%M%S')}.mp4"
        else:
            base_name = os.path.basename(file_name[0])
            out_file = f"{idir}_{base_name}"

        print(f"[main]:出力ファイル：{out_file}: {frame_width}x{frame_height}")
        #print(f"os.sep: {os.sep}")
    #
    if not raw_video:
        #------------------------------------------------------------------------
        # NNモデルのインスタンス生成
        #------------------------------------------------------------------------
        print(f"YOLO{V8_model} Pose Detectionを開始します")
        print(f"YOLOv8 ログレベル={mylog_level}")
        print(f"解析パラメータ={param_nm}, レベル={step_no}, モデル={V8_model}, 出力クラス区分数: {output_dim}")        
        mylog.log(INFO,f"YOLO{V8_model} Pose Detectionを開始します")
                
        # YOLOv8-poseモデルの読み込み（事前学習済みモデル）
        model = YOLO(f"yolo{V8_model}-pose.pt")  # 軽量モデル。他にも'yolov8s-pose.pt'などあり
        model.info()  # モデル情報を表示
        
        if nn_gru:
            print("GRUによる姿勢解析を有効化します")
            mylog.log(INFO, "GRUによる姿勢解析を有効化します")
            print(f"input_dim={input_dim}")            
            # KyudoGRUモデルの読み込み（事前学習済みモデル）
            parts =model_pth.split('_') 
            if 'modelse' in parts:
                model_gru = KyudoGRUs( input_size = input_dim, output_size = output_dim,
                                section_embed_dim = section_dim,
                                completed_embed_dim = completed_dim )
            elif 'modelme' in parts:
                model_gru = KyudoGRUm( input_size = input_dim, output_size = output_dim,
                                hidden_size=32,
                                section_embed_dim = section_dim,
                                completed_embed_dim = completed_dim )
            else:
                print(f"非対応のモデルです。")
                return   
            model_gru.to( get_device() )
            model_gru.load_state_dict( torch.load(model_pth, map_location = get_device()) )

            print(f"model_gru={model_gru}")
            mylog.log(INFO,f"model_gru={model_gru}")            
            print(f"[main]:model loaded from {model_pth}")
            mylog.log(INFO,f"model loaded from {model_pth}")
    #    
    sample_seconds = 1.0 / Fps * Sample_frames  # サンプリング秒数
    
    mylog.log(INFO, f"[main]:起動パラメータ情報:WindowSize={Window_size}:case_name={case_name}")
    print(f"[main]:起動パラメータ情報:WindowSize={Window_size}:case_name={case_name}")
    mylog.log(INFO, f"[main]:フレーム情報: {file_name[0]}: {frame_width}x{frame_height}, Fps={Fps:.2f}")
    print(f"[main]:フレーム情報: {file_name[0]}: {frame_width}x{frame_height}, Fps={Fps:.2f}")
        
    if not raw_video:
        mylog.log(INFO, f"[main]:サンプリング: {Sample_frames}フレーム({sample_seconds:.3f} sec.), Lag={Sample_lag}")
        print(f"[main]:サンプリング:Fps={Fps:.2f}, Interval={Sample_frames}フレーム({sample_seconds:.3f}sec.), Lag={Sample_lag}")    
    
    if nn_gru:
        mylog.log(INFO, f"[main]:入力次元数: {input_dim}, シーケンスフレーム数： {seq_frames}, 出力クラス区分数: {output_dim}")
        print(f"[main]:入力次元数: {input_dim}, シーケンスフレーム数： {seq_frames}, 出力クラス区分数: {output_dim}")
    
    if Tracking_only or Update_tracking:
        mylog.log(INFO, f"[main]:出力クラス区分数: {output_dim}")
        print(f"[main]:出力クラス区分数: {output_dim}")
    #   
    Frame_counter = 1                   # フレームカウンターの初期化
    if raw_video is True:
        keyCtl['iwait_init'] = int(1/Fps * 1000)  # 生画像を表示する場合、FPS値からキー入力待ち時間を設定
    else: 
        keyCtl['iwait_init'] = 1
    # ウィンドウの更新間隔を設定
    if '--' in opts:
        # '--'オプションが指定されている場合、ウィンドウの更新間隔を0に設定（起動直後にPAUSE状態にする）
        keyCtl['iwait'] = 0
    else:
        keyCtl['iwait'] = keyCtl['iwait_init']
    #        
    print(f"[main]:iwait={keyCtl['iwait']}")
    mylog.log(INFO, f"[main]:iwait={keyCtl['iwait']}")
    if manual_plot:
        print_param(CompleteAction_param)
        print_param(StartAction_param)
    #
    #------------------------------------------------------------------------
    #  メインのループ処理 
    #------------------------------------------------------------------------
    actStr = ''
    while True:
        # 次のフレームの読み込み
        ret, frame = cap[0].read()
        if not ret:
            if keyCtl['repeat']:
                cap[0].release()
                cap[0] = cv2.VideoCapture(file_name[0])  # 動画ファイルのパスを指定
                Frame_counter = 0
                continue
            print(f"[main]: #end of video data. frame={Frame_counter}")
            break
        #
        Frame_counter += 1  # フレームカウンターをインクリメント
        if raw_video is True:
            if clip_video:
                # クリッピング処理
                annotated_frame = frame[ frame_y:frame_y + frame_height, frame_x:frame_x + frame_width ]
                for rect in rectAreas:
                    # モザイク処理
                    w, h = rect.width_height()
                    annotated_frame = mosaic_area( annotated_frame, \
                                                   (rect.y[0] - frame_y), (rect.x[0] - frame_x), h, w )
            else:
                if multi_frames and cap[1] is not None:
                    # 画面を重ねて表示
                    ret, frame1 = cap[1].read()
                    if ret is True: 
                        frame = multi_frame_display(frame, frame1)
                # 生画像を表示する場合
                annotated_frame = frame
        else:
            # フレームのコントラストと明るさを調整
            #frame = adjust_frame_contrast(frame, alpha=1.8, beta=20)  # コントラストと明るさを調整
            #
            # YOLOで骨格検出
            results = model.predict(frame)
            if len(results) == 0 or len(results[0].keypoints) == 0:
                mylog.log(INFO, "[main]検出結果がありません")
                continue
                        
            # 面積最大のボックスを取得、信頼度の低いキーポイント座標データは前回採用データで置き換える
            result = results[0]
            try:
                myResult = MyResult(result)
            except BoundaryBoxError as e:
                print(f"フレーム({Frame_counter}):{e}")
                mylog.log(INFO, f"[main]:フレーム({Frame_counter}):検出結果の描画をスキップ")
                preResult.clear()
                annotated_frame = frame
            else:
                '''
                if preResult.len() > 1 and Section_no > 1 and Section_no < 9:
                    # 直近の検出結果がある場合、信頼度の低いキーポイント座標データは前回採用データで置き換える
                    myResult.adjust_points(preResult.get().points)
                '''
                # 補正用の直近リングバッファに保存
                preResult.append( myResult )
                
                # キーポイントの過去サンプリング位置からの変位ベクトルの長さ、角度を計算する    
                myResult.calc_arrow_length_angles(prePointsBuffer)

                # {Sample_frames}フレーム毎に検出結果を保存
                if (Frame_counter%Sample_frames) == 0 or Frame_counter < Sample_frames:
                    # 検出結果（補正済）を保存 
                    prePointsBuffer.append( myResult )                        
                    mylog.log(DEBUG, f"[main]: {datetime.now().strftime('%H-%M-%S')}:検出結果保存: {type(results)}, {len(results)}個の結果,"\
                                + f"フレーム={Frame_counter}, buffer_length={prePointsBuffer.length}")

                # 検出結果をフレームに描画
                if manual_plot:
                    # 生画像に手動（OpenCV）で描画
                    # 射法八節の姿勢解析を実行
                    if Tracking_only or Update_tracking: 
                        Db.frame_no = Frame_counter     # トラッキングデータのフレーム番号を設定  
                    
                    annotated_frame = frame
                    if prePointsBuffer.len() > 1:
                        annotated_frame = plot( myResult, frame, output_dim, \
                                                nn_gru, model_gru if nn_gru else None)
                        if annotated_frame is None and preFrame is not None:  # 前回のフレームを描画
                            annotated_frame = preFrame
                            mylog.log(INFO, "[main]: 前回フレームを描画")
                        elif mosaic:
                            # モザイク処理
                            areas = get_mosaic_areas(myResult)
                            for rect in areas:
                                annotated_frame = mosaic_area( annotated_frame, \
                                                    rect[0], rect[1], rect[2], rect[3] )

                else:
                    # YOLOv8のplot関数を使用してフレームに描画  
                    # 　kpt_line=False： キーポイントのマークのみを描画）
                    annotated_frame = myResult.result.plot(boxes=True, labels=False, kpt_line=True, kpt_radius=3)
                    #annotated_frame = plot( myResult )
        #        
        preFrame = annotated_frame.copy()  # 前回のフレームへ保存
        #
        if keyCtl['grid']:
            # グリッドを表示        
            draw_grid(annotated_frame, keyCtl['grid_shape'], keyCtl['grid_shift'], GRAY, 1)
        #
        if keyCtl['videoWrite']:
            # 出力ファイルに書き込み
            Cv2Video.write(annotated_frame)
        
        # ウィンドウに操作ガイダンスを表示
        if guidance is True:
            # キー操作モード
            pos, str = edit_key_mode(frame_height, keyCtl['iwait'], out_file, keyCtl['videoWrite'],\
                                    raw_video, clip_video, keyCtl['repeat'])
            str = f"mode  : {str}"
            x, y = pos
            size, base = cv2.getTextSize(str,cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2 )
            w, h = size
            model_color = GRAY if keyCtl['key_inter'] > 0 else YELLOW
            cv2.putText(annotated_frame, str, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, model_color, 2)
            # キー操作ガイダンス
            str = edit_key_ope(out_file, raw_video, clip_video)
            pos = (x + w + 40, y)
            cv2.putText(annotated_frame, str, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, guid_color, 2)            
            
            # フレームカウンター、インターバル情報
            if guid_option > 1:
                pos = (x, y - 20)
                str = f"frame :{Frame_counter:4d}   interval : {keyCtl['iwait']}ms."
                cv2.putText(annotated_frame, str, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 1)            
            
            # パラメータ情報       
            if manual_plot and guid_option > 2:
                pos = (x, y - 45)
                comp = 1 if Completed else 0
                str = f"param({Section_no}-{comp}-{Step_counter:2d}) : "
                if not nn_gru: 
                    for i in  range( Stkp.len() ):
                        no, val = Stkp.get(i)
                        if i > 0: str += ", "
                        str += f"{no}={val}"
                else:
                    if Action != 0: actStr = f"Action={Action}"
                    str += actStr
                cv2.putText(annotated_frame, str, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)            
        #    
        # ウィンドウに表示する   
        cv2.imshow('YOLO Pose Detection', annotated_frame)
        #print(f"({Frame_counter})")
        #キー入力をチェックするする
        key = cv2.waitKey(keyCtl['iwait']) & 0xFF
        if key == -1: 
            # キー入力がない場合は次のフレームへ
            continue        
        #
        # キー入力に応じて処理を実行
        #
        if key_ope(key, keyCtl, annotated_frame, cap[0], idir, out_file, raw_video, clip_video) == False:
            # キー操作が終了（'q'）で、ループを抜ける
            print("[main]:Interrapted by 'q'")
            break
        #
        # 繰り返し再生の処理
        if keyCtl['repeat'] and keyCtl['stop_frame'] != 0 and Frame_counter >= keyCtl['stop_frame']:
            # 繰り返し再生の開始フレームに戻す
            Frame_counter = keyCtl['start_frame'] - 1           
            cap[0].set(cv2.CAP_PROP_POS_FRAMES, Frame_counter)
    #
    if Tracking_enabled:
        Db.update_frame_info('stop_frame', Frame_counter)   # 停止フレーム番号
    # リソースの解放
    if Tracking_only: 
        Db.csvfile1.close()
        Db.csvfile2.close()
    Db.close() 
    cap[0].release()
    if multi_frames and cap[1] is not None: cap[1].release()
    cv2.destroyAllWindows()
    print("[main]:YOLOv8 terminated.")
#
if __name__ == "__main__":
    print(datetime.now())
    print(os.getcwd())
    #
    ultralytics.checks()  # YOLOv8のチェックを実行
    if not os.path.exists(f'yolo{V8_model}-pose.pt'):
        print("YOLOv8-poseモデルが見つかりません。ダウンロードしてください。")
        exit(1)
    main()
# eof