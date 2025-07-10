import cv2
from ultralytics import YOLO
import ultralytics

import tkinter.filedialog as filedialog
import sys
import os
from datetime import datetime
import time

import numpy as np
import math

# local package
from  env import * 
from mysqlite3.mysqlite3 import MyDb

# Ultralytics YOLOv8とアプリ専用のロガー設定
import logging
DEBUG = logging.DEBUG
INFO = logging.INFO
ERROR = logging.ERROR

logger = logging.getLogger('ultralytics')
logger.disabled = True  # ログ出力を無効化

mylog = logging.getLogger(__name__)
filehandler = logging.FileHandler('yolo.log', mode='w')  # ログファイルの設定
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # ログフォーマットの設定
formatter = logging.Formatter('%(message)s')  # ログフォーマットの設定
filehandler.setFormatter(formatter)  # フォーマッタをハンドラに設定
mylog.addHandler(filehandler)  # ログハンドラを追加

#　アプリケーションのグローバル変数の定義
Frame_counter:int = 0   # フレームカウンター
Fps:float = 30          # フレームレート
Section_no:int = 0      # セクション番号
Split_sec:int = 0       # スプリット秒
Split_start:int = 0     # スプリットベース時間
Lap_sec:int = 0         # ラップ秒 
Lap_start:int = 0       # ラップベース時間
Completed:bool = False  # 完了フラグ
Step_counter:int = 0    # セクション内のステップカウンター

# カメラの位置を定義
Camera_position:int = 0 # カメラの位置（0:未定義、1:前面、2:右側面、3:上面）
CameraPos:str = ''      # カメラの位置名
CameraPos_name = ['', 'Front-side', 'Right-side', 'Upper-side']  # カメラの位置

# トラッキングのみフラグ
Tracking_only:bool = False # トラッキングのみフラグ
Tracking_on:bool = False   # トラッキングオンフラグ

# データベースのインスタンスを作成
Db = MyDb(DB_PATH)  
Db.mode = 'csv'

#
# YOLOv8とOpenPoseの組み合わせ例（Ultralytics YOLOv8 + YOLOv8-poseモデル利用）
# このコードは、YOLOv8を使用してカメラまたは動画ファイルから骨格検出を行うものです。
# YOLOv8-poseモデルは、Ultralyticsの事前学習済みモデルを使用しています。
def help():
    print(" --- command ---")
    print(" python ./src/yolo.py [<Camera-ID>] [-h] [-v] [-d<level>[-a] [-r|[-m|-t <case_name>]] [-w]")
    print(" --- option ---")
    print(" -h(elp)")
    print(" -v(erborse)")
    print(" -d(ebug-level)<0-2>")
    print(" -a(ll-file-types)")
    print(" -m(anual-plot::dont use YOLO plot)")
    print(" -r(aw-image)")
    print(" -t(racking::create-csvfile)")
    print(" -w(rite-analized-file)")
    print(" --- key operation ---")
    print(" s :スナップショットファイルの作成")
    print(" w :出力ファイルへの書き込み開始／停止")
    print(" t :トラッキング開始／停止（'0'->'t'の順")
    print(" a :ログファイルへのアテンションメッセージ出力")
    print(" 0 :ラップ開始")
    print(" 1-8:節の開始")
    print(" .(>):スキップ")
    print(" ,(<):巻き戻し")
    print(" p :一時停止／再開")
    print(" q :処理の終了")
    print(" --- example ---")
    print("例)当日作成の動画ファイルから選択 : python yoloApp.py")  
    print("例)全ての動画ファイルタイプから選択: python yoloApp.py -a")  
    print("例)カメラID 1 を指定             : python yoloApp.py 1")  
    return

#
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
    mylog.log(DEBUG, f"near={ans} : p1=({p1[0]},{p1[1]}), p2=({p2[0]}, {p2[1]}), threshold={threshold}")
    return ans
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
            mylog.log(INFO, f"[get_max_box]: boxid={i}, conf={result.boxes.conf[i].item():.2f}  skip....")
            continue  # 信頼度が低いボックスは無視
        x, y, w, h = map(int, boxes.xywh[i])
        area = np.append(area, w * h)                   # 面積を計算して追加
    if len(area) > 0:
        # 最大のボックスのインデックスを取得
        max_box_no = area.argmax()           
        # 最大のボックスの情報を表示
        # インデックスは0から始まるため、1を加算
        conf = result.boxes.conf[max_box_no].item()  # 最大ボックスの信頼度を取得    
        max_box_no += 1  
        mylog.log(DEBUG, f"[get_max_box]: max_box_no={max_box_no}, conf={conf}:.2f, area:{area}, xywh:{boxes.xywh[max_box_no-1]}")             
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
    length_h, x = keyPoints.norm('right_hip', 'left_hip')                   # 右腰と左腰のベクトルの長さと角度を計算

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

    def len(self):
        return self.length
#
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

