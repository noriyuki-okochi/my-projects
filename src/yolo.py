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

# ログレベルをINFOに設定
mylog.setLevel(DEBUG)  
mylog.setLevel(INFO)  

#　アプリケーションのグローバル変数の定義
Section_no = 0      # セクション番号
Split_sec = 0       # スプリット秒
Split_start = 0     # スプリットベース時間
Lap_sec = 0         # ラップ秒 
Lap_start = 0       # ラップベース時間
Completed = False   # 完了フラグ
Step_counter = 0    # セクション内のステップカウンター
# セクション名の定義
Section_name = [' ', '1.Asi-bumi', '2.Dou-zukuri', '3.Yu-gamae', '4.Uti-okosshi', 
                     '5.Hiki-wake', '6.Kai', '7.Hanare', '8.Zan-shin', '']  # セクション名
# キーポイントのインデックスを定義
Kn2idx = {'nose':0, 'left_eye':1, 'right_eye':2, 'left_ear':3, 'right_ear':4, 
        'left_shoulder':5, 'right_shoulder':6, 'left_elbow':7, 'right_elbow':8, 
        'left_wrist':9, 'right_wrist':10, 'left_hip':11, 'right_hip':12,
        'left_knee':13, 'right_knee':14, 'left_ankle':15, 'right_ankle':16}  # キーポイント名
# カメラの位置を定義
Camera_pos = ['', 'Front-side', 'Right-side', 'Upper-side']  # カメラの位置
#
# YOLOv8とOpenPoseの組み合わせ例（Ultralytics YOLOv8 + YOLOv8-poseモデル利用）
# このコードは、YOLOv8を使用してカメラまたは動画ファイルから骨格検出を行うものです。
# YOLOv8-poseモデルは、Ultralyticsの事前学習済みモデルを使用しています。
def help():
    print(" --- command ---")
    print(" python ./src/yolo.py [<Camera-ID>] [-h] [-v] [-a] [-r|-m] [-w]")
    print(" --- option ---")
    print(" -hELP")
    print(" -vERBOSE")
    print(" -aLL-FILE-TYPES")
    print(" -mANUAL-PLOT(dont use YOLO plot)")
    print(" -rOW-IMAGE")
    print(" -wRite-MOTION-FILE")
    print(" --- key operation ---")
    print(" s :スナップショットファイルの作成")
    print(" o :出力ファイルへの書き込み開始")
    print(" c :出力ファイルへの書き込み停止")
    print(" 0 :ラップ開始")
    print(" q :処理の中断")
    print(" --- example ---")
    print("例)当日作成の動画ファイルから選択 : python yolo.py")  
    print("例)全ての動画ファイルタイプから選択: python yolo.py -a")  
    print("例)カメラID 1 を指定             : python yolo.py 1")  
    return

