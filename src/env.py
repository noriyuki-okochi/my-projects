import os

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
# eof