class MyResult(Keypoint):
    def __init__(self, result, boxid=None):
        if boxid is None:
            boxno = get_max_box(result)
            if boxno == 0: raise BoundaryBoxError('Target boundary-box can not be found.')
            else: boxid = boxno - 1
        super().__init__(result, boxid)
        self.result = result
        self.confs = result.keypoints.conf[boxid].numpy()
        self.points = result.keypoints.xy[boxid].numpy()
        # 補正対象のキーポイントの信頼度閾値テーブル
        # 'nose', 'left_eye', 'right_eye', 'left_ear', 
        # 'right_ear','left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 
        #  'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
        # 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'}
        self.limit_val = [ 
            0,    0,    0,   0,
            0,   0,    0,    0,   0, 
            0, 0.92, 0,   0,
            0,    0,    0,   0]

    def adjust_points(self, prePoints):
        for key, idx in Kn2idx.items():
            if self.limit_val[idx] != 0 and self.confs[idx] < self.limit_val[idx]:
                self.points[idx] = prePoints[idx]           
                mylog.log(INFO, f"[adjust_points]:フレーム={Frame_counter}, Key={key},"\
                              + f" conf={self.confs[idx]:.3f}({self.limit_val[idx]:.3f})") 
        
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
###
###
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
# 解析結果をトラッキングする関数              
def tracking_result( myResult, arrows):
    keypoints = myResult.keypoints                        # キーポイントリスト(Tensor)
    boxes = myResult.boxes    
    box_id = myResult.boxid
    
    arrow = arrows[0]                                   # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
    box_h = boxes.xywh[box_id][3].item()                # 解析対象のボックスの高さ
    box_w = boxes.xywh[box_id][2].item()                # 解析対象のボックスの幅
    box_conf = boxes.conf[box_id].item()                # 解析対象の信頼度

    keyPoints = myResult                                # キーポイントのデータ解析インスタンス
    eyes_len, x = keyPoints.norm('right_eye', 'left_eye')            # 右目と左目のベクトルの長さと角度を計算       
    shds_len, x = keyPoints.norm('right_shoulder', 'left_shoulder')  # 右目と左目のベクトルの長さと角度を計算       
    
    for name, idx in Kn2idx.items():
        key_id = idx
        if idx > 12: continue
        
        key_name = name
        x = keypoints.xy[box_id][idx][0].item()         # キーポイントX座標
        y = keypoints.xy[box_id][idx][1].item()         # キーポイントY座標
        xy_conf = keypoints.conf[box_id][idx].item()    # キーポイントの信頼度
        norm, angle = arrow[idx]                        # 移動ベクトルの長さと角度
        ratio = norm/box_h                              # ボックスの高さに対する比率
                
        data_list = [key_id, key_name, box_id, box_w, box_h, box_conf, x, y, xy_conf, norm, ratio, angle, eyes_len, shds_len]
        
        Db.insert_tracking_data( data_list )  # データベースに挿入
    
    if Db.mode == 'csv': Db.csvfile.flush()
    else:    Db.commit()
    
    return
#
# 次のセクションが開始したかどうかを判定する関数
#
def section_started(section_no, myResult, arrows):
    global Step_counter

#    keyPoints = Keypoint(result, ibox)           # キーポイントのデータ解析インスタンス
    keyPoints = myResult           # キーポイントのデータ解析インスタンス
    ibox = myResult.boxid
    
    thsd = Threshold(keyPoints.block_height)     # バウンディングボックスの高さを基準に閾値設定インスタンス
    
    arrow = arrows[0]                            # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
    
    normR, anglR = arrow[Kn2idx['right_wrist']]                     # 右手首の移動ベクトルの長さと角度
    normL, anglL = arrow[Kn2idx['left_wrist']]                      # 左手首の移動ベクトルの長さと角度
    normS, x = arrow[Kn2idx['right_shoulder']]                      # 右肩の移動ベクトルの長さと角度
    xy_wristR = keyPoints.xy('right_wrist')                         # 右手首の座標
    
    started = False
    
    conf = keyPoints.conf('right_wrist')                             # 右手首の座標の信頼度
    if conf < 0.90 :
        # 右手首の信頼度が低い場合は開始しない
        mylog.log(INFO, f"started ({section_no}): roght_wrist-conf={conf:.2f}  skip....")
        return started

    mylog.log(INFO, f"started ({section_no}):  boxid={ibox}, H={int(thsd.block_height)}:  wristR=[{int(xy_wristR[0])}, {int(xy_wristR[1])}],"\
            + f"    normR={int(normR)}({thsd.ratio(normR):.3f}), anglR={int(anglR)}°, conf={conf:.2f}, counter={Step_counter}")
    #
    # 次の節への移行条件を判定
    #
    # 0-Start  ->  1-Asi-bumi
    if section_no == 0:    
        lenS, x = keyPoints.norm('left_shoulder', 'right_shoulder')          # 右肩と左肩のベクトルの長さと角度を計算
        mylog.log(INFO, f">>>   lenS={int(lenS)}({thsd.ratio(lenS):.3f}), normS={(int(normS))}({thsd.ratio(normS):.3f})")
        mylog.log(INFO, f">>>   [ lenS < {int(thsd(0.15))} and normS > {int(thsd(0.14))} ]")

        if lenS < thsd(0.120) and  normS > thsd(0.14):
            # 右肩と左肩のベクトルの長さが80未満、右肩の移動ベクトルの長さが50以上の場合（射位へ移動）
            started = True
    
    # 1-Asi-bumi  ->  2-Dou-zukuri        
    elif section_no == 1:  
        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.080))} ]")

        if normR > thsd(0.080):
            # 右手首と左手首の移動ベクトルの長さが50以上の場合（矢つがえ動作開始）
            Step_counter += 1
            if Step_counter == 2: started = True
    
    # 2-Dou-zukuri  ->  3-Yu-gamae        
    elif section_no == 2:  
        lenY, x = keyPoints.norm('right_eye', 'left_eye')         # 右目と左目のベクトルの長さと角度を計算       
        mylog.log(INFO, f">>>   lenY={int(lenY)}({thsd.ratio(lenY):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.035))} and lenY > {int(thsd(0.030))} ]")

        if normR > thsd(0.035)  and lenY > thsd(0.030):
            # 右手首の移動ベクトルの長さが10以上の場合（取りかけ動作開始）
            Step_counter += 1
            if Step_counter == 4: started = True
        else: Step_counter = 0
    
    # 3-Yu-gamae  ->  4-Uti-okosshi        
    elif section_no == 3:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.034))} and normL > {int(thsd(0.034))} ]")

        if normR > thsd(0.034) and normL > thsd(0.034):
            # 右手首と左手首の移動ベクトルの長さが10以上の場合（打起し動作開始）
            Step_counter += 1
            if Step_counter == 6:   started = True
    
    # 4-Uti-okosshi  ->  5-Hiki-wake        
    elif section_no == 4:  
        pre_arrow = arrows[2]                            # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
        x, pre_anglR = pre_arrow[Kn2idx['right_wrist']]                     # 右手首の移動ベクトルの長さと角度
        x, anglER = keyPoints.norm('right_elbow', 'right_wrist')         # 右肘と右手首のベクトルの長さと角度を計算       
        
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), anglL={int(anglL)}°, pre_anglR={int(pre_anglR)}° ,anglER={int(anglER)}°"\
                      + f" conf={keyPoints.conf('left_wrist'):.2f}")
