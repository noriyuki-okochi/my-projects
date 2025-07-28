import os
import numpy as np

##############################
# 共通定数
##############################
DB_PATH = './yolo-tracking.db'
PICT_PATH = 'C:/Users/USER/Pictures/Camera Roll/' 
#   PICT_PATH = 'C:/Users/staff/OneDrive/画像/カメラロール/'    # 初期ディレクトリを指定

# セクション名の定義
Section_names = [' ', '1.Asi-bumi', '2.Dou-zukuri', '3.Yu-gamae', '4.Uti-okosshi', 
                     '5.Hiki-wake', '6.Kai', '7.Hanare', '8.Zan-shin', '']  # セクション名
# キーポイントのインデックスを定義
Kn2idx = {'nose':0, 'left_eye':1, 'right_eye':2, 'left_ear':3, 'right_ear':4, 
        'left_shoulder':5, 'right_shoulder':6, 'left_elbow':7, 'right_elbow':8, 
        'left_wrist':9, 'right_wrist':10, 'left_hip':11, 'right_hip':12,
        'left_knee':13, 'right_knee':14, 'left_ankle':15, 'right_ankle':16}  # キーポイント名

# 2軸に指定できる'tracking_dat'テーブルのカラム名
Col_names = ['box_w', 'box_h', 'box_conf', 'x', 'y', 'xy_conf', 'angle'] 

# 動作解析データのサンプリング間隔（フレーム数）
Sample_frames:int = 8

# 移動平均のウィンドウサイズと重みの設定
Window_size = 5   # ウィンドウサイズを設定
WMA_weights = np.arange(1, Window_size + 1)

