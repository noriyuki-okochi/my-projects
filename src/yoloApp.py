import cv2
from ultralytics import YOLO
import ultralytics

import tkinter.filedialog as filedialog
import sys
import os
import time
from datetime import datetime
from copy import copy 
import numpy as np
import pandas as pd
import copy

# local package
from kyudo.env import * 
from kyudo.param import * 
from kyudo.appUtil import * 
from kyudo.kyudoModel import * 
from kyudo.evalModel import *
from kyudo.kyudoUtils import *
from mysqlite3.mysqlite3 import MyDb

# local module
from gruAnal import gru_analize
from manAnal import manual_analize_start
from manAnal import manual_analize_completed
from manAnal9 import manual_analize_start_L9
from manAnal9 import manual_analize_completed_L9
import kyudo.globals as g

# Ultralytics YOLOv8とアプリ専用のロガー設定
logger = logging.getLogger('ultralytics')
logger.disabled = True                      # ログ出力を無効化

mylog = logging.getLogger(__name__)
filehandler = logging.FileHandler('./log/yoloApp.log', mode='w')  # ログファイルの設定
filehandler.setFormatter(formatter)         # フォーマッタをハンドラに設定
mylog.addHandler(filehandler)               # ログファイルハンドラを追加


#　アプリケーションのグローバル変数の定義
Debug_opt:int = 0               # デバッグレベル
Camera_position:int = 0         # カメラの位置（0:未定義、1:前面、2:右側面、3:上面）
CameraPos_name = ['', 'Front-side', 'Right-side', 'Upper-side']  # カメラの位置
Fps:float = 30                  # フレームレート
Action:int = 0                  # アクション（予測結果）
Section_color:list = YELLOW     # セクションの色（黄色）BGR
Alart_message:str = ''          # アラートメッセージ

# トラッキングフラグ
Tracking_only:bool = False      # トラッキングフラグ
Tracking_enabled:bool = False   # トラッキングオン
Tracking_onece:bool = False     # トラッキング開始済
Update_tracking:bool = False    # DBのトラッキングデータ(section,completed)更新
Update_enabled:bool = False     # DBのトラッキングデータ更新オン
# データベースのインスタンスを作成
Db = MyDb(DB_PATH)  
Db.mode = 'csv'                 # 解析結果のトラッキングデータをCSVファイルに出力する

# 評価のインスタンスを生成
Eval = MyEval()
Eval_enabled:bool = False       # 評価オン
# GRUモデル
Input_key:int = Current_feature_key  # 使用する特徴量の個数(6,7,8)
Num_input:int = Input_dim       # 入力データ次元数
Num_frames = Sequence_frames    # 入力シーケンスのフレーム数
Num_classes:int = Output_dim    # 出力クラス数（ラベル[0=移行,1=完了,2=開始]の区分数）
# YOLOv8モデル
V8_model:str = 'v8s'            # YOLOv8のモデルファイル名
Level:int = 0                   # 解析パラメータレベル（0-3,9）
# ビデオ出力設定
Cv2Video = None                 # OpenCVのビデオライターインスタンス
Add_alpha:float = float(ADD_WEIGHT)   # 画像重ねのアルファ値
Add_beta:float = 1.0 - Add_alpha

#
# YOLOv8とOpenPoseの組み合わせ例（Ultralytics YOLOv8 + YOLOv8-poseモデル利用）
# このコードは、YOLOv8を使用してカメラまたは動画ファイルから骨格検出を行うものです。
# YOLOv8-poseモデルは、Ultralyticsの事前学習済みモデルを使用しています。
def help():
    print(" --- command ---")
    print(" python ./src/yoloApp.py {-c [<id>]|-a|-o <case1_name>[,<case2_name>]} [-clip|-multi [[<frame1_no>],[<frame2_no>]|-r|{-m|-t|-u} <case_name>]\n"\
        + "                         [-gru <model-path> [inputkey=6|7|8]] [classes=3|19]] [-s<step-no>]\n"\
        + "                         [-f'<frame_count>[.<lag>]'] [-W<window_size>] [-V{8|26}{n|s|m}]  [-eval [<model-path>]] [-rortate] [-w [<fps>]] [-z]\n"\
        + "                         [{-{p|P}'(<section-no>,<index>)=<value>'}...] [{-S(<section-no>}...]\n"\
        + "                         [-I ['<frame_name>' -s<step-no>]] [-g[<level>[<color>]]]\n"\
        + "                         [-kpt <no>] [-h] [-v] [-d<debug-level>] [--] [-at <frame_no>]")
    print(" --- Notation---")
    print(" '|': or,  '[]': optional,  '{}': group,  '...': repeat,  '<>': value")
    print(" --- Option ---")
    print(" -c <id>: camera id (default=0)")
    print(" -a(ll-video-file)")
    print(" -o <case_name>: specify the case name")
    print(" -m(anual-plot::dont use YOLO plot)")
    print(" -gru(:analize with RNN-model)")
    print(" -s(kill):skill-level default=1(0-3,9)")
    print(" -r(aw-video)")
    print(" -clip(:raw-video)")
    print(" -rotate(:90°clockwise): enabled only '-r' or '-clip'")
    print(" -multi(-video-layer display)")
    print(" -t(racking::create-csvfile)")
    print(" -u(pdate tracking_data in table)")
    print(" -f(rame-count) and lag for sampling data: default=1.7")
    print(" -W(window-size::ring-buffer-size: default=8)")
    print(" -V(8-pose model-file):default=v8s")
    print(" -eval(:print rating score)")
    print(" -w(rite-video-file) <FPS-multi-ratio>")
    print(" -z(:hide the faces by mosaic)")
    print(" -p(arameter set in StartAction_parames)")
    print(" -P(arameter set in g.CompletedAction_parames)")
    print(" -S(kip illegal-action-check): section-no=3,5")
    print(" -I(nitial entry to act_table from Actin_params::<frame_name><step-no>')")
    print(" -kpt <no>: draw key-point-line type:1=upper,2=right-side,3=front(default),0=yolo standard")
    print(" -h(elp)")
    print(" -g(uidance)<level><color>::[0|1|2|3]:0=dont display(default=3):[Y|G|B|W]: yellow, green, black, white")
    print(" -v(erborse)")
    print(" -d(ebug-level)<0-3>: 0:none, 1:info, 2:debug, 3:more-debug")
    print(" -at <frame_no>: auto-pause at the specified frame number")
    print(" --:auto-pause imidiately after starting the processing")
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
    print(" z :ズーム領域を指定してズーム再生開始（終了はクリア'c'キー押下）")
    print(" g :グリッド表示・非表示（分割数は数値入力キー’i’で指定：：(0|1)(<分割数>),0=行,1=列）")
    print(" G :グリッド表示シフト（シフト量は数値入力キー’i’で指定：：(0|1)(グリッド幅の割合<分子><分母>)）")
    print(" 0 :姿勢解析開始")
    print(" 1-8:節の開始")
    print(" Sp:節の完了移行")
    print(" Tb:次節の完了")
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
#Stkp = StackActParam()  
#
# 動作解析パラメータテーブルをログファイルに出力する
def print_param(tbl):
    mylog.log(INFO, f"frame:{tbl['frame']}, step = {tbl['step']}, act = {tbl['act']}")
    for sect, raw_vals in enumerate(tbl['param']):
        mylog.log(INFO, f"({sect:2d}): {raw_vals}") 
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
        #ipos = 3    # Upper    
        ipos = 2    # Right-side
    
    if ipos != Camera_position:
        # カメラの位置が変更された場合、ログに記録
        mylog.log(INFO,  f"[get_camera_pos]: conf-R={keyPoints.conf('right_shoulder'):.3f}, conf-L={l_conf:.3f},"\
                       + f" length-S={length:.2f}({thsd.ratio(length):.3f}), angle-S={angle:.2f}°, length-H={length_h:.2f}({thsd.ratio(length_h):.3f})")
        mylog.log(INFO, f"[get_camera_pos]: [ length-S < {thsd(0.120):.3f} and length-H < {thsd(0.08):.3f} ]")
        mylog.log(INFO, f"[get_camera_pos]: Camera_position={ipos}({CameraPos_name[ipos]})")

        Camera_position = ipos
    return CameraPos_name[ipos]
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
        shouls_norm, _ = keyPoints.norm('right_shoulder','left_shoulder')   # 左肩から左肩ベクトルの長さと角度を計算
        
        # グローバル変数にセット(評価データ参照用)
        g.RL_angle = rl_angle
        g.HR_angle = hr_angle
        g.SR_angle = sr_angle
        g.SL_angle = sl_angle
        g.ER_angle = rew_angle
        g.RSE_angle = rse_angle
        # アクション発生後の経過時間（x10秒）
        # act_sec = int( (g.Lap_sec - g.Action_start)*10 ) if g.Action_start > 0.0 else 0
        # 体の向き（0/1=的方向／正面向き）
        shouls_ratio = shouls_norm/box_h
        xy_conf = keyPoints.conf('left_shoulder')                  # キーポイントの信頼度(Numpy)
        
        body_front:int = 0 if xy_conf < 0.9 else \
                    (1 if shouls_ratio > Body_front_threshold else 0)    
        if g.Section_no >= 2 and g.Section_no <= 9:
            # 胴づくりー＞湯倒しは体正面向きに固定
            body_front = 1

        # 顔の向き（0/1/2=不定／正面／横）
        eyes_ratio = eyes_norm/box_w
        g.EYE_ratio = eyes_ratio
        
        face_front:int = 0
        if Level == 9: # Right-side
            eye_conf = keyPoints.conf('right_eye')                 # 右目の座標の信頼度
            face_front = 2 if eye_conf > Face_front_threshold9 else 1
        else:          # Front-side
            eye_conf = keyPoints.conf('left_eye')                  # 左目の座標の信頼度
            face_front = 0 if eyes_ratio > 0.5 else \
                        (1 if eyes_ratio > Face_front_threshold else 2)    
            if g.Section_no >= 4 and g.Section_no <= 8:
                # 打ちお越しー＞残身は顔の向きを横に固定
                face_front = 2
            
        # 解析データリストを作成
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
                    face_front, body_front]
                #   face_front, act_sec]
        # データリストをセット
        inputPdf.set_kyudo_data_list( data_list )  
    
    return