#        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.06))} or normL > {int(thsd(0.06))} ]")
#        if  normR > thsd(0.06) or normL > thsd(0.06):
        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.06))} ]")

#        if  normR > thsd(0.06):
        if  normR > thsd(0.035):
            # 右手首の移動ベクトルの長さが15以上の場合（引分け大三への動作開始）
            Step_counter += 1
            if Step_counter == 1:   started = True
#            if Step_counter == 2:   started = True
        '''
        if started == False:
            # 右手首の移動ベクトルの角度が80度以上の場合（引分け大三への動作開始）
            mylog.log(INFO, f">>>   [ anglR > 80 ]")
            if anglR > 80.0:
                Step_counter += 1
                if Step_counter == 3:   started = True
        '''
    
    # 5-Hiki-wake  ->  6-Kai        
    elif section_no == 5:  
        normER, x = arrow[Kn2idx['right_elbow']]                    # 右肘の移動ベクトルの長さと角度
        normEL, x = arrow[Kn2idx['left_elbow']]                     # 左肘の移動ベクトルの長さと角度
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                        + f" normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ (normR < {int(thsd(0.025))} and normL < {int(thsd(0.025))}) and (normER < {int(thsd(0.025))} and normEL < {int(thsd(0.025))}) ]")

        if (normR < thsd(0.025) and normL < thsd(0.025)) and (normER < thsd(0.025) and normEL < thsd(0.025)) :
            # 右手首の移動ベクトルの長さが10以上の場合（引分けの完了）
            Step_counter = Step_counter + 1
            if Step_counter == 5: started = True    #  停止状態の５回保持で完了
    
    # 6-Kai  ->  7-Hanare        
    elif section_no == 6:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.085))} and normL > {int(thsd(0.085))} ]")

        if normR > thsd(0.085) and normL > thsd(0.085):
            # 右手首の移動ベクトルの長さが10以上の場合（離れ）
            started = True
    
    # 7-Hanare  ->  8-Zan-shin        
    elif section_no == 7:  
        mylog.log(INFO, f">>>   [ normR < {int(thsd(0.085))} ]")

        if normR < thsd(0.085) :
            started = True

    # 8-Zan-shin  ->  9-''(弓倒し)
    elif section_no == 8:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
#        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.085))} or normL > {int(thsd(0.085))} ]")
#        if normR > thsd(0.085) or normL > thsd(0.085):
        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.085))} ]")

        if normR > thsd(0.085):
            # 右手首と左手首の移動ベクトルの長さが大きい場合（弓だおし開始）
            started = True
    
    # 9-''(弓倒し)  ->  0-Start
    elif section_no == 9:  
        if Step_counter == 0: Step_counter = 10
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), normSR={int(normS)}({thsd.ratio(normS):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.085))} ]")

        if normR > thsd(0.085):
            # 右手首と左手首の移動ベクトルの長さが大きい場合（矢つがえ開始）
            if Step_counter/10 == 2: Step_counter = 10
            Step_counter += 1
            if Step_counter%10 == 2: started = True
        else:
            mylog.log(INFO, f">>>   [ normSR > {int(thsd(0.085))} ]")

            if normS > thsd(0.085):
                # 右腰の移動ベクトルの長さが大きい場合（退場）
                if Step_counter/10 == 1: Step_counter = 20
                Step_counter += 1
                if Step_counter%10 == 2: started = True
    else:
        mylog.log(ERROR, f">>> section_no={section_no}は未定義のセクションです")
        started = False
    #
    mylog.log(INFO, f">>>   started  ({section_no}): started={started}")
    return started
#
#セクションが完了したかどうかを判定する関数
#
def section_completed(section_no, myResult, arrows):
    global Step_counter
    