#
# リングバッファのクラス定義
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
    x1, y1 = map(int, p1)
    x2, y2 = map(int, p2)
    if abs(x2 - x1) < threshold and abs(y2 - y1) < threshold: ans = True
    '''
    vect = p1 - p2  # 2点のベクトルを計算
    length, x = vector_length_angle(vect.numpy())  # ベクトルの長さと角度を計算
    if abs(length) < threshold:
        # ベクトルの長さが閾値以下の場合、近いと判断
        ans = True
    mylog.log(DEBUG, f"near={ans} : p1=({p1[0]},{p1[1]}), p2=({p2[0]}, {p2[1]}), threshold={threshold}")
    return ans
#
#    閾値の計算を行うクラス       
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
#セクションが開始したかどうかを判定する関数
#
def section_started(section_no, result, ibox, arrows):
    global Step_counter

    keyPoints = Keypoint(result, ibox)           # キーポイントのデータ解析インスタンス
    thsd = Threshold(keyPoints.block_height)     # バウンディングボックスの高さを基準に閾値設定インスタンス
    
    arrow = arrows[0]                            # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
    
    normR, anglR = arrow[Kn2idx['right_wrist']]                     # 右手首の移動ベクトルの長さと角度
    normL, x = arrow[Kn2idx['left_wrist']]                          # 左手首の移動ベクトルの長さと角度
    normS, x = arrow[Kn2idx['right_shoulder']]                      # 右肩の移動ベクトルの長さと角度
    xy_wristR = keyPoints.xy('right_wrist')                         # 右手首の座標
    
    started = False
    conf = keyPoints.conf('right_wrist')                             # 右手首の座標の信頼度
    if conf < 0.3 :
        # 右手首の信頼度が低い、または移動ベクトルの長さが0の場合は開始しない
        mylog.log(INFO, f">>>   conf={conf:.2f}  skip....")
        return started

    mylog.log(INFO, f"started ({section_no}):  boxid={ibox}, H={int(thsd.block_height)}:  wristR=[{int(xy_wristR[0])}, {int(xy_wristR[1])}],"\
            + f"    normR={int(normR)}({thsd.ratio(normR):.3f}), anglR={int(anglR)}°, conf={conf:.2f}")

    if section_no == 0:    # 0-Start  ->  1-Asi-bumi
        lenS, x = keyPoints.norm('left_shoulder', 'right_shoulder')          # 右肩と左肩のベクトルの長さと角度を計算
        mylog.log(INFO, f">>>   lenS={int(lenS)}({thsd.ratio(lenS):.3f}), normS={(int(normS))}({thsd.ratio(normS):.3f})")
        mylog.log(INFO, f">>>   [ lenS < {int(thsd(0.14))} and normS > {int(thsd(0.20))} ]")
        if lenS < thsd(0.14) and  normS > thsd(0.18):
            # 右肩と左肩のベクトルの長さが80未満、右肩の移動ベクトルの長さが50以上の場合（射位へ移動）
            started = True
            
    elif section_no == 1:  # 1-Asi-bumi  ->  2-Dou-zukuri
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normL > {int(thsd(0.084))} ]")
        if normL > thsd(0.084):
#       if normL > 50:
            # 右手首と左手首の移動ベクトルの長さが50以上の場合（矢つがえ動作開始）
            started = True
            
    elif section_no == 2:  # 2-Dou-zukuri  ->  3-Yu-gamae
        lenE, x = keyPoints.norm('right_eye', 'left_eye')         # 右目と左目のベクトルの長さと角度を計算       
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), lenE={int(lenE)}({thsd.ratio(lenE):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.034))} and normL < {int(thsd(0.017))} and lenE > {int(thsd(0.034))} ]")
        if (normR > thsd(0.034) and normL < thsd(0.017)) and lenE > thsd(0.034):
#       if (normR > 20 and normL < 10) and lenE > 20:
            # 右手首の移動ベクトルの長さが10以上の場合（取りかけ動作開始）
            started = True
            
    elif section_no == 3:  # 3-Yu-gamae  ->  4-Uti-okosshi
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.017))} and normL > {int(thsd(0.017))} ]")
        if normR > thsd(0.017) and normL > thsd(0.017):
#       if normR > 10 and normL > 10:
            # 右手首と左手首の移動ベクトルの長さが10以上の場合（打起し動作開始）
            started = True
            
    elif section_no == 4:  # 4-Uti-okosshi  ->  5-Hiki-wake
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normL > {int(thsd(0.025))} ]")
        if  normL > thsd(0.025):
#       if  normL > 15:
            # 左手首の移動ベクトルの長さが15以上の場合（引分け大三への動作開始）
            started = True
            
    elif section_no == 5:  # 5-Hiki-wake  ->  6-Kai
        normER, x = arrow[Kn2idx['right_elbow']]                    # 右肘の移動ベクトルの長さと角度
        normEL, x = arrow[Kn2idx['left_elbow']]                     # 左肘の移動ベクトルの長さと角度
        mylog.log(INFO, f">>>   count={Step_counter}, normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                        + f" normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ (normR < {int(thsd(0.025))} and normL < {int(thsd(0.017))}) and (normER < {int(thsd(0.017))} and normEL < {int(thsd(0.017))}) ]")
        if (normR < thsd(0.025) and normL < thsd(0.017)) and (normER < thsd(0.017) and normEL < thsd(0.017)) :
#       if (normR < 15 and normL < 10) and (normER < 10 and normEL < 10) :
            # 右手首の移動ベクトルの長さが10以上の場合（引分けの完了）
            Step_counter = Step_counter + 1
            if Step_counter == 5: started = True
            
    elif section_no == 6:  # 6-Kai  ->  7-Hanare
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.085))} and normL > {int(thsd(0.085))} ]")
        if normR > thsd(0.085) and normL > thsd(0.085):
#       if normR > 50 and normL > 50:
            # 右手首の移動ベクトルの長さが10以上の場合（離れ）
            started = True
            
    elif section_no == 7:  # 7-Hanare  ->  8-Zan-shin
        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.085))} ]")
        if normR > thsd(0.085):
#       if normR > 50:
            # 右手首の移動ベクトルの長さが50以上の場合（残身）
            started = True
            
    elif section_no == 8:  # 8-Zan-shin  ->  9-''(ダミー：弓倒し)
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(0.085))} and normL > {int(thsd(0.085))} ]")
        if normR > thsd(0.085) and normL > thsd(0.085):
#       if normR < 10 and normL < 10:
            # 右手首と左手首の移動ベクトルの長さが10未満の場合（弓だおし開始）
            started = True
            
    elif section_no == 9:  # 9-''(ダミー：弓倒し)  ->  0-Start
        pass
    else:
        mylog.log(ERROR, f">>> section_no={section_no}は未定義のセクションです")
        started = False
    #
    mylog.log(INFO, f">>>   started  ({section_no}): started={started}")
    return started
#
#セクションが完了したかどうかを判定する関数
#
def section_completed(section_no, result, ibox, arrows):
    global Step_counter
    
    keyPoints = Keypoint(result, ibox)           # キーポイントのデータ解析インスタンス
    thsd = Threshold(keyPoints.block_height)     # バウンディングボックスの高さを基準に閾値設定インスタンス

    arrow = arrows[0]               # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
    
    normR, anglR = arrow[Kn2idx['right_wrist']]                     # 右手首の移動ベクトルの長さと角度
    normL, x = arrow[Kn2idx['left_wrist']]                          # 左手首の移動ベクトルの長さと角度
    normER, x = arrow[Kn2idx['right_elbow']]                        # 右肘の移動ベクトルの長さと角度
    normEL, x = arrow[Kn2idx['left_elbow']]                         # 左肘の移動ベクトルの長さと角度
    
    xy_wristR = keyPoints.xy('right_wrist')                         # 右手首の座標
    xy_wristL = keyPoints.xy('left_wrist')                          # 左手首の座標
    xy_nose = keyPoints.xy('nose')                                  # 鼻の座標

    lenE, x = keyPoints.norm('right_eye', 'left_eye')               # 右目と左目のベクトルの長さと角度を計算
    
    completed = False    
    conf = keyPoints.conf('right_wrist')                            # 右手首の座標の信頼度
    if conf < 0.9 :
        # 右手首の信頼度が低い、または移動ベクトルの長さが0の場合は開始しない
        mylog.log(INFO, f">>>   conf={conf:.2f}  skip....")
        return completed

    mylog.log(INFO, f"completed({section_no}):  boxid={ibox}, H={int(thsd.block_height)}, wristR=[{int(xy_wristR[0])}, {int(xy_wristR[1])}],"\
            + f"    normR={int(normR)}({thsd.ratio(normR):.3f}), anglR={int(anglR)}°, conf={conf:.2f}")

    if section_no == 1:  # 1-Asi-bumi
        normN, x = arrow[Kn2idx['nose']]                        # 鼻の移動ベクトルの長さと角度
        conf = keyPoints.conf('right_eye')                      # 右目座標の信頼度
        if conf >= 0.92:  # 右目の信頼度が0.9以上の場合            
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), normN={int(normN)}({thsd.ratio(normN):.3f}), "\
                        + f" lenE={int(lenE)}({thsd.ratio(lenE):.3f}), conf={conf:.2f}") 
                     
            mylog.log(INFO, f">>>   [ normR <= {int(thsd(0.015))} and normL <= {int(thsd(0.015))} and (normN <= {int(thsd(0.015))}) and (lenE >= {int(thsd(0.015))} ]")
            if (normR <= thsd(0.015) and normL <= thsd(0.015)) and (normN <= thsd(0.015)) and (lenE >= thsd(0.015)) :
                # 右手首と左手首の移動ベクトルの長さが10未満、鼻の移動ベクトルの長さが10未満、
                # 右目と左目のベクトルの長さが15以上
                arrow = arrows[1]               # 前前回キーポイントの移動ベクトルの長さと角度を格納するリスト
                if arrow is None:
                    mylog.log(INFO, f">>>   arrow[1] is None")
                    return completed
                normR, anglR = arrow[Kn2idx['right_wrist']]                     # 右手首の移動ベクトルの長さと角度
                normL, x = arrow[Kn2idx['left_wrist']]                          # 左手首の移動ベクトルの長さと角度
                mylog.log(INFO, f">>>   normR={int(normR)}({thsd.ratio(normR):.3f}), normL={int(normL)}({thsd.ratio(normL):.3f})")
                mylog.log(INFO, f">>>   [ normR <= {int(thsd(0.025))} and normL <= {int(thsd(0.025))} ]")
                if normR <= thsd(0.025) and normL <= thsd(0.025):  completed = True
                
    elif section_no == 2:  # 2-Dou-zukuri
        lenER, angER = keyPoints.norm('right_elbow', 'right_wrist')             # 右肘から右手首へのベクトルの長さと角度を計算
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), lenER= {int(lenER)}({thsd.ratio(lenER):.3f}),"\
                        f" angER= {int(angER)}")
        if (normR < 10 and normL < 10) and  lenER > 55 and (angER > 50 and angER < 75):
            # 右手首と左手首の移動ベクトルの長さが10未満、右手首と右股関節のベクトルの長さが100未満の場合
            arrow = arrows[2]               # 前前回キーポイントの移動ベクトルの長さと角度を格納するリスト
            normR, anglR = arrow[Kn2idx['right_wrist']]                     # 右手首の移動ベクトルの長さと角度
            normL, x = arrow[Kn2idx['left_wrist']]                          # 左手首の移動ベクトルの長さと角度
            mylog.log(INFO, f">>>   normR={int(normR)}({thsd.ratio(normR):.3f}), normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                          + f" count={Step_counter}")
            mylog.log(INFO, f">>>   [ normR < {int(thsd(0.025))} and normL < {int(thsd(0.025))})")
            if normR <= thsd(0.025) and normL <= thsd(0.025) :
#           if normR <= 15 and normL <= 15 :
                Step_counter = Step_counter + 1
                if Step_counter == 4:  completed = True
                
    elif section_no == 3:  # 3-Yu-gamae
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), normER={int(normER)}({thsd.ratio(normR):.3f}),"\
                      + f" normEL={int(normEL)}({thsd.ratio(normEL):.3f}), lenE={int(lenE)}({thsd.ratio(lenE):.3f})"\
                      + f" count={Step_counter}")
        mylog.log(INFO, f">>>   [ Step_counter == 0 and lenE < {int(thsd(0.025))} ]")
        if Step_counter == 0 and lenE < 15:
            Step_counter = Step_counter + 1
        else:
            mylog.log(INFO, f">>>   [ Step_counter == 1 and (normR < {int(thsd(0.017))} and normL < {int(thsd(0.017))})"\
                          + f" and (normER < {int(thsd(0.017))} and normEL < {int(thsd(0.017))}) and lenE > {int(thsd(0.025))} ]")
            if Step_counter == 1 and (normR < 10 and normL < 10) and (normER < 10 and normEL < 10) and lenE > 15:
                # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満、右目と左目のベクトルの長さが10未満の場合
                completed = True
            
    elif section_no == 4:  # 4-Uti-okosshi
        mylog.log(INFO, f">>>   y_nose={int(xy_nose[1])}, y_R={int(xy_wristR[1])}, y_L={int(xy_wristL[1])}")
        if (xy_wristR[1] < xy_nose[1] and xy_wristL[1] < xy_nose[1]):
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                          + f"normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normEL)}({thsd.ratio(normEL):.3f})")
            mylog.log(INFO, f">>>   [ (normR < {int(thsd(0.017))} and normL < {int(thsd(0.017))}) and (normER < {int(thsd(0.017))} and normEL < {int(thsd(0.017))}) ]")
            if (normR < thsd(0.017) and normL < thsd(0.017)) and (normER < thsd(0.017) and normEL < thsd(0.017)): completed = True
#           if (normR < 10 and normL < 10) and (normER < 10 and normEL < 10): completed = True
            # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満
            # （右手首と左手首が鼻より高い位置で停止）
            
    elif section_no == 5:  # 5-Hiki-wake
        mylog.log(INFO, f">>>   y_nose={int(xy_nose[1])}, y_R={int(xy_wristR[1])}, y_L={int(xy_wristL[1])}")
        if (xy_wristR[1] > xy_nose[1] and xy_wristL[1] > xy_nose[1]):
            mylog.log(INFO, f">>>   count={Step_counter}, normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                          + f" normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normL)}({thsd.ratio(normEL):.3f})")
            mylog.log(INFO, f">>>   [ (normR < {int(thsd(0.025))} and normL < {int(thsd(0.017))}) and (normER < {int(thsd(0.017))} and normEL < {int(thsd(0.017))}) ]")
            if (normR < thsd(0.025) and normL < thsd(0.017)) and (normER < thsd(0.017) and normEL < thsd(0.017)) :
#           if (normR < 15 and normL < 10) and (normER < 10 and normEL < 10) :
                # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満（姿勢の保持で完了）
                Step_counter = Step_counter + 1
                if Step_counter == 5:  completed = True
                
    elif section_no == 6:  # 6-Kai
        mylog.log(INFO, f">>>   count={Step_counter}, normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                      + f" normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normEL)}({thsd.ratio(normEL):.3f}) ")
        mylog.log(INFO, f">>>   [ (normR < {int(thsd(0.017))} and normL < {int(thsd(0.017))}) and (normER < {int(thsd(0.017))} and normEL < {int(thsd(0.017))}) ]")
        if (normR < thsd(0.017) and normL < thsd(0.017)) and (normER < thsd(0.017) and normEL < thsd(0.017)) :
#       if (normR < 10 and normL < 10) and (normER < 10 and normEL < 10) :
            # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満（姿勢の保持で完了）
            Step_counter = Step_counter + 1
            if Step_counter == 5:  completed = True
            
    elif section_no == 7:  # 7-Hanare
        Step_counter = Step_counter + 1
        mylog.log(INFO, f">>>   count={Step_counter}")
        if Step_counter > 5: completed = True
        
    elif section_no == 8:  # 8-Zan-shin
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), count={Step_counter}")
        mylog.log(INFO, f">>>   [ normR < {int(thsd(0.05))} and normL < {int(thsd(0.05))} ]")
        if normR < thsd(0.05) and normL < thsd(0.05):
#       if normR < 15 and normL < 15:
            # 右手首と左手首の移動ベクトルの長さが50以下の場合（姿勢の保持で完了）
            Step_counter = Step_counter + 1
            if Step_counter == 3:  completed = True
            
    elif section_no == 9:  # 8-Zan-shin(ダミー：弓倒し)
            pass
            
    else:
        mylog.log(ERROR, f">>>  section_no={section_no}は未定義のセクションです")
        completed = False
    #
    mylog.log(INFO, f">>>   completed({section_no}): completed={completed}")
    return completed
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
        if result.boxes.conf[i].item() < 0.3: continue  # 信頼度が低いボックスは無視
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
def get_camera_pos(result, ibox):
    """
    :param result: YOLOv8の検出結果
    :param ibox: ボックスのインデックス
    :return: カメラの位置（’’）
    """
    keyPoints = Keypoint(result, ibox)           # キーポイントのデータ解析インスタンス
    thsd = Threshold(keyPoints.block_height)     # バウンディングボックスの高さを基準に閾値設定インスタンス

    # 検出されたバウンディングボックスの取得
    x, y, w, h = map(int, result.boxes.xywh[ibox])

    length, angle = keyPoints.norm('right_shoulder', 'left_shoulder')       # 右肩と左肩のベクトルの長さと角度を計算
    
    mylog.log(DEBUG,  f"[get_camera_pos]: ibox={ibox}, xywh=[({x}, {y}), ({w}, {h})],"\
                    + f" length={length:.2f}, angle={angle:.2f}°, (length/H)={thsd.ratio(length):.3f}")

    ipos = 0
    mylog.log(DEBUG,  f"[get_camera_pos]: length < {int(thsd(0.1))}")
    if length < thsd(0.1):  # 右肩と左肩のベクトルの長さが100未満の場合
        ipos = 2    # Right-side
    elif angle > -45 and angle < 45 :  # 
        ipos = 1    # Front
    else:  # 
        ipos = 3    # Upper    
    
    mylog.log(DEBUG, f"[get_camera_pos]: Camera_pos={Camera_pos[ipos]}")
    return Camera_pos[ipos]
#
#キーポイントをフレームに描画する関数
'''
    #:param annotated_frame: 描画対象のフレーム
    #:param keypoints: キーポイントの座標と信頼度
    #:param ibox: 最大ボックスのインデック
    #:param idxs: キーポイントのインデックスリスト
    #:param color: キーポイントの色
    #:param weight: 線の太さ
    #:param radius: キーポイントの半径（Noneの場合は描画しない）