#
# 特徴量データフレームのインスタンス
InputPdf:FeaturePdf = None
#
# 表示セクション名と色を返す関数 
def edit_section_name(no, counter):
    # セクション名を編集する
    name = Section_names[no]    
    if counter > 0:                     # セクション内の動作カウンターが1以上の場合、セクション名にカウンターを追加
        stepKey = no*100 + counter
        #print(f"stepKey={stepKey}")
        if stepKey in Step_names:
            name += f"（{Step_names[stepKey]}）"            # 大三 etc.
            if stepKey == 511: name += f" {g.Push_counter:2d}"
            elif stepKey == 512: name += f" {g.Pull_counter:2d}"
        else :
            if Debug_opt > 1 : name += f"（{counter}）"     # その他
            else : pass   
    # セクションの色を設定    
    if g.Step_error or Section_color == RED: 
        if g.Section_no > (g.Alart_section + 1) or g.Section_no == 0 or g.Section_no == 9:
            # セクション番号がアラートセクション番号より2以上大きい場合、アラート表示をクリア
            color = YELLOW
        else:  color = RED                      # 不正な動作のセクションの色（赤色）BGR
    else:
        color =  YELLOW                         # セクションの色（黄色）BGR
        if g.Completed: color = GREEN             # 完了したセクションの色（緑色）BGR

    return name, color
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
        if out_file != '':  ope_str += ':(w)rite'
        if Tracking_only:   ope_str += ':(t)racking'
        if Update_tracking: ope_str += ':(u)pdate-tracking'
        if raw_video and (not clip_video):   ope_str += ':(r)epeat'
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
    return cv2.addWeighted(frame1, Add_alpha, frame2, Add_beta, 0) 
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
Rect_area: Rect = Rect()
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
        mylog.log(DEBUG, f"[get_mosaic_areas]:{i}:({y}, {x}, {x1}, {x2}, {w})")

        areas.append( [int(y - w/4), int(x - w/3), int(w/1.5), int(w/1.5)] )  # 矩形情報を追加
    return areas
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
# ズーム処理
#
def zoom_area( src, y, x,  height, width, frame_width, frame_height ):
    if y <= 0 or (y + height) >= frame_height: return src   
    x = 0 if x < 0 else x
    x = frame_width - width if (x + width) >= frame_width else x    
    dst_area = src[y:y + height, x:x + width]
    zoom = cv2.resize(dst_area, dsize=(frame_width, frame_height), interpolation=cv2.INTER_LINEAR)
    return zoom

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
def clip_process( frame , rotate = False):
    global Rect_area
    rectAreas:Rect = []
    # クリッピング・ウィンドウとマウスイベント・コールバック登録
    cv2.namedWindow("Select ROI")
    cv2.setMouseCallback("Select ROI", draw_rectangle)
    # クリッピング処理
    h, w = frame.shape[1], frame.shape[0]
    ratio = h/w if h < w else w/h    
    while True:
        temp_frame = frame.copy()   # 読み込んだ先頭フレーム上で矩形領域を指定する    
        if rotate:
            temp_frame = cv2.resize(temp_frame, dsize=None, fx=ratio, fy=ratio , interpolation=cv2.INTER_NEAREST)
            temp_frame = cv2.rotate(temp_frame, cv2.ROTATE_90_CLOCKWISE)
            
        for rect in rectAreas:
            # 指定済み矩形のライン描画
            cv2.rectangle(temp_frame, rect.start, rect.end, GREEN, 1)
            
        if Rect_area.drawing and Rect_area.start and Rect_area.end:
            # 矩形のライン描画
            cv2.rectangle(temp_frame, Rect_area.start, Rect_area.end, GREEN, 2)
        # キーオペレーションのヘルプ表示
        hight, _ = temp_frame.shape[:2]
        help_str = "r(eset)|c(onfirm)|p(ass)|q(uit)"
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
        elif key_val == ord("q"):
            # 処理を中断
            rectAreas.clear()
            break
        elif key_val == ord("p"):
            # クリッピング処理をパス
            rectAreas.clear()
            break
        elif key_val == ord("c"):
            # 指定を確定
            break
    #
    cv2.destroyWindow("Select ROI")
    if key_val == ord("q") : return  None   # 以降の処理を中断してプログラムを終了
    if len(rectAreas) == 0:
        #print(f"クリッピング領域を指定してください。")
        #return rectAreas
        Rect_area.start = (0, 0)
        Rect_area.end = (frame.shape[1], frame.shape[0])
        rectAreas.append( copy.copy(Rect_area) )
    return copy.deepcopy( rectAreas )