#    keyPoints = Keypoint(result, ibox)           # キーポイントのデータ解析インスタンス
    keyPoints = myResult           # キーポイントのデータ解析インスタンス
    ibox = myResult.boxid
    
    thsd = Threshold(keyPoints.block_height)     # バウンディングボックスの高さを基準に閾値設定インスタンス

    arrow = arrows[0]               # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
    
    normR, anglR = arrow[Kn2idx['right_wrist']]                     # 右手首の移動ベクトルの長さと角度
    normL, x = arrow[Kn2idx['left_wrist']]                          # 左手首の移動ベクトルの長さと角度
    normER, x = arrow[Kn2idx['right_elbow']]                        # 右肘の移動ベクトルの長さと角度
    normEL, x = arrow[Kn2idx['left_elbow']]                         # 左肘の移動ベクトルの長さと角度
    
    xy_wristR = keyPoints.xy('right_wrist')                         # 右手首の座標
    xy_wristL = keyPoints.xy('left_wrist')                          # 左手首の座標
    xy_nose = keyPoints.xy('nose')                                  # 鼻の座標

    lenY, x = keyPoints.norm('right_eye', 'left_eye')               # 右目と左目のベクトルの長さと角度を計算
    
    completed = False
        
    conf = keyPoints.conf('right_wrist')                            # 右手首の座標の信頼度
    if conf < 0.90 :
        # 右手首の信頼度が低い、または移動ベクトルの長さが0の場合は開始しない
        mylog.log(INFO, f"completed({section_no}): roght-wrist-conf={conf:.2f}  skip....")
        return completed

    mylog.log(INFO, f"completed({section_no}):  boxid={ibox}, H={int(thsd.block_height)}, wristR=[{int(xy_wristR[0])}, {int(xy_wristR[1])}],"\
            + f"    normR={int(normR)}({thsd.ratio(normR):.3f}), anglR={int(anglR)}°, conf={conf:.2f}, counter={Step_counter}")
    
    # 1-Asi-bumi
    if section_no == 1:  
        if Step_counter == 0:
            lenY, x = keyPoints.norm('right_eye', 'left_eye')         # 右目と左目のベクトルの長さと角度を計算
            conf= keyPoints.conf('left_eye')       
            mylog.log(INFO, f">>>   lenY={int(lenY)}({thsd.ratio(lenY):.3f}), conf={conf:.2f}")
            mylog.log(INFO, f">>>   [  conf > 0.50 and lenY > {int(thsd(0.028))}]")
            
            if conf > 0.50 and lenY > thsd(0.028):
                # 右目と左目のベクトルの長さが10以上、左目の信頼度が0.5以上の場合（正面を向く）
                Step_counter = 10
        else:
            normN, x = arrow[Kn2idx['nose']]                        # 鼻の移動ベクトルの長さと角度
            normHR, x = arrow[Kn2idx['right_hip']]                  # 左腰の移動ベクトルの長さと角度
            normHL, x = arrow[Kn2idx['left_hip']]                   # 左腰の移動ベクトルの長さと角度
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), normN={int(normN)}({thsd.ratio(normN):.3f}), "\
                            + f" normHR={int(normHR)}({thsd.ratio(normHR):.3f}), normHR={int(normHL)}({thsd.ratio(normHL):.3f})") 

            mylog.log(INFO, f">>>   [ (normR <= {int(thsd(0.035))} and normL <= {int(thsd(0.035))}) and"\
                        + f" (normHR <= {int(thsd(0.035))}) and (normHL <= {int(thsd(0.035))}) and (normN <= {int(thsd(0.035))}) ")
            
            if (normR <= thsd(0.035) and normL <= thsd(0.035)) and (normHR <= thsd(0.035) and normHL <= thsd(0.035)) and (normN <= thsd(0.035)):
                # 右手首と左手首、右腰骨と左腰骨の移動ベクトルの長さが10未満、鼻の移動ベクトルの長さが10未満、
                Step_counter += 1
                if (Step_counter%10) == 2: completed = True
    
    # 2-Dou-zukuri            
    elif section_no == 2:  
        if Step_counter == 10:
            mylog.log(INFO, f">>>   [ normR > {int(thsd(0.080))} ]")
            
            if normR > thsd(0.080): Step_counter = 20
            # 右手首の移動ベクトルの長さが大きい場合（取り矢動作開始）
        else:
            x, angER = keyPoints.norm('right_elbow', 'right_wrist')             # 右肘から右手首へのベクトルの長さと角度を計算
            mylog.log(INFO, f">>>   angER= {angER:.1f}°")
            mylog.log(INFO, f">>>   [ angER > 65 and angER < 95 ]")
            
            if ( angER > 60 and angER < 95 ):
                # 右手首と右肘を結ぶベクトルの角度が65度から95度の範囲内の場合
                mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
                mylog.log(INFO, f">>>   [ normR < {int(thsd(0.030))} and normL < {int(thsd(0.030))} ]")
            
                if (normR <= thsd(0.030) and normL <= thsd(0.030)) : 
                    if Step_counter < 10:
                        # 右手首と左手首の移動ベクトルの長さが10未満の場合（矢つがえ動作完了）
                        Step_counter += 1
                        if (Step_counter%10) == 2: Step_counter = 10        #２回保持
                    elif Step_counter >= 20:
                        # 右手首と左手首の移動ベクトルの長さが10未満の場合（胴作り完了）
                        Step_counter += 1
                        if (Step_counter%10) == 5: completed = True         #５回保持
    
    # 3-Yu-gamae            
    elif section_no == 3:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), normER={int(normER)}({thsd.ratio(normR):.3f}),"\
                      + f" normEL={int(normEL)}({thsd.ratio(normEL):.3f}), lenY={int(lenY)}({thsd.ratio(lenY):.3f})")
        
        if Step_counter == 0:
            mylog.log(INFO, f">>>   [ lenY < {int(thsd(0.026))} ]")
            
            if lenY < thsd(0.026):  Step_counter = Step_counter + 1
                #　物見を定める
        else:
            mylog.log(INFO, f">>>   [ (normR < {int(thsd(0.025))} and normL < {int(thsd(0.025))})"\
                          + f" and (normER < {int(thsd(0.025))} and normEL < {int(thsd(0.025))}) ]")

            if (normR < thsd(0.025) and normL < thsd(0.025)) and (normER < thsd(0.025) and normEL < thsd(0.025)) :
                # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満の場合
                Step_counter = Step_counter + 1
                if Step_counter == 3: completed = True   # ３回保持で完了                