# 動作開始解析パラメータ
StartAction_params = [
    {'flame': '18n',   #約1.0秒
     'param': [
        [0.150, 0.140, None, None, None, None, None, None],     # 0.
        [0.080, 2, None, None, None, None, None, None],         # 1.足踏み
        [0.030, 0.035, 4, None, None, None, None, None],        # 2.胴作り
        [0.034, 0.034, 6, None, None, None, None, None],        # 3.弓構え
        [0.035, 0.035, 0.90, 1, None, None, None, None],         # 4.打起こし
        [0.025, 1.000, 0.025, 1.000, 5, None, None, None],      # 5.引分け
        [0.085, 0.085, None, None, None, None, None, None],     # 6.会
        [0.085, None, None, None, None, None, None, None],      # 7.離れ
        [0.085, 0.085, None, None, None, None, None, None],     # 8.残心
        [0.085, 2, 0.085, 2, None, None, None, None],           # 9.弓倒し
        [0.900, 0.100, None, None, None, None, None, None]      #10.共通
     ]
    },          
    {'flame': '8n',    # 約0.5秒
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],     # 0.
        [0.080, 2, None, None, None, None, None, None],         # 1.足踏み
        [0.030, 0.035, 3, None, None, None, None, None],        # 2.胴作り
        [0.050, 0.050, 3, None, None, None, None, None],        # 3.弓構え
        [0.050, 0.05, 0.90, 1, None, None, None, None],         # 4.打起こし
        [0.025, 1.000, 0.025, 1.000, 5, None, None, None],      # 5.引分け
        [0.050, 0.085, None, None, None, None, None, None],     # 6.会
        [0.085, None, None, None, None, None, None, None],      # 7.離れ
        [0.1, 0.1, None, None, None, None, None, None],     # 8.残心
        [0.085, 2, 0.085, 2, None, None, None, None],           # 9.弓倒し
        [0.900, 0.100, None, None, None, None, None, None]      #10.共通
     ]
    },          
    {'flame': '8s',    # 約0.5秒
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],     # 0.
        [0.080, 2, None, None, None, None, None, None],         # 1.足踏み
        [0.030, 0.035, 3, None, None, None, None, None],        # 2.胴作り
        [0.040, 0.040, 3, None, None, None, None, None],        # 3.弓構え
        [0.030, 0.030, 0.90, 1, None, None, None, None],         # 4.打起こし
        [0.025, 1.000, 0.025, 1.000, 5, None, None, None],      # 5.引分け
        [0.050, 0.000, None, None, None, None, None, None],     # 6.会
        [0.085, None, None, None, None, None, None, None],      # 7.離れ
        [0.085, 0.085, None, None, None, None, None, None],     # 8.残心
        [0.085, 2, 0.085, 2, None, None, None, None],           # 9.弓倒し
        [0.900, 1.00, None, None, None, None, None, None]      #10.共通
     ]
    }          
]
# 動作完了解析パラメータ
CompleteAction_params = [
    {'flame': '18n',   #約1.0秒
     'param': [
        [None, None, None, None, None, None, None, None],       # 0.
        [0.028, 0.5, 0.035, 0.035, 0.035, 0.035, 0.035, 2],     # 1.足踏み
        [60.0, 95.0, 0.003, 2, 0.080, 5, None, None],           # 2.胴作り
        [0.025, 0.025, 0.025, 0.025, 3, 0.026, 2, 0.034],       # 3.弓構え
        [0.020, 0.020, 0.020, 0.020, 3, None, None, None],      # 4.打起こし
        [0.025, 1.000, 0.025, 1.000, 5, 0, 0.085, None],        # 5.引分け
        [0.017, 1.000, 0.017, 1.000, 5, None, None, None],      # 6.会
        [10, None, None, None, None, None, None, None],         # 7.離れ
        [0.10, 0.10, 3, None, None, None, None, None],          # 8.残心
        [25.0, 95.0, 0.030, 2, 0.085, None, None, None],        # 9.弓倒し
        [0.900, 0.100, None, None, None, None, None, None]      #10.共通
     ]
    },
    {'flame': '8n',  # 約0.5秒
     'param': [
        [None, None, None, None, None, None, None, None],       # 0.
        [0.028, 0.5, 0.015, 0.015, 0.015, 0.015, 0.015, 3],     # 1.足踏み
        [60.0, 95.0, 0.025, 2, 0.080, 5, None, None],           # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 3, 0.027, 2, 0.05 ],       # 3.弓構え
        [0.020, 0.020, 0.020, 0.020, 8, None, None, None],      # 4.打起こし
        [0.015, 1.000, 0.015, 1.000, 5, 0, 0.085, None],        # 5.引分け
        [0.015, 1.000, 0.015, 1.000, 5, None, None, None],      # 6.会
        [5, None, None, None, None, None, None, None],          # 7.離れ
        [0.085, 0.085, 3, None, None, None, None, None],        # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],        # 9.弓倒し
        [0.900, 0.100, None, None, None, None, None, None]      #10.共通
     ]
    },
   {'flame': '8s',  # 約0.5秒
     'param': [
        [None, None, None, None, None, None, None, None],       # 0.
        [0.028, 0.5, 0.015, 0.015, 0.015, 0.015, 0.015, 3],     # 1.足踏み
        [60.0, 95.0, 0.025, 2, 0.080, 5, None, None],           # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.027, 2, 0.04 ],       # 3.弓構え
        [0.015, 0.015, 0.015, 0.015, 8, None, None, None],     # 4.打起こし
        [0.015, 1.000, 0.015, 1.000, 5, 0, 0.085, None],        # 5.引分け
        [0.015, 1.000, 0.015, 1.000, 5, None, None, None],      # 6.会
        [5, None, None, None, None, None, None, None],          # 7.離れ
        [0.080, 0.080, 3, None, None, None, None, None],        # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],        # 9.弓倒し
        [0.900, 1.00, None, None, None, None, None, None]      #10.共通
     ]
    }
]
#
# アラートID、メッセージの定義
#
Alart_Monomi = 3  # 「物見を定まらず」のアラートID
Alart_Kai = 5     # 「会なし離れ」のアラートID
#
Alart_msg = {
   0:'',
   3:'Warning:Detected illegal action in section-3.(MONOMI nasi)',
   30:'警告：物見なし打ちおこしを検知しました。',
   5:'Warning:Detected illegal action in section-5.(KAI nasi)',
   50:'警告：会なし離れを検知しました。'
}
# 
# テキスト属性
#
STYLE_NON = '0'
STYLE_BOLD = '1'
STYLE_LIGHT = '2'
STYLE_ITALIC = '3'
STYLE_UNDER = '4'
STYLE_BLINK = '5'
FG_BLACK = '30'
FG_RED = '31'
FG_GREEN = '32'
FG_YELLOW = '33'
FG_BLUE = '34'
FG_PURPLE = '35'
FG_CYAN = '36'
FG_WHITE = '3f'
BG_BLACK = '40'
BG_RED = '41'
BG_GREEN = '42'
BG_YELLOW = '43'
BG_BLUE = '44'
BG_PURPLE = '45'
BG_CYAN = '46'
BG_WHITE = '4f'
#
YELLOW = (0, 255, 255)  # 黄色
GREEN = (0, 255, 0)    # 緑色
RED = (0, 0, 255)      # 赤色
BLUE = (255, 0, 0)     # 青色  
WHITE = (255, 255, 255)  # 白色
BLACK = (0, 0, 0)      # 黒色
CYAN = (255, 255, 0)   # シアン
PURPLE= (255, 0, 255)  # 紫色
GRAY = (128, 128, 128)  # グレー
# eof