'''
def draw_kpt_line(annotated_frame, keypoints, ibox, idxs,  color=(0, 255, 0), weight=2, radius=None):
    for i, idx  in enumerate(idxs):
        if keypoints.conf[ibox][idx].item() < 0.3: break
        if i == 0:
            x1, y1 = map(int, keypoints.xy[ibox][idx])
            if x1 == 0 or y1 == 0: break
        else:
            x2, y2 = map(int, keypoints.xy[ibox][idx])
            if x2 == 0 or y2 == 0: break
            cv2.line(annotated_frame, (x1, y1), (x2, y2), color, weight)  # 緑色のライン
            x1, y1 = x2, y2  # 次のラインの始点を更新
        if radius is not None:
            # キーポイントの半径が指定されている場合、キーポイントを描画
            cv2.circle(annotated_frame, (x1, y1), radius, color, -1)
#
# キーポイントの接続ラインを描画する関数
#
def draw_kpts_line(annotated_frame, keypoints, ibox):
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
    
    mylog.log(DEBUG, f"draw_kpts_line:keypoints.xy:{keypoints.xy.shape}, keypoints.conf:{keypoints.conf.shape}")

    # キーポイントの接続ラインを描画
    draw_kpt_line(annotated_frame, keypoints, ibox, arm_line,  color=(0, 255, 0), weight=2, radius=3)   # 右手首ー＞左手首 
    draw_kpt_line(annotated_frame, keypoints, ibox, body_line, color=(0, 255, 0), weight=2, radius=3)   # 胴体
    #draw_kpt_line(annotated_frame, keypoints, ibox, legR_line, color=(255, 0, 0), weight=2, radius=3)   # 右脚
    #draw_kpt_line(annotated_frame, keypoints, ibox, legL_line, color=(255, 0, 0), weight=2, radius=3)   # 左脚
    draw_kpt_line(annotated_frame, keypoints, ibox, eye_line,  color=(255, 0, 0), weight=2, radius=3)   # 目

#
# 検出結果をフレームに描画する関数
#
def plot(result, prepoints_buffer=None, annotated_frame=None):
    global Section_no, Split_start, Split_sec, Lap_sec, Completed, Step_counter
    mylog.log(DEBUG, f"[plot]: {type(result.keypoints)},{len(result.keypoints)}個のキーポイント")

    if annotated_frame is None:
        # YOLOv8のplot関数を使用してフレームに描画  
        # 　kpt_line=False： キーポイントのマークのみを描画）
        annotated_frame = result.plot(boxes=False, labels=False, kpt_line=True, kpt_radius=2)
    else:    
        # 面積最大のボックスを取得 
        max_no = get_max_box(result)  
        if max_no == 0:                     
            # 対象ボックスの判定できないときは手動での描画はしない
            mylog.log(INFO, f"[plot]: 対象ボックスの判定不可")
            return annotated_frame
        # 対象ボックスのキーポイントの左（右）手首座標データの信頼度を取得
        conf = result.keypoints.conf[max_no - 1][Kn2idx['right_wrist']].item()  # 右手首の信頼度を取得
        if conf < 0.75: #       信頼度が0.93未満の場合は描画しない
            mylog.log(INFO, f"[plot]: 対象ボックスのキーポイントの信頼度が低いので描画しない: conf={conf:.2f}")
            return None
        # 対象ボックスのキーポイントの接続ラインを描画
        draw_kpts_line(annotated_frame, result.keypoints, max_no - 1)   

        # 前回のキーポイントデータを取得
        prepoints = prepoints_buffer.get(1)     
        boxid = prepoints['boxid']                              # 前回のボックスID
        if boxid != -1:
            mylog.log(DEBUG, f"{type(prepoints['keypoints'])},{len(prepoints['keypoints'])}個のキーポイント, boxid={boxid}")

        # セクション情報を更新
        camera_pos = get_camera_pos(result, max_no - 1)         # カメラの位置取得
        if (camera_pos == '' or camera_pos == 'Front-side') and boxid  >= 0:
            arrow_length_angles = [None, None, None]            # 各キーポイントの移動ベクトルの長さと角度を格納するリストを初期化（前回、前前回）
            arrow_points = result.keypoints.xy[max_no - 1] - prepoints['keypoints'].xy[boxid]       # 前回のキーポイントとの差分ベクトルを計算
            arrow_length_angles[0] = [vector_length_angle(vect) for vect in arrow_points.numpy()]   # 各ベクトルの長さと角度を計算 
            
            # 前前回のキーポイントデータを取得
            if prepoints_buffer.len() >= 4:
                for i in range(1,3):
                    prepoints = prepoints_buffer.get((i+1))     
                    boxid = prepoints['boxid']                  # 前前回のボックスID
                    if  boxid  >= 0:
                        arrow_points = result.keypoints.xy[max_no - 1] - prepoints['keypoints'].xy[boxid]       # 前前回のキーポイントとの差分ベクトルを計算
                        arrow_length_angles[i] = [vector_length_angle(vect) for vect in arrow_points.numpy()]   # 各ベクトルの長さと角度を計算 
            
            # 射法八節の動作開始、完了を判定する（キー'0'の押下で判定を開始する）
            if Lap_start > 0:    
                if Split_start == 0 or (Section_no == 6 and Completed):     # スプリット秒が0、または開(6)は完了状態の場合
                    # スプリット秒が0の場合、動作の開始を判定
                    if section_started(Section_no, result, max_no - 1, arrow_length_angles):
                        Split_start = time.time()                           # スプリット開始時間を記録
                        Split_sec = 0
                        Step_counter = 0                                    # セクション内の動作カウンター
                        Completed = False                                   # セクションが開始されたら完了フラグをリセット    
                        Section_no = Section_no + 1                         # セクション番号をインクリメント
                        if Section_no == 9: Split_start = 0
                else:
                    # スプリット秒が0でない場合、動作の完了を判定
                    if section_completed(Section_no, result, max_no - 1, arrow_length_angles):
                        Completed = True 
                        if Section_no != 6: Split_start = 0                 # スプリット開始時間をリセット
                        else: # 開(6)は完了状態を計測する
                            Split_start = time.time()                           
                            Split_sec = 0                       
                        Step_counter = 0                                    # セクション内の動作カウンター
        #
        if Lap_start != 0:   Lap_sec = int(time.time() - Lap_start)         # ラップ秒を計算
        if Split_start != 0: Split_sec = int(time.time() - Split_start)     # スプリット秒を計算

        # セクション情報をフレームに描画
        section_color =  (0, 255, 255)      # セクションの色（黄色）BGR
        others_color =  (255, 255, 255)     # その他の色（白）
        if Completed: section_color = (0, 255, 0)       
        
        cv2.putText(annotated_frame, f"camera: {camera_pos}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 2)
        cv2.putText(annotated_frame, f"section: {Section_name[Section_no]}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, section_color, 2)
        cv2.putText(annotated_frame, f"split   : {Split_sec:6d}sec.", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 2)
        cv2.putText(annotated_frame, f"lap    : {Lap_sec:6}sec.", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 2)
    #
    return annotated_frame


def main(): 
    global Section_no, Split_sec, Split_start, Lap_sec, Lap_start, Completed
    #
    # start of main
    #
    cam_id = None                                   # デフォルトのカメラID
    raw_image = False                               # 生画像を表示するオプション
    manual_plot = False                             # 手動でプロットするオプション
    idir = 'C:/Users/USER/Pictures/Camera Roll/'    # 初期ディレクトリを指定
#   idir = 'C:/Users/staff/OneDrive/画像/カメラロール/'    # 初期ディレクトリを指定
    ALL_TYPES = "*.*"                               # 動画ファイル名[*.mp4;*.avi;*.mov;*.mkv"]
    timestamp = datetime.now().strftime('%Y%m%d')
    filetypes = f"WIN_{timestamp}_*.mp4"            #'*WIN_YYYYmmdd_10_46_55_Pro.mp4'  # 動画ファイル名
    iwait = 1                                       # ウィンドウの更新間隔（ミリ秒）
    milsec = 0  # ミリ秒
    attention = 0
    prePointsBuffer = RingBuffer(4)     # 検出結果を保存するリングバッファ（4回分を保存）                           
    preFrame = None                     # 前回のフレームを保存する変数
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
    if '-v' in opts:
        logger.disabled = False  # ログ出力を有効化
    
    if '-r' in opts:
        raw_image = True  # 生画像を表示するオプション
        iwait = 10
    if '-m' in opts:
        manual_plot = True
    
    if '-a' in opts:
        filetypes = ALL_TYPES   
        
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
    mylog.log(INFO,"YOLOv8 Pose Detectionを開始します")
    model = YOLO('yolov8n-pose.pt')  # 軽量モデル。他にも'yolov8s-pose.pt'などあり
    model.info()  # モデル情報を表示
    #
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if raw_image is True:
            # 生画像を表示する場合
            annotated_frame = frame
        else:
            # YOLOで骨格検出
            results = model.predict(frame)
            if len(results) == 0 or len(results[0].keypoints) == 0:
                mylog.log(INFO, "検出結果がありません")
                continue
            # 1秒ごとに検出結果を保存
            ms = time.time()*1000
            if Lap_start != 0 and (int(ms/1000) != int(milsec/1000)):
                mylog.log(INFO, f"[main]: {datetime.now().strftime('%H-%M-%S')}:検出結果保存: {type(results)}, {len(results)}個の結果,{int(ms/1000)}sec")
                points =  { 'boxid': -1, 'keypoints': None }                        
                points['boxid'] =  get_max_box(results[0]) - 1  # 面積最大のボックスを取得
                points['keypoints'] = results[0].keypoints
                # 検出結果を保存                        
                prePointsBuffer.append(points)                        
                milsec = ms
                   
            # 検出結果をフレームに描画
            if manual_plot is True:
                annotated_frame = frame
                if prePointsBuffer.len() > 1:
                    # 生画像に手動でを表示
                    annotated_frame = plot( results[0], prePointsBuffer, frame)
                    if annotated_frame is None and preFrame is not None:  # 前回のフレームを描画
                        annotated_frame = preFrame
                        mylog.log(INFO, "[main]: 前回フレームを描画")
            else:
                # YOLOのplot関数を使用してフレームに描画
                annotated_frame = plot( results[0] )
    
        # ウィンドウに表示
        cv2.imshow('YOLO Pose Detection', annotated_frame)
        preFrame = annotated_frame.copy()  # 前回のフレームを保存
        
        if imgWriteEnabled:
            # 出力ファイルに書き込み
            cv2Video.write(annotated_frame)
        #キー入力をチェックするする
        key = cv2.waitKey(iwait) & 0xFF
        if key == -1: 
            # キー入力がない場合は次のフレームへ
            continue
        # キー入力に応じて処理を実行
        if key == ord('q'):
            # 'q'キーで終了
            break
        elif key == ord('s'):
            # スクリーンショットを保存
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"{idir}screenshot_{timestamp}.png"
            cv2.imwrite(screenshot_path, annotated_frame)
            print(f"スクリーンショットを保存しました: {screenshot_path}")
        elif key == ord('o') and out_file != '' and not imgWriteEnabled:
            imgWriteEnabled = True
            print(f"出力ファイルに書き込みを開始します: {out_file}")
        elif key == ord('c') and imgWriteEnabled:
            imgWriteEnabled = False
            print("出力ファイルへの書き込みを停止します")
        elif key >= ord('0') and key <= ord('8'):
            # セクション番号を設定
            Section_no = key - ord('0')
            print(f"セクション番号を設定: {Section_no}")
            Completed = False
            Split_sec = 0
            Split_start = 0
            if Section_no == 0:
                Lap_start = time.time()  # ラップ開始時間を記録
                Lap_sec = 0
                milsec = time.time() * 1000  # ミリ秒を記録
            else: 
                Split_start = time.time()
        elif key == ord('9'):
            Lap_start = 0
        elif key == ord('.'):
            if iwait > 1: iwait = iwait - 1
            print(f"(>)down iwait={iwait}")
        elif key == ord(','):
            iwait = iwait + 1
            print(f"up(<) iwait={iwait}")
        elif key == ord('a'):
            attention += 1
            mylog.log(INFO, f"!!Attention({attention})-{chr(key)}")
            print(f"アテンション({attention})ー{chr(key)}")
    #
    # リソースの解放
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