#                if Step_counter == 2: completed = True   # ３回保持で完了                
                
    # 4-Uti-okosshi        
    elif section_no == 4:  
        mylog.log(INFO, f">>>   xy_nose={int(xy_nose[1])}, xy_wristR={int(xy_wristR[1])}, xy_wristL={int(xy_wristL[1])}")
        mylog.log(INFO, f">>>   [ (xy_wristR[1] < xy_nose[1] and xy_wristL[1] < xy_nose[1] ]")

        if (xy_wristR[1] < xy_nose[1] and xy_wristL[1] < xy_nose[1]):
            # （右手首と左手首が鼻より高い位置で停止）
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                          + f"normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normEL)}({thsd.ratio(normEL):.3f})")
            mylog.log(INFO, f">>>   [ (normR < {int(thsd(0.020))} and normL < {int(thsd(0.020))}) and (normER < {int(thsd(0.020))} and normEL < {int(thsd(0.017))}) ]")

            if (normR < thsd(0.020) and normL < thsd(0.020)) and (normER < thsd(0.020) and normEL < thsd(0.020)):
                # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満
                Step_counter = Step_counter + 1
                if Step_counter == 3: completed = True   # ３回保持で完了                
    
    # 5-Hiki-wake        
    elif section_no == 5:  
        mylog.log(INFO, f">>>   y_nose={int(xy_nose[1])}, y_R={int(xy_wristR[1])}, y_L={int(xy_wristL[1])}")
        mylog.log(INFO, f">>>   [ (xy_wristR[1] > xy_nose[1] and xy_wristL[1] > xy_nose[1] ]")

        if (xy_wristR[1] > xy_nose[1] and xy_wristL[1] > xy_nose[1]):
            # （右手首と左手首が鼻より低い位置で停止）
            if Step_counter < 20: Step_counter += 10
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                          + f" normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normL)}({thsd.ratio(normEL):.3f})")
            mylog.log(INFO, f">>>   [ (normR < {int(thsd(0.025))} and normL < {int(thsd(0.025))}) and (normER < {int(thsd(0.025))} and normEL < {int(thsd(0.025))}) ]")

            if (normR < thsd(0.025) and normL < thsd(0.025)) and (normER < thsd(0.025) and normEL < thsd(0.025)) :
                # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満（姿勢の保持で完了）
                Step_counter = Step_counter + 1
                if (Step_counter%10) == 5:  completed = True
        else:
            Step_counter = 10

    # 6-Kai            
    elif section_no == 6:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                      + f" normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normEL)}({thsd.ratio(normEL):.3f}) ")
        mylog.log(INFO, f">>>   [ (normR < {int(thsd(0.017))} and normL < {int(thsd(0.017))}) and (normER < {int(thsd(0.017))} and normEL < {int(thsd(0.017))}) ]")

        if (normR < thsd(0.017) and normL < thsd(0.017)) and (normER < thsd(0.017) and normEL < thsd(0.017)) :
            # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満（姿勢の保持で完了）
            Step_counter = Step_counter + 1
            if Step_counter == 5:  completed = True
    
    # 7-Hanare        
    elif section_no == 7:  
        Step_counter = Step_counter + 1
        if Step_counter > 10: completed = True
    
    # 8-Zan-shin    
    elif section_no == 8:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR < {int(thsd(0.10))} and normL < {int(thsd(0.10))} ]")

        if normR < thsd(0.10) and normL < thsd(0.10):
            # 右手首と左手首の移動ベクトルの長さが50以下の場合（姿勢の保持で完了）
            Step_counter = Step_counter + 1
            if Step_counter == 3:  completed = True
    
    # 8-Zan-shin(弓倒し)        
    elif section_no == 9:  
        x, angER = keyPoints.norm('right_elbow', 'right_wrist')             # 右肘から右手首へのベクトルの長さと角度を計算
#        normHR, x = arrow[Kn2idx['right_hip']]                              # 右腰の移動ベクトルの長さと角度
        normS, x = arrow[Kn2idx['right_shoulder']]                      # 右肩の移動ベクトルの長さと角度
#        mylog.log(INFO, f">>>   angER= {angER:.1f}°, normHR={int(normHR)}({thsd.ratio(normHR):.3f})")
        mylog.log(INFO, f">>>   angER= {angER:.1f}°, normSR={int(normS)}({thsd.ratio(normS):.3f})")
        mylog.log(INFO, f">>>   [ angER > 20 and angER < 95 ]")

        if ( angER > 25 and angER < 95 ):
            # 右手首と右肘を結ぶベクトルの角度が65度から95度の範囲内の場合
            mylog.log(INFO, f">>>   [ normR < {int(thsd(0.030))} ]")

            if normR <= thsd(0.030) : 
                Step_counter = Step_counter + 1
                if Step_counter == 2: completed = True

#        mylog.log(INFO, f">>>   [ normHR > {int(thsd(0.085))} ]")
#        if normHR > thsd(0.085):
        mylog.log(INFO, f">>>   [ normS > {int(thsd(0.085))} ]")

        if normS > thsd(0.085):
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
# 検出結果をフレームに描画する関数
#
def plot(myResult, prepoints_buffer=None, annotated_frame=None):
    global Section_no, Split_start, Split_sec, Lap_start, Lap_sec, Completed, Step_counter, CameraPos
    
    result = myResult.result
    mylog.log(DEBUG, f"Tracking_only={Tracking_only}")
    mylog.log(DEBUG, f"[plot]: {type(result.keypoints)},{len(result.keypoints)}個のキーポイント")

    if annotated_frame is None:
        # YOLOv8のplot関数を使用してフレームに描画  
        # 　kpt_line=False： キーポイントのマークのみを描画）
        annotated_frame = result.plot(boxes=True, labels=False, kpt_line=True, kpt_radius=3)
    else:    
        # 面積最大のボックスを取得 
        boxid = myResult.boxid
        # 対象ボックスのキーポイントの左（右）手首座標データの信頼度を取得
        '''
        confR = result.keypoints.conf[boxid][Kn2idx['right_wrist']].item()     # 右手首の信頼度を取得
        confL = result.keypoints.conf[boxid][Kn2idx['left_wrist']].item()      # 左手首の信頼度を取得
#       if confR < 0.90 or (Section_no > 4 and confL < 0.85) : #       信頼度が0.93未満の場合は描画しない（ー＞画像の欠落が著しい）
        if confR < 0.75 : #       信頼度が0.93未満の場合は描画しない
            mylog.log(INFO, f"[plot]: 対象ボックスのキーポイントの信頼度が低いので描画しない: confR={confR:.2f}, confL={confL:.2f}")
            return annotated_frame  # -> オリジナル画像を表示する
#           return None             # -> 前回の画像を再表示する
        '''

        # 対象ボックスのキーポイントの接続ラインを描画
        draw_kpts_line(annotated_frame, myResult.points)   

        # 前回（直近ではない）サンプリングのキーポイントデータを取得
        preResult = prepoints_buffer.get(1)     
        pboxid = preResult.boxid                                 # 前回のボックスID

        # セクション情報を更新
        if Section_no < 2: 
            CameraPos = get_camera_pos(myResult)                # カメラの位置取得（足踏み完了まで）

        if ( Tracking_only or CameraPos == 'Right-side' or CameraPos == 'Front-side'):
            arrow_length_angles = [None, None, None, None]      # 各キーポイントの移動ベクトルの長さと角度を格納するリストを初期化（前回、前前回）