#
# 検出結果をフレームに描画する関数
#
def plot(myResult:MyResult, annotated_frame, output_dim=None, nn_gru=False, model=None, evalModel=None, evalInput_dim=None):
    global Action
    global Section_color, Alart_message, Eval
    
    result = myResult.result
    mylog.log(DEBUG, f"Tracking_enabled={Tracking_enabled}")
    mylog.log(DEBUG, f"[plot]: {type(result.keypoints)},{len(result.keypoints)}個のキーポイント")

    #if annotated_frame is None:
        # YOLOv8のplot関数を使用してフレームに描画  
        # 　kpt_line=False： キーポイントのマークのみを描画）
        #annotated_frame = result.plot(boxes=True, labels=False, kpt_line=True, kpt_radius=3)
    #else:    
    # 対象ボックスのキーポイントの接続ラインを描画
    myResult.plot(annotated_frame)   

    if g.Section_no < 2: 
        # カメラの位置取得（足踏み完了まで）
        g.CameraPos = get_camera_pos(myResult)                

    # セクション情報を更新
    arrows = myResult.arrow_length_angles       # キーポイントの移動ベクトルの長さと角度を取得
    
    if g.CameraPos in ['Right-side', 'Front-side'] and arrows[Sample_lag] is not None:
        if Tracking_enabled or nn_gru:
            # 姿勢解析入力データリストを作成、保存しておく
            tracking_result(myResult, InputPdf, output_dim, csvout=False)
        # 姿勢解析結果のキーポイントの座標変位から、射法八節の動作の開始、完了を判定する
        if g.Lap_start > 0:    
            # 射法八節の動作開始、完了を判定する（キー'0'の押下で判定を開始する）
            g.Step_error = False
            g.Alart_id = 0
            p_section = g.Section_no
            if nn_gru:
                # GRUモデルによる姿勢解析
                # カレントのデータフレームを作成、保存
                n = InputPdf.set_current_pdf(g.Section_no, g.Completed)
                if n == 0:
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
                        g.Section_no, g.Completed, Action = gru_analize(g.Section_no, g.Completed, model, input_pdf)
                        mylog.log(INFO, f"[gru_analize_o]: Section={g.Section_no}, g.Completed={g.Completed}, Action={Action}")
                        InputPdf.update_previous_pdf()
                else:
                    mylog.log(INFO, f"[plot]: set_current_pdf returned n={n}")
                
            # ハイブリッドモデルの場合、プログラムロジックによる姿勢解析も行う
            if not nn_gru or g.Hybrid_model:
                # プログラムロジックによる姿勢解析
                if g.Section_no == 0 or g.Completed:
                    # 動作の開始を判定
                    g.Section_no, g.Completed = manual_analize_start(g.Section_no, myResult) if Level != 9 \
                                            else manual_analize_start_L9(g.Section_no, myResult)
                else:
                    # 動作の完了を判定
                    g.Section_no, g.Completed = manual_analize_completed(g.Section_no, myResult) if Level != 9 \
                                            else manual_analize_completed_L9(g.Section_no, myResult)
            #
            if g.Section_no != p_section and g.Section_no == 5: 
                g.Pull_counter,g.Push_counter = 0,0     # 「引き分け」引き・押しのカウンターリセット
                
            Db.section = g.Section_no                 # トラッキングデータのセクション番号を設定 
            Db.step_counter = g.Step_counter          # トラッキングデータのセクション内の動作カウンターを設定             
            Db.completed = 1 if g.Completed else 0

            if Tracking_enabled:
                # 解析結果のデータをCSVに出力する
                tracking_result(myResult, InputPdf, output_dim, csvout=True)
            if Update_enabled:
                # トラッキングデータのテーブル（'section'/'completed'）を更新する
                Db.update_tracking_section()  
                if g.Step_error: Db.update_tracking_tag( 'tag1', 9 ) # 不正動作を登録
    #
    # セクション情報をフレームに描画
    if g.Lap_start > 0:   g.Lap_sec = (g.Frame_counter - g.Lap_start)/Fps         # ラップ秒を計算
    if g.Split_start > 0: g.Split_sec = (g.Frame_counter - g.Split_start)/Fps     # スプリット秒を計算
    if g.Section_no < 7:  g.Split_last = 0.0
    #
    # 評価用のデータ保存、採点
    if Eval_enabled:
        bSectionChanged = Eval(g.Frame_counter, g.Section_no, 1 if g.Completed else 0, \
            g.Step_counter, g.Split_sec, \
            g.RL_angle, g.ER_angle, g.SL_angle, g.SR_angle,\
            g.RSE_angle, g.EYE_ratio, g.Alart_id)
        
        if bSectionChanged and evalModel is not None: 
            # 予測実行(predict)
            df_x = Eval.get_eval_pdf(evalInput_dim)     # 評価用の特徴量データフレームを取得
            Eval.df_to_csv()
            df_x = df_x.astype({'section': 'Int64'})    # 整数型に変換する   
            # numpy配列に変換
            x = df_x.to_numpy(dtype=np.float32)         # (input_frames, input_dim)
            pred_score  = predict_Eval( evalModel, x, Eval_sframes ) # x=numpy(input_frames, input_dim)
            sect_no = int(df_x.iloc[-1]['section'])          # 最新のセクション番号を取得
            Eval.scores[sect_no - 1] = pred_score
            #print(f"[predict_Eval]: section({sect_no}) predicted_score={pred_score}")   
            Eval.free_eval_pdf()
    
    # セクション名を編集
    section_name, Section_color = edit_section_name(g.Section_no, g.Step_counter)   
    others_color =  WHITE                       # その他の色（白）

    if g.Alart_id > 0: 
        #　警告メッセージ（全角文字）取得
        Alart_message = Alart_msg[g.Alart_id*10]
        print(f"フレーム({g.Frame_counter}):{Alart_msg[g.Alart_id*10]}")
        mylog.log(INFO, f">>> {Alart_msg[g.Alart_id*10]}")
        
    # テキストの描画 （カメラ位置、セクション名、スプリット秒、ラップ秒、角度）          
    cv2.putText(annotated_frame, f"camera: {g.CameraPos }", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 1)
    
    # 節(g.Section_no)、ステップ(g.Step_counter)情報の描画
    annotated_frame = draw_text(annotated_frame, f"Section : {section_name}", (10, 40),  Section_color)
    
    # 保持時間(split)の描画
    if g.Split_last == 0.0:
        cv2.putText(annotated_frame, f"split   : {g.Split_sec:6.2f}sec.", (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 1)
    else:
        cv2.putText(annotated_frame, f"split   : {g.Split_sec:6.2f}sec. {g.Split_last:6.2f}sec.", (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 1)
    
    # 経過時間(lap)の描画
    cv2.putText(annotated_frame, f"lap    : {g.Lap_sec:6.2f}sec.", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 1)
    
    # 角度情報(XX_angle)の描画
    if g.Section_no == 4 or g.Section_no == 5 or g.Section_no == 6:
        cv2.putText(annotated_frame, f"angle  : {-1*g.RL_angle:6.1f}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 1)
    if g.Section_no == 7 or g.Section_no == 8:
        cv2.putText(annotated_frame, f"angle  : {-1*g.ER_angle:6.1f}  {-1*g.SL_angle:6.1f}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, others_color, 1)
    
    # 警告メッセージの描画
    annotated_frame = draw_text(annotated_frame, Alart_message, (10, 140), RED)
    
    # 評価結果の描画
    if Eval_enabled and Eval.score_on:
        cv2.putText(annotated_frame, Eval.score_text, (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 1)
        # 減点理由の表示
        # annotated_frame = draw_text(annotated_frame, '減点', (10, 200), YELLOW)
        for i, msg in enumerate(Eval.deduct_msgs):
            annotated_frame = draw_text(annotated_frame, f"{i+1}.{msg}", (10, 200 + i*30), GREEN, 18)
#
    return annotated_frame
#
# 節の移行処理
#
def transition_to(section_no, ctl):
    global Section_color, Alart_message
    
    g.Completed = False
    g.Split_sec = 0
    g.Split_start = 0
    g.Step_counter = 0                    # セクション内の動作カウンターをリセット
    g.Nop_counter = 0                     # セクション内の動作カウンターをリセット
    g.Step_error = False                  # 不正な動作フラグ
    Section_color =  YELLOW             # セクションの色（黄色）BGR
    Alart_message = ''                  # アラートメッセージをリセット
    ctl['tag1_section'] = g.Section_no
    ctl['tag2_section'] = g.Section_no
    if g.Section_no == 0:
        g.Lap_start = g.Frame_counter       # ラップ開始時間を記録
        g.Lap_sec = 0.0
        ctl['tag1_section'] = 0         # tag登録用セクション番号
        ctl['tag2_section'] = 0         # tag登録用セクション番号
    else: 
        g.Split_start = g.Frame_counter
        if g.Lap_start > 0: g.Lap_start = g.Frame_counter
        if g.Section_no == 2 and ctl['key_inter'] != 0: 
            # セクション2の連打は動作カウンターを20に設定
            g.Step_counter = 20
    return
#
# キー入力操作関数
#
def key_ope(key, ctl, annotated_frame, cap, idir, out_file, raw_video, clip_video):
    global Section_color, Alart_message, Eval
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
                Db.update_frame_info('start_frame', g.Frame_counter)  # 開始フレーム番号
                Tracking_onece = True
            mylog.log(INFO, f">> Trucking start: {Db.csvpath1}")
        else: 
            print("トラッキングを停止します")
            Db.update_frame_info('stop_frame', g.Frame_counter)   # 停止フレーム番号
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
            if Cv2Video is None:
                # 動画ファイルの書き込みオブジェクトを作成
                frame_height, frame_width = annotated_frame.shape[0:2]
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                Cv2Video = cv2.VideoWriter(out_file, fourcc, Fps*ctl['fps_ratio'], (frame_width, frame_height))
                print(f"出力ファイルに書き込みを開始します: {out_file}: {frame_width}x{frame_height}, Fps={(Fps*ctl['fps_ratio']):.2f}")
                mylog.log(INFO, ">> video write start")
            else:
                print(f"出力ファイルに書き込みを再開します: {out_file}")
                mylog.log(INFO, ">> video write re-start")
        else: 
            print(f"出力ファイルに書き込みを停止します: {out_file}")
            mylog.log(INFO, ">> video write pause")

    elif key == ord('r') and (raw_video and not clip_video):
        if ctl['key_inter'] > 0:
            if not ctl['repeat'] : ctl['start_frame'] = g.Frame_counter       # 繰り返し再生の開始フレームを設定
            else: ctl['stop_frame'] = g.Frame_counter                         # 繰り返し再生の終了フレームを設定
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
                g.Frame_counter = ctl['start_frame']
                cap.set(cv2.CAP_PROP_POS_FRAMES, g.Frame_counter)
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
        g.Section_no = key - ord('0')
        if g.Section_no == 0:
            if Eval_enabled: Eval(section = 0)  # 評価用のデータをリセット 
            print(f"姿勢解析を開始します")
        else:  print(f"セクション番号を設定: {g.Section_no}")

        #  動作開始（節の移行）
        transition_to(g.Section_no, ctl)
        #
        if ctl['key_inter'] == 0: ctl['key_inter'] = int(time.time())  

    elif key == ord('9') and (len(ctl['key_data']) == 0 and len(ctl['para_data']) == 0):
        print(f"姿勢解析を停止します。")
        g.Lap_start = 0                       # ラップ開始時間をリセット 
        g.Split_start = 0                     # スプリット開始時間をリセット 
        g.Step_counter = 0                    # セクション内の動作カウンターをリセット              

    elif key == ord(' '):
        if g.Completed == False:
            #  動作完了
            print(f"動作完了を設定")
            g.Completed = True
            if g.Section_no != 6 and g.Section_no != 8: # 「会」、「残身」はスプリットを計測
                g.Split_start = 0                     # スプリット開始時間をリセット
        else:
            #  動作開始（節の移行）
            g.Section_no = (g.Section_no + 1) if g.Section_no < 9 else 2
            print(f"節の移行: g.Section_no={g.Section_no}")
            transition_to(g.Section_no, ctl)

    elif key == ord('.') and len(ctl['para_data']) == 0: 
                                            # (.) フレームカウンターを2秒進める
        g.Frame_counter += int(Fps)*2     
        cap.set(cv2.CAP_PROP_POS_FRAMES, g.Frame_counter)
        print(f"フレーム={g.Frame_counter}")
        
    elif key == ord('>'):                   # (>) nフレーム進める
        if len(ctl['key_data']) > 1 and ctl['key_data'][1:].isdigit():
            # キー入力データの2文字目以降をフレーム数として設定
            ctl['skipf_frames'] = int(ctl['key_data'][1:])
            ctl['key_data'] = ''            # キー入力データをクリア
        g.Frame_counter += ctl['skipf_frames'] 
        cap.set(cv2.CAP_PROP_POS_FRAMES, g.Frame_counter)
        print(f"フレーム={g.Frame_counter}")
    
    elif key == ord(',') and len(ctl['para_data']) == 0:                   
        # (,) フレームカウンターを2秒戻す
        if g.Frame_counter > int(Fps)*2 :g.Frame_counter -= int(Fps)*2  
        else: g.Frame_counter = 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, g.Frame_counter)
        print(f"フレーム={g.Frame_counter}")
    
    elif key == ord('<'):                   
        # (<) nフレーム戻す
        if len(ctl['key_data']) > 1 and ctl['key_data'][1:].isdigit():
            # キー入力データの2文字目以降をフレーム数として設定
            ctl['skipb_frames'] = int(ctl['key_data'][1:])
            ctl['key_data'] = ''            # キー入力データをクリア
        if g.Frame_counter > ctl['skipb_frames'] :g.Frame_counter -= ctl['skipb_frames']  
        else: g.Frame_counter = 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, g.Frame_counter)
        print(f"フレーム={g.Frame_counter}")

    elif key == ord('j'):
        # 指定フレームへジャンプ                   
        if len(ctl['key_data']) > 1 and ctl['key_data'][1:].isdigit():
            frame = int(ctl['key_data'][1:])
            if frame < 1: frame = 1
            if frame > ctl['frame_count']: frame = ctl['frame_count']
            g.Frame_counter = frame 
            cap.set(cv2.CAP_PROP_POS_FRAMES, g.Frame_counter)
            ctl['key_data'] = ''            # キー入力データをクリア
            print(f"フレーム={g.Frame_counter}")

    elif key == ord('\t') and ctl['at_case'] is not None:
        # 次セクション完了フレームへジャンプ 
        frame = Db.get_frame_no_at(ctl['at_case'], ctl['at_section'] + 1, 0)
        if frame is not None:
            g.Frame_counter = min(frame, ctl['frame_count']) 
            cap.set(cv2.CAP_PROP_POS_FRAMES, g.Frame_counter)
            ctl['at_section'] += 1
            print(f"フレーム={g.Frame_counter} at ({ctl['at_section']})")
            
            if ctl['at_section'] == 9: ctl['at_section'] =  11
            
        elif ctl['at_section'] < 19: ctl['at_section'] += 1
        else: ctl['at_section'] = 1
                    
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
        mylog.log(INFO, f"!!Attention({ctl['attention']}):Section({g.Section_no:2d}), g.Frame_counter={g.Frame_counter}")
        print(f"アテンション({ctl['attention']}):Section({g.Section_no:2d}), g.Frame_counter={g.Frame_counter}")

    elif key == ord('I'):
        tbl = CompleteAction_param
        print(f">Please input frame-name.!: [/:cancle]")
        ans = input(f"{tbl['frame']} -> :")
        if len(ans) > 0:
            if ans == '/':
                return True
            elif ans not in InitAction_param_nms:
                print(f"Error: Invalid frame name. Please input one of {InitAction_param_nms}")
                return True
            else: tbl['frame'] = ans
        print(f">Please input step.!: [/:cancle]")
        ans = input(f"{tbl['step']} -> :")
        if len(ans) > 0:
            if ans == '/':
                return True
            elif ans.isnumeric() == False:
                print(f"Error: Invalid step. Please input a numeric value.")
                return True
            else: tbl['step'] = int(ans)
        # 動作完了パラメータをテーブルに登録
        Db.insert_act_param(tbl)
        print(f"パラメータ:{tbl['frame']} step={tbl['step']},act={tbl['act']} テーブル登録完了")
        # 動作開始パラメータをテーブルに登録
        StartAction_param['frame'] = CompleteAction_param['frame']
        StartAction_param['step'] = CompleteAction_param['step']
        tbl = StartAction_param
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
        row = g.Section_no        
        tbl = CompleteAction_param if not g.Completed else StartAction_param  
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
        
    elif key == ord('z'):
        rectAreas:Rect = []
        while( True ): 
            rectAreas = clip_process( annotated_frame ) # ズーム領域を指定する
            if rectAreas is  None: break                # 'q'押下で中断
            elif len(rectAreas) > 0:                    # 'c'押下でズーム処理継続
                # ズーム領域座標の取得
                ctl['zoom_rect'] = rectAreas.pop(0)  # 最初の矩形をズーム領域として設定
                print(f"ズーム領域を設定しました: {ctl['zoom_rect'].width_height()}")
                break        
        
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
            
        # ズーム領域をリセット
        ctl['zoom_rect'] = None           
        # フレームスキップ数をデフォルトにリセット
        ctl['skipf_frames'] = 1
        ctl['skipb_frames'] = 2              

        # グリッド表示をデフォルトにリセット
        ctl['grid_shape'] = (6, 6)              
        ctl['grid_shift'] = (0, 0)
        # フレーム間インターバルをデフォルトにリセット
        ctl['iwait'] = ctl['iwait_init']
        # 評価スコアの表示をオフにする
        Eval.score_on = False 
        Eval.deduct_msgs.clear() 
        #
        ctl['at_section'] = 1
        #print(f"{ctl}")
        
    elif key == ord('?'):
        print(f"{ctl}")
    #
    return True
    
#
# Main process to play video with form-analize by YOLOv8
#
def main(): 
    global Section_color, Alart_message
    global Tracking_only, Tracking_enabled, Update_tracking, Update_enabled, Eval_enabled, Eval_sframes
    global Window_size, Sample_frames, Sample_lag, V8_model, Debug_opt, Level
    global StartAction_param, CompleteAction_param
    global Rect_area
    global InputPdf
    global Fps

    #
    # start of main
    #
    cam_id = None                                   # デフォルトのカメラID
    raw_video = False                               # 生画像を表示するオプション
    clip_video = False                              # 生画像をクリップしてファイルを作成
    rotate_video = False                            # 動画を90度回転して表示するオプション
    manual_plot = False                             # 手動でプロット、姿勢解析するオプション
    nn_gru = False                                  # GRUによる姿勢解析オプション
    multi_frames = False                 #          # 2動画ファイルを重ねて再生するオプション
    multi_fstart = [0, 0]                           # 2動画ファイルを重ねて再生する開始フレーム
    mosaic = False                                  # モザイク処理を行うオプション
    guidance = True                                 # '-g'キー操作ガイダンス表示
    idir = PICT_PATH                                # 初期ディレクトリを指定
    idir = idir if idir[-1] == '/' else idir + '/'
    ALL_TYPES = "*.*"                               # 動画ファイル名[*.mp4;*.avi;*.mov;*.mkv"]
    timestamp = datetime.now().strftime('%Y%m%d')
    filetypes = f"WIN_{timestamp}_*.mp4"            #'*WIN_YYYYmmdd_10_46_55_Pro.mp4'  # 動画ファイル名
    file_name = [None, None]  
    #
    case_name = None                                # ケース名（デフォルト：動画ファイル名）
    case_img_path = []                              # ケース内設定の動画ファイルのパス
    case_name_l = []                                # ケース名リスト
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
        'skipf_frames': 1,                          # 早送りフレーム数
        'skipb_frames': 2,                          # 巻き戻しフレーム数
        'videoWrite': False,                        # 動画ファイルへの書き込みフラグ
        'repeat': False,                            # 繰り返し再生フラグ
        'frame_count': 0,                           # 総フレーム数
        'start_frame': 0,                           # 繰り返し再生開始フレーム
        'stop_frame': 0,                            # 繰り返し再生終了フレーム
        'grid': False,                              # グリッド表示有無
        'grid_shape': (6, 6),                       # グリッド分割数(行,列)
        'grid_shift': (0, 0),                       # グリッド表示シフト量(行,列)
        'zoom_rect': None,                          # ズーム領域
        'at_case': None,                            # '-o'指定のケース名
        'at_section':0,                             # '-at'指定のセクション番号
        'fps_ratio':1.0                             # '-w'指定の出力ファイルFPS算出係数
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
    if '-c' in args and len(ids) > 0:
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
        if '-rotate' in opts: 
            rotate_video = True # 動画を90度回転して表示するオプション   
    
    eval_model_pth = None      # 評価モデル(EvalNN)ファイルのパス   
    if '-eval' in opts:
        Eval_enabled = True
        # 評価モデル(EvalNN)ファイルの指定をチェックする
        opt_vals, _ = get_opt_values(args, '-eval')
        if len(opt_vals) > 0: 
            eval_model_pth = opt_vals[0]
            if os.path.isfile(eval_model_pth) is False:
                print(f"[yoloApp]error:model-file({eval_model_pth}) not found.")
                return

    if '-clip' in opts:
        clip_video = True
        raw_video = True        # 生画像を表示するオプション
        if '-rotate' in opts: 
            rotate_video = True # 動画を90度回転して表示するオプション   

    if '-o' in opts:
        # 動画ファイルの選択をケース名で指定する
        cases, _ = get_opt_values(args, '-o', type='c', sep=',')
        if len(cases) > 0:
            for case in cases:
                fps,_ = Db.get_fps(case)   
                if fps is None:
                    print(f"> '{case}' not found in frame_info table.")
                    return
                path = get_case_img_path(Db, idir, case)
                if path is None:
                    print(f">  image file({path}) for '{case}' not found.")
                    return
                case_name_l.append(case)
                case_img_path.append(path)
        else:
            print("(-o)ケース名の指定がありません")
            return
    if '-multi' in opts:
        # 再生開始のフレーム番号を指定する
        multi_frames = True     # 複数画像を再生するオプション
        raw_video = True        # 生画像を再生するオプション
        fstart, idx = get_opt_values(args, '-multi', 'n', sep=',')
        if len(fstart) > 0:
            # フレーム番号指定
            for i, val in enumerate(fstart):
                if i < 2:       # 最大２ファイルまで
                    multi_fstart[i] = val
        elif len(case_name_l) == 2:
            # <section>.<step>指定
            at_l = []
            fstart = args[idx].split(',')
            for val_s in fstart:
                at = val_s.strip().split('.')
                if at[0].isnumeric() and at[1].isnumeric(): 
                    at_l.append(at)
            # 指定数のチェック
            s = len(at_l)
            if s == 1: at_l.append(at_l[0])     # 第１指定のみの時、第２にコピー
            elif s == 0:
                print(f"[main]:無効なフレーム番号が指定されました.")
                return                
            # 指定ケース毎に該当フレーム番号を取得する
            for i, case in enumerate(case_name_l):
                frame_no = -1
                ret = Db.get_frame_no_at(case, int(at_l[i][0]), int(at_l[i][1]))
                frame_no = -1 if ret is None else ret
                if frame_no == -1: 
                    print(f"[main]:該当するフレームが見つかりません.:"\
                            f"case={case},section={int(at_l[i][0])}, step={int(at_l[i][1])}")
                    break
                multi_fstart[i] = frame_no
            if frame_no == -1:
                print(f"[main]:無効なフレーム番号が指定されました.")
                return                
        else:
            print(f"[main]:無効なフレーム番号が指定されました.")
            return
        print(f"[main]:開始フレーム={multi_fstart}")
       
    if not raw_video and ('-m' in opts):            # 手動（OpenCV）で解析データをプロット、姿勢解析するオプション
        manual_plot = True

    # キーポイントの描画形式番号を指定する
    draw_kpt_no = 3
    if '-kpt' in opts:
        opt_vals, _ = get_opt_values(args, '-kpt', 'n')
        if len(opt_vals) > 0: draw_kpt_no = opt_vals[0]
    
    # GRUモデルパラメータ
    model_pth = None
    input_key = Input_key
    face_embed = False
    input_dim = Num_input
    output_dim = Num_classes
    seq_frames = Num_frames
    _, _, _, _, section_dim, completed_dim = Hyper_parameters
        
    if not raw_video and ('-gru' in opts):          # GRUで姿勢解析するオプション
        nn_gru = True
        opt_vals, _ = get_opt_values(args, '-gru')
        if len(opt_vals) > 0: model_pth = opt_vals[0]
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
                input_dim = int(params[0])
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
                if input_key <= 60 or input_key >= 99:
                    print("入力データキーは60～99範囲で指定してください")
                    return
        face_embed = True if 'face' in get_feature_colnames(Features_lists[input_key]) else False
        print(f"[main]:Input_feature_key = {input_key}, face_embed={face_embed}")
        
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
        Tracking_only = True                            # トラッキングのみを行うオプション
        Eval_enabled = True                             # 評価用のデータ作成をセット
        # トラッキングデータリストのインスタンス作成
        if not nn_gru: 
            InputPdf = FeaturePdf(input_key, seq_frames)
        i = args.index('-t')
    if not raw_video and ( '-u' in opts) :
        manual_plot = True
        Update_tracking = True  # トラッキングを更新するオプション
        i = args.index('-u')
    if Tracking_only or Update_tracking:
        if i + 1 < len(args) and (not args[i + 1].startswith('-')):
            case_name = args[i + 1]  # ケース名を取得
            if len(case_name) == 0:
                print("(-t)ケース名の指定がありません")
                return
            Db.case_name = case_name   
            fps, _ = Db.get_fps()
            if Update_tracking and fps is None:
                print(f"> '{case_name}' not found in frame_info table.")
                return
        else:
            print("(-t)ケース名の指定がありません")
            return
    #
    # トラッキングデータのケース名を設定
    if Tracking_only: 
        fps, x = Db.get_fps()
        if fps is not None:
            print(f"> '{case_name}' already registered. Are you sure?[y/n].")
            ans = input('>>')
            if ans == 'y': delete_frame_info(Db, case_name)                
            else: Tracking_only = False
    #
    # YOLOv8モデルファイル指定（デフォルトは'V8s'）
    for V8 in V8_models_l:
        if f'-{V8}' in opts:
            V8_model = V8.lower()  # YOLOv8モデルを使用

    # 動作解析パラメータのフレーム名を設定（デフォルト値から変更することがあるため、ここで設定）
    param_nm = f"{Sample_frames}.{Sample_lag}-{V8_model[-1:]}"
    # サンプリングフレーム数を取得
    opt_val  = [opt for opt in opts if opt.startswith('-f')]
    if len(opt_val) > 0:
        if len(opt_val[0]) > 2 :
            vals = opt_val[0][2:].split('.')
            if vals[0].isnumeric(): 
                Sample_frames = int(vals[0])
            if len(vals) > 1 and vals[1].isnumeric(): 
                Sample_lag = int(vals[1])

    # 段レベル(step)を取得
    step_no = 1
    opt_val  = [opt for opt in opts if opt.startswith('-s')]
    if len(opt_val) > 0:
        if len(opt_val[0]) > 2 and opt_val[0][2:].isnumeric():
            step_no = int(opt_val[0][2:])
            if nn_gru:
                g.Hybrid_model = True
    Level = step_no
    #
    if '-I' in opts:            # 動作開始解析パラメータの初期登録
        param_nms = []
        opt_vals, _ = get_opt_values(args, '-I')
        if len(opt_vals) > 0:
            if opt_vals[0] in InitAction_param_nms:
                param_nms.append( opt_vals[0] )     # パラメータテーブルframe名を取得
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
        files = 2 if multi_frames  else 1
        for i in range( files ):
            if len(case_img_path) > 0:
                file_name[i] = case_img_path[i]
            else:
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

    out_frame_width, out_frame_height = frame_width, frame_height
    # フレームレートを取得
    Fps = cap[0].get(cv2.CAP_PROP_FPS)       
    #
    if Tracking_only:
        # トラッキングデータ、姿勢解析データの出力先CSVファイルを開く
        Db.open_csv()
        Eval.open_csv(case_name, step_no, Db.csvpath1)
        # トラッキングデータの情報テーブルに登録 
        img_file = os.path.basename(file_name[0])        # 'memo'に初期設定する画像ファイル名を取得
        memo = f"{img_file}: {param_nm}:s{step_no})"
        Db.insert_frame_info( [file_name[0], Fps, frame_height, frame_width, Db.csvpath1, memo] )     
    #---------------------------------------------------------------------  
    # クリッピング領域指定
    #---------------------------------------------------------------------  
    rectAreas:Rect = []
    if clip_video:
        while( True ): 
            # クリッピング領域を指定する
            rectAreas = clip_process( frame, rotate_video ) 
            if rectAreas is  None: return           # 'q'押下で終了
            elif len(rectAreas) > 0:                # 'c'押下で処理継続
                # クリッピング領域座標の取得
                rect = rectAreas.pop(0)
                out_frame_width, out_frame_height = rect.width_height()
                frame_x = rect.x[0]
                frame_y = rect.y[0]
                break
    #---------------------------------------------------------------------  
    # 重ね動画の先頭フレームを読み込み、開始フレームを設定
    #---------------------------------------------------------------------  
    if multi_frames:
        if cap[1].isOpened():
            # 先頭フレームを読み込み
            ret, frame1 = cap[1].read()
            if not ret:
                print("動画ファイルの読み込みに失敗しました")
                cap[1].release()
                return
            # 先頭フレームを指定フレームに設定する
            for i in range(2):
                max_frame = int(cap[i].get(cv2.CAP_PROP_FRAME_COUNT))
                cur_frame = int(cap[i].get(cv2.CAP_PROP_POS_FRAMES))
                if multi_fstart[i] > max_frame:
                    print(f"[main]:開始フレームが動画の総フレーム数を超えています: {multi_fstart[i]} > {max_frame}")
                    cap[i].release()
                    return
                if cur_frame < multi_fstart[i]:
                    cap[i].set(cv2.CAP_PROP_POS_FRAMES, multi_fstart[i])
                    print(f"[main]:動画{i+1}の開始フレーム：{multi_fstart[i]}")
                #
        else:
            print("動画ファイルが見つかりません")
            cap[1].release()
            return
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

        print(f"[main]:出力ファイル：{out_file}")
        #print(f"os.sep: {os.sep}")
        if not clip_video:
            # '-w'指定時のみ、出力FPS値の検査
            opt_vals, _ = get_opt_values(args, '-w', 'n', sep='.')  # '-w'オプションの値を取得
            if len(opt_vals) > 1:
                keyCtl['fps_ratio'] = float(f"{opt_vals[0]}.{opt_vals[1]}")
                print(f"[main]:出力ファイル：FPS=Fps*{keyCtl['fps_ratio']:.3f}")
    #
    if not raw_video:
        #------------------------------------------------------------------------
        # YOLO-poseモデルのインスタンス生成
        #------------------------------------------------------------------------
        mylog.log(INFO,f"YOLO{V8_model} Pose Detectionを開始します")
        print(f"YOLO{V8_model} Pose Detectionを開始します")
        print(f"YOLOv8 ログレベル={mylog_level}")
        print(f"解析パラメータ={param_nm}, レベル={step_no}, モデル={V8_model}, 出力クラス区分数: {output_dim}")        
                
        # YOLOv8-poseモデルの読み込み（事前学習済みモデル）
        if V8_model[1] != '8':
            V8_model = V8_model[1:]
        print(f"学習済モデルファイル：yolo{V8_model}-pose.pt")
        model = YOLO(f"yolo{V8_model}-pose.pt")  # 軽量モデル。他にも'yolov8s-pose.pt'などあり
        model.info()  # モデル情報を表示
        #------------------------------------------------------------------------
        # GRUモデルのインスタンス生成
        #------------------------------------------------------------------------        
        if nn_gru:
            print("GRUによる姿勢解析を有効化します")
            mylog.log(INFO, "GRUによる姿勢解析を有効化します")
            print(f"input_dim={input_dim}")            
            # KyudoGRUモデルの読み込み（事前学習済みモデル）
            parts = model_pth.split('_') 
            if 'modelse' in parts:
                gruModel = KyudoGRUs( input_size = input_dim, output_size = output_dim,
                                face_embed_dim = Face_dim if face_embed else None,
                                section_embed_dim = section_dim,
                                completed_embed_dim = completed_dim )
            elif 'modelme' in parts:
                gruModel = KyudoGRUm( input_size = input_dim, output_size = output_dim,
                                hidden_size=32,
                                face_embed_dim = Face_dim if face_embed else None,
                                section_embed_dim = section_dim,
                                completed_embed_dim = completed_dim )
            else:
                print(f"非対応のモデルです。")
                return   
            gruModel.to( get_device() )
            gruModel.load_state_dict( torch.load(model_pth, map_location = get_device()) )

            print(f"gruModel={gruModel}")
            mylog.log(INFO,f"gruModel={gruModel}")            
            print(f"[main]:model loaded from {model_pth}")
            mylog.log(INFO,f"model loaded from {model_pth}")
            
        #------------------------------------------------------------------------
        # EvalNNモデルのインスタンス生成
        #------------------------------------------------------------------------
        evalModel = None
        eval_input_dim = None
        if eval_model_pth is not None:
            # 学習済みモデルファイル名からパラメータを取得（eval_model_pthの例：eval_modeln_9-48-6.pth）
            parts = eval_model_pth.split('_') 
            params = parts[-1].split('-')
            eval_input_dim = int(params[0]) if len(params) > 0 and params[0].isnumeric() else len(Eval_Features_lists[Eval_feature_key])
            eval_output_dim = int(params[2]) if len(params) > 2 and params[2].isnumeric() else Eval_output_dim
            Eval_sframes = int(params[1]) if len(params) > 1 and params[1].isnumeric() else Eval_sframes
            print(f"[main]:input_dim={eval_input_dim}, s_frames={Eval_sframes}, output_dim={eval_output_dim}")
            completed_dim = 0 
            if 'modeln' in parts:
                
                evalModel = EvalNN( input_dim = eval_input_dim, 
                                s_frames = Eval_sframes,
                                output_size = eval_output_dim,
                                section_embed_dim = section_dim)
                #evalModel.to( get_device() )
                #evalModel.load_state_dict( torch.load(eval_model_pth, map_location = get_device()) )
            elif 'modelc' in parts:
                evalModel = EvalCN( input_dim = eval_input_dim, 
                                s_frames = Eval_sframes,
                                output_size = eval_output_dim)
                #evalModel.to( get_device() )
                #evalModel.load_state_dict( torch.load(eval_model_pth, map_location = get_device()) )
            else :
                print(f"非対応のモデルです。")
                return           
            #
            evalModel.to( get_device() )
            print(f"evalModel={evalModel}")
            mylog.log(INFO,f"evalModel={evalModel}")            

            evalModel.load_state_dict( torch.load(eval_model_pth, map_location = get_device()) )
            print(f"[main]:model loaded from {eval_model_pth}")
            mylog.log(INFO,f"model loaded from {eval_model_pth}") 
    #    
    sample_seconds = 1.0 / Fps * Sample_frames  # サンプリング秒数
    
    if len(case_name_l) > 0:
        mylog.log(INFO, f"[main]:起動パラメータ情報:WindowSize={Window_size}:case_name={case_name_l}")
        print(f"[main]:起動パラメータ情報:WindowSize={Window_size}:case_name={case_name_l}")
    else:
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
    # フレームカウンターの初期化
    g.Frame_counter = 1 if not multi_frames else multi_fstart[0]
    #
    # コマンドライン引数でフレームカウンターを指定するオプションの処理
    if '-at' in opts:
        frame_no = -1
        opt_vals, _ = get_opt_values(args, '-at', 'n', sep='.')  # '-at'オプションの値を取得
        count = len(opt_vals)
        if count == 1:                              # フレーム番号指定
            frame_no = opt_vals[0]
        elif count == 2 and len(case_name_l) > 0:   # <section>.<step>指定
            no = Db.get_frame_no_at(case_name_l[0], opt_vals[0], opt_vals[1]) 
            frame_no = -1 if no is None else no
            if frame_no != -1:
                # キー操作（tab)の情報
                keyCtl['at_case'] = case_name_l[0]
                keyCtl['at_section'] = opt_vals[0]
        else: pass
        if frame_no == -1:    
            print(f"[main]:無効なフレーム番号が指定されました.")
            return
        max_frame = int(cap[0].get(cv2.CAP_PROP_FRAME_COUNT))
        g.Frame_counter = max(1, min(frame_no, max_frame))  # フレームカウンターを1以上、最大フレーム数以下に制限
        print(f"[main]:開始フレームを{g.Frame_counter}に設定しました")
        g.Frame_counter -= 1  
        # フレームカウンターを指定されたフレームに設定 
        cap[0].set(cv2.CAP_PROP_POS_FRAMES, g.Frame_counter)
    #
    # ウィンドウの更新間隔とキー入力待ち時間の初期値を設定
    if raw_video is True:
        keyCtl['iwait_init'] = int(1/Fps * 1000) + 1  # 生画像を表示する場合、FPS値からキー入力待ち時間を設定
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
    buffer_size = max( (Window_size, (Sample_lag+1)) )  # リングバッファサイズ
    prePointsBuffer = RingBuffer(buffer_size)           # 検出結果を保存するリングバッファ                           
    preResult = RingBuffer(2)                           # 前回の検出結果（補整済）を保存するリングバッファ                           
    preFrame = None                                     # 前回のフレームを保存する変数
    actStr = 'action :'
    ratio = frame_height/frame_width if frame_height < frame_width else frame_width/frame_height
    # メインループ
    while True:
        # 次のフレームの読み込み
        ret, frame = cap[0].read()
        if not ret:
            if keyCtl['repeat']:
                cap[0].release()
                cap[0] = cv2.VideoCapture(file_name[0])  # 動画ファイルのパスを指定
                g.Frame_counter = 0
                continue
            print(f"[main]: #end of video data. frame={g.Frame_counter}")
            break
        #
        g.Frame_counter += 1  # フレームカウンターをインクリメント
        if raw_video is True:
            if rotate_video:
                frame = cv2.resize(frame, dsize=None, fx=ratio, fy=ratio, interpolation=cv2.INTER_NEAREST)
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            if clip_video:
                # クリッピング処理
                annotated_frame = frame[ frame_y:frame_y + out_frame_height, frame_x:frame_x + out_frame_width ]
                #print(f"[main]:クリッピング処理: {frame.shape} -> {annotated_frame.shape}")
                for rect in rectAreas:
                    # モザイク処理
                    w, h = rect.width_height()
                    y1 = rect.y[0]
                    x1 = rect.x[0]
                    annotated_frame = mosaic_area( annotated_frame, y1 - frame_y, x1 - frame_x, h, w )
            elif keyCtl['zoom_rect'] is not None:
                # ズーム処理
                w, h = keyCtl['zoom_rect'].width_height()
                y1 = keyCtl['zoom_rect'].y[0]
                x1 = keyCtl['zoom_rect'].x[0]
                annotated_frame = zoom_area( frame, y1, x1, h, w, frame_width, frame_height )
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
                myResult = MyResult(result, g.Frame_counter, manual_plot)
            except BoundaryBoxError as e:
                print(f"フレーム({g.Frame_counter}):{e}")
                mylog.log(INFO, f"[main]:フレーム({g.Frame_counter}):検出結果の描画をスキップ")
                preResult.clear()
                annotated_frame = frame
            else:
                myResult.draw_line = draw_kpt_no
                # 検出結果をフレームに描画
                if manual_plot:
                    # 補正用の直近リングバッファに保存
                    preResult.append( myResult )
                    
                    # キーポイントの過去サンプリング位置からの変位ベクトルの長さ、角度を計算する    
                    myResult.calc_arrow_length_angles(prePointsBuffer)

                    # {Sample_frames}フレーム毎に検出結果を保存
                    if (g.Frame_counter%Sample_frames) == 0 or g.Frame_counter < Sample_frames:
                        # 検出結果（補正済）を保存 
                        prePointsBuffer.append( myResult )                        
                        mylog.log(DEBUG, f"[main]: {datetime.now().strftime('%H-%M-%S')}:検出結果保存: {type(results)}, {len(results)}個の結果,"\
                                    + f"フレーム={g.Frame_counter}, buffer_length={prePointsBuffer.length}")

                    # 生画像に手動（OpenCV）で描画
                    # 射法八節の姿勢解析を実行
                    if Tracking_only or Update_tracking: 
                        Db.frame_no = g.Frame_counter     # トラッキングデータのフレーム番号を設定  
                    
                    annotated_frame = frame
                    if prePointsBuffer.len() > 1:
                        annotated_frame = plot( myResult, frame, output_dim, \
                                                nn_gru, gruModel if nn_gru else None,\
                                                evalModel, eval_input_dim)
                        if annotated_frame is None and preFrame is not None:  # 前回のフレームを描画
                            annotated_frame = preFrame
                            mylog.log(INFO, "[main]: 前回フレームを描画")
                        elif mosaic:
                            # モザイク処理
                            areas = get_mosaic_areas(myResult)
                            for rect in areas:
                                annotated_frame = mosaic_area( annotated_frame, rect[0], rect[1], rect[2], rect[3] )
                else:
                    if draw_kpt_no != 0:
                        annotated_frame = myResult.plot(frame)
                    else:
                        # YOLOv8のplot関数を使用してフレームに描画  
                        # 　kpt_line=False： キーポイントのマークのみを描画）
                        annotated_frame = myResult.result.plot(boxes=True, labels=False, kpt_line=True, kpt_radius=3)                        
                '''                
                if multi_frames and cap[1] is not None:
                    # 画面を重ねて表示
                    ret, frame1 = cap[1].read()
                    if ret is True: 
                        annotated_frame = multi_frame_display(annotated_frame, frame1)
                '''
                
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
                str = f"frame :{g.Frame_counter:4d}   interval : {keyCtl['iwait']}ms."
                cv2.putText(annotated_frame, str, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 1)            
            
            # パラメータ情報       
            if manual_plot and guid_option > 2:
                pos = (x, y - 45)
                comp = 1 if g.Completed else 0
                str = f"param({g.Section_no}-{comp}-{g.Step_counter:2d}) : "
                for i in  range( Stkp.len() ):
                    no, val = Stkp.get(i)
                    if i > 0: str += ", "
                    str += f"{no}={val}"
                cv2.putText(annotated_frame, str, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)
            
            # GRU動作解析情報            
            if nn_gru:
                pos = (x, y - 70)
                if Action != 0: 
                    actStr = f"action :{g.Section_no}"
                    actStr +=  "c" if Action == 1 else "s"
                cv2.putText(annotated_frame, actStr, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 1)            
        #    
        # ウィンドウに表示する   
        cv2.imshow('YOLO Pose Detection', annotated_frame)
        #print(f"({g.Frame_counter})")
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
        if key == ord('a'):
            # 'a'キーが押された場合の処理
            val = myResult.get_normalized_value('right_shoulder', 'left_shoulder')
            print(f"Normalized value: {val:.4f}")
        #
        # 繰り返し再生の処理
        if keyCtl['repeat'] and keyCtl['stop_frame'] != 0 and g.Frame_counter >= keyCtl['stop_frame']:
            # 繰り返し再生の開始フレームに戻す
            g.Frame_counter = keyCtl['start_frame'] - 1           
            cap[0].set(cv2.CAP_PROP_POS_FRAMES, g.Frame_counter)
    #
    if Tracking_enabled:
        Db.update_frame_info('stop_frame', g.Frame_counter)   # 停止フレーム番号
    # リソースの解放
    if Tracking_only: 
        Db.csvfile1.close()
        Db.csvfile2.close()
        Eval.csvfd.close()
    if Cv2Video is not None:
        Cv2Video.release()
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
    '''
    if not os.path.exists(f'yolo{V8_model}-pose.pt'):
        print(f"YOLOv8-poseモデル(yolo{V8_model}-pose.pt)が見つかりません。ダウンロードしてください。")
        #exit(1)
    '''
    main()
# eof