#            arrow_points = result.keypoints.xy[boxid] - preResult.keypoints.xy[pboxid]              # 前回のキーポイントとの差分ベクトルを計算
#            arrow_length_angles[0] = [vector_length_angle(vect) for vect in arrow_points.numpy()]   # 各ベクトルの長さと角度を計算 
            arrow_points = myResult.points - preResult.points              # 前回のキーポイントとの差分ベクトルを計算
            arrow_length_angles[0] = [vector_length_angle(vect) for vect in arrow_points]   # 各ベクトルの長さと角度を計算 
            
            # 前前回のキーポイントデータを取得
            if prepoints_buffer.length > 2:   # 前前回のキーポイントデータがある場合
                for i in range(1, prepoints_buffer.length - 1):
                    preResult = prepoints_buffer.get( (i + 1) )     
                    pboxid = preResult.boxid                  # 前前回のボックスID
                    if  pboxid  >= 0:
#                        arrow_points = result.keypoints.xy[boxid] - preResult.keypoints.xy[pboxid]       # 前前回のキーポイントとの差分ベクトルを計算
#                        arrow_length_angles[i] = [vector_length_angle(vect) for vect in arrow_points.numpy()]   # 各ベクトルの長さと角度を計算
                        arrow_points = myResult.points - preResult.points       # 前前回のキーポイントとの差分ベクトルを計算
                        arrow_length_angles[i] = [vector_length_angle(vect) for vect in arrow_points]   # 各ベクトルの長さと角度を計算
                        mylog.log(DEBUG, f"arrow_length_angles[{i}]: {arrow_length_angles[i]}") 

            if Tracking_only:
                # 解析結果のデータをトラッキング（DBに出力）する
                if Tracking_on: tracking_result(myResult, arrow_length_angles)
            
            if Lap_start > 0:    
                # 射法八節の動作開始、完了を判定する（キー'0'の押下で判定を開始する）
                if Section_no == 0 or Completed:
                    # 動作の開始を判定
                    if section_started(Section_no, myResult, arrow_length_angles):
                        Split_start = Frame_counter                         # スプリット開始時間を記録
                        Split_sec = 0
                        Completed = False                                   # セクションが開始されたら完了フラグをリセット    
                        if Section_no != 9: 
                            Section_no = Section_no + 1                     # セクション番号をインクリメント
                            Step_counter = 0                                # セクション内の動作カウンター
                        else: 
                            counter = int(Step_counter/10)      
                            mylog.log(INFO, f"[plot]:Step_counter={Step_counter}, {counter}") 
                            if counter == 2: 
                                Lap_start = 0                               # 退場動作開始の場合、解析終了
                                Split_sec = 0
                                Split_start = 0
                            else:                                           # 乙矢の矢つがえ動作開始
                                # セクション番号を2にリセット、動作カウンターを20に設定
                                Section_no = 2
                                Step_counter = 20
                                mylog.log(INFO, f"[plot]:Next {Section_names[Section_no]} Sction_no={Section_no}, Step_counter={Step_counter}") 

                else:
                    # 動作の完了を判定
                    if section_completed(Section_no, myResult, arrow_length_angles):
                        Completed = True 
                        if Section_no != 6: Split_start = 0                 # スプリット開始時間をリセット
                        if Section_no == 9 and Step_counter == 0:           # 退場動作の場合、解析終了 
                            Lap_start = 0
                        Step_counter = 0                                    # セクション内の動作カウンター
 
                mylog.log(DEBUG, f"[plot]:Lap_start={Lap_start}") 
        #
        if Lap_start != 0:   Lap_sec = (Frame_counter - Lap_start)/Fps         # ラップ秒を計算
        if Split_start != 0: Split_sec = (Frame_counter - Split_start)/Fps     # スプリット秒を計算

        # セクション情報をフレームに描画
        section_color =  (0, 255, 255)              # セクションの色（黄色）BGR
        others_color =  (255, 255, 255)             # その他の色（白）
        if Completed: section_color = (0, 255, 0)   # 完了したセクションの色（緑色）BGR
        
        section_name = Section_names[Section_no]     # セクション名を取得
        if Step_counter > 0:                        # セクション内の動作カウンターが1以上の場合、セクション名にカウンターを追加
            section_name += f"({Step_counter})"     
        
        cv2.putText(annotated_frame, f"camera: {CameraPos}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 2)
        cv2.putText(annotated_frame, f"section: {section_name}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, section_color, 2)
        cv2.putText(annotated_frame, f"split   : {Split_sec:6.2f}sec.", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 2)
        cv2.putText(annotated_frame, f"lap    : {Lap_sec:6.2f}sec.", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 2)
    #
    return annotated_frame
#
# Main process to play video with form-analize by YOLOv8
#
def main(): 
    global Frame_counter, Section_no, Split_sec, Split_start, Lap_sec, Lap_start, Completed, Step_counter, Tracking_only, Tracking_on
    #
    # start of main
    #
    cam_id = None                                   # デフォルトのカメラID
    raw_image = False                               # 生画像を表示するオプション
    manual_plot = False                             # 手動でプロットするオプション
    idir = PICT_PATH                                # 初期ディレクトリを指定
    ALL_TYPES = "*.*"                               # 動画ファイル名[*.mp4;*.avi;*.mov;*.mkv"]
    timestamp = datetime.now().strftime('%Y%m%d')
    filetypes = f"WIN_{timestamp}_*.mp4"            #'*WIN_YYYYmmdd_10_46_55_Pro.mp4'  # 動画ファイル名
    iwait = 1                                       # ウィンドウの更新間隔（ミリ秒）
    milsec = 0  # ミリ秒
    attention = 0
    prePointsBuffer = RingBuffer(4)                 # 検出結果を保存するリングバッファ（4回分を保存）                           
    preResult = RingBuffer(1)                       # 前回の検出結果（補整済）を保存するリングバッファ                           
    preFrame = None                                 # 前回のフレームを保存する変数
    #
    case_name = None                                # ケース名（動画ファイル名）
    #
    # print command line(arguments)
    args = sys.argv
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
    #
    if '-r' in opts:
        raw_image = True        # 生画像を表示するオプション

        
    if '-m' in opts:            # 手動（OpenCV）で解析データをプロットするオプション
        manual_plot = True
        
    if '-t' in opts:
        Tracking_only = True    # トラッキングのみを行うオプション
#        Tracking_on = True      # トラッキングを有効にする
        i = args.index('-t') 
        if i + 1 < len(args) and (not args[i + 1].startswith('-')):
            case_name = args[i + 1]  # ケース名を取得
            if len(case_name) == 0:
                print("ケース名の指定がありません")
                return
                
            
    if '-a' in opts:
        filetypes = ALL_TYPES   
        
    # YOLOV8のログレベルを設定
    if '-v' in opts:
        logger.disabled = False  # ログ出力を有効化
    
    # ログファイル出力のログレベルを設定
    debug_opt = 0
    dbg_opt = [opt for opt in opts if opt.startswith('-d')]
    if len(dbg_opt) > 0 and dbg_opt[0][2:].isnumeric(): debug_opt = int(dbg_opt[0][2:])
    
    mylog_level = ERROR  # デフォルトはERROR
    if debug_opt != 0: 
        mylog_level = INFO if debug_opt == 1 else DEBUG 
    mylog.setLevel(mylog_level)  
        
    if cam_id is not None:
        # カメラから映像を取得
        cap = cv2.VideoCapture(cam_id) # カメラIDを指定
    else:
        # 動画ファイルを選択する
        file_name = filedialog.askopenfilename(
            title = "動画ファイルを選択してください",
            filetypes = [("Video files", filetypes)],
            initialdir = idir
        )
        if not file_name:
            print("動画ファイルの選択がキャンセルされました")
            return
        
        cap = cv2.VideoCapture(file_name)  # 動画ファイルのパスを指定
        iwait = 1  # 動画ファイルの場合はウィンドウの更新間隔を長くする
        #
        if case_name is None:
            # 動画ファイル名からケース名を取得
            case_name = os.path.basename(file_name).split('.')[0]
    # トラッキングデータのケース名を設定
    if Tracking_only: 
        Db.case_name = case_name   
        fps, x = Db.get_fps()
        if fps is not None:
            print(f"> '{case_name}' already registered. Are you sure?[y/n].")
            ans = input('>>')
            if ans != 'y': return
        Db.open_csv()

    # 動画ファイルが開けない場合のエラーハンドリング
    if not cap.isOpened():
        print("カメラor動画ファイルが見つかりません")
        return
    # 出力ファイルの設定
    imgWriteEnabled = False
    out_file = ''
    if ('-w' in opts) or ('-wo' in opts):
        out_file = f"{idir}/_WIN_{timestamp}_{datetime.now().strftime('%H%M%S')}.mp4"  # 出力ファイル名を指定   
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        cv2Video = cv2.VideoWriter(out_file, fourcc, cap.get(cv2.CAP_PROP_FPS),
                    (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
    #
    # YOLOv8-poseモデルの読み込み（事前学習済みモデル）
    #
    print("YOLOv8 Pose Detectionを開始します")
    print(f"YOLOv8 ログレベル={mylog_level}")
    print(f"Tracking_only={Tracking_only}")
    
    mylog.log(INFO,"YOLOv8 Pose Detectionを開始します")
    model = YOLO('yolov8n-pose.pt')  # 軽量モデル。他にも'yolov8s-pose.pt'などあり
    model.info()  # モデル情報を表示
    #
    # 先頭フレームを読み込み
    #
    ret, frame = cap.read()
    if not ret:
        print("動画ファイルの読み込みに失敗しました")
        cap.release()
        return
    
    # フレームのサイズを取得
    frame_height, frame_width = frame.shape[:2] 
    Fps = cap.get(cv2.CAP_PROP_FPS)                                                 # フレームレートを取得
    Db.insert_frame_info( [file_name, Fps, frame_height, frame_width, Db.csvpath] ) # DBテーブルに登録
    
    mylog.log(INFO, f"[main]:フレーム情報: {file_name}:{frame_width}x{frame_height}, Fps={Fps:.2f}")
    
    Frame_counter = 1  # フレームカウンターの初期化
    #
#    if raw_image is True or Tracking_only is True:
    if raw_image is True:
        iwait_init = int(1/Fps * 1000)  # 生画像を表示する場合、FPS値からキー入力待ち時間を設定
    else: 
        iwait_init = 1
    # ウィンドウの更新間隔を設定
    iwait = iwait_init        
    print(f"[main]:iwait={iwait}")
    mylog.log(INFO, f"[main]:iwait={iwait}")
    #
    while True:
        # 次のフレームの読み込み
        ret, frame = cap.read()
        if not ret:
            break
        Frame_counter += 1  # フレームカウンターをインクリメント
        if raw_image is True:
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
                print(e)
                mylog.log(INFO, "[main]検出結果の描画をスキップ")
                annotated_frame = frame
            else:
                if preResult.len() > 0:
                    myResult.adjust_points(preResult.get().points)
                # リングバッファに保存
                preResult.append( myResult )       
                    
                # Sample_flamesフレーム毎に検出結果を保存
                if (Frame_counter%Sample_flames) == 0:
                    # 検出結果（補正済）を保存 
                    prePointsBuffer.append( myResult )                        
                    mylog.log(INFO, f"[main]: {datetime.now().strftime('%H-%M-%S')}:検出結果保存: {type(results)}, {len(results)}個の結果,"\
                                + f"フレーム={Frame_counter}, buffer_length={prePointsBuffer.length}")
                # 検出結果をフレームに描画
                if manual_plot or Tracking_only:
                    if Tracking_only: 
                        Db.frame_no = Frame_counter     # トラッキングデータのフレーム番号を設定  
                        Db.section = Section_no         # トラッキングデータのセクション番号を設定              
                    
                    # 生画像に手動（OpenCV）で描画
                    annotated_frame = frame
                    if prePointsBuffer.len() > 1:
                        annotated_frame = plot( myResult, prePointsBuffer, frame)
                        if annotated_frame is None and preFrame is not None:  # 前回のフレームを描画
                            annotated_frame = preFrame
                            mylog.log(INFO, "[main]: 前回フレームを描画")
                else:
                    # YOLOのplot関数を使用してフレームに描画
                    annotated_frame = plot( myResult )
    
        # ウィンドウに表示
        cv2.imshow('YOLO Pose Detection', annotated_frame)
        preFrame = annotated_frame.copy()  # 前回のフレームへ保存
        
        if imgWriteEnabled:
            # 出力ファイルに書き込み
            cv2Video.write(annotated_frame)
            
        #キー入力をチェックするする
        key = cv2.waitKey(iwait) & 0xFF
        if key == -1: 
            # キー入力がない場合は次のフレームへ
            continue
        #
        # キー入力に応じて処理を実行
        #
        if key == ord('q'):
            # 'q'キーで終了
            break
        
        elif key == ord('p'):
            iwait = 0 if iwait > 0 else iwait_init  # 'p'キーで一時停止/再開
            if iwait == 0: print("一時停止しました")
            else: print("再開しました")
            
        elif key == ord('t') and Tracking_only:
            Tracking_on = True if Tracking_on is False else False  # 't'キーで一開始／停止
            if Tracking_on: 
                print("トラッキングを開始します")
                mylog.log(INFO, ">> Trucking start")
            else: 
                print("トラッキングを停止します")
                mylog.log(INFO, ">> Trucking pause")
        
        elif key == ord('s'):
            # スクリーンショットを保存
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"{idir}screenshot_{timestamp}.png"
            cv2.imwrite(screenshot_path, annotated_frame)
            print(f"スクリーンショットを保存しました: {screenshot_path}")
        
        elif key == ord('w') and out_file != '':
            imgWriteEnabled = True if imgWriteEnabled is False else False  # 't'キーで一開始／停止
            if imgWriteEnabled: 
                print(f"出力ファイルに書き込みを開始します: {out_file}")
                mylog.log(INFO, ">> image write start")
            else: 
                print(f"出力ファイルに書き込みを停止します: {out_file}")
                mylog.log(INFO, ">> image write pause")

        elif key >= ord('0') and key <= ord('8'):
            # セクション番号を設定
            Section_no = key - ord('0')
            if Section_no == 0: print(f"姿勢解析を開始します")
            else:  print(f"セクション番号を設定: {Section_no}")
            Completed = False
            Split_sec = 0
            Split_start = 0
            Step_counter = 0                    # セクション内の動作カウンターをリセット
            if Section_no == 0:
                Lap_start = Frame_counter       # ラップ開始時間を記録
                Lap_sec = 0
#                milsec = time.time() * 1000     # ミリ秒を記録
            else: 
                Split_start = Frame_counter
        
        elif key == ord('9'):
            print(f"姿勢解析を停止します。")
            Lap_start = 0                       # ラップ開始時間をリセット 
            Split_start = 0                     # スプリット開始時間をリセット 
            Step_counter = 0                    # セクション内の動作カウンターをリセット              
        
        elif key == ord('.'):                   # (>) 進める
            Frame_counter += int(Fps)*2         # フレームカウンターを2秒進める
            cap.set(cv2.CAP_PROP_POS_FRAMES, Frame_counter)
        
        elif key == ord(','):                   # (<) 戻す
            if Frame_counter > int(Fps)*2 :Frame_counter -= int(Fps)*2  
                                                # フレームカウンターを2秒戻す
            else: Frame_counter = 1
            cap.set(cv2.CAP_PROP_POS_FRAMES, Frame_counter)
        
        elif key == ord('a'):
            attention += 1
            mylog.log(INFO, f"!!Attention({attention}):Section({Section_no:2d}), Frame_counter={Frame_counter}")
            print(f"アテンション({attention}):Section({Section_no:2d}), Frame_counter={Frame_counter}")
    #
    # リソースの解放
    if Tracking_only: Db.csvfile.close() 
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    print(datetime.now())
    print(os.getcwd())
    #
    ultralytics.checks()  # YOLOv8のチェックを実行
    if not os.path.exists('yolov8n-pose.pt'):
        print("YOLOv8-poseモデルが見つかりません。ダウンロードしてください。")
        exit(1)
    main()
# eof