import os
import numpy as np

##############################
# 共通定数
##############################
DB_PATH = './yolo-tracking.db'
PICT_PATH = 'C:/Users/USER/Pictures/Camera Roll/' 
#   PICT_PATH = 'C:/Users/staff/OneDrive/画像/カメラロール/'    # 初期ディレクトリを指定

# セクション名の定義
Section_names = [' ', '1.足踏み', '2.胴造り', '3.弓構え', '4.打起し', 
                  '5.引分け', '6.会', '7.離れ', '8.残身', '']  # セクション名
Step_names = { 201: '矢番え', 221: '取矢', 231: '矢番え', 240: '弦調べ・箆調べ',\
               310: '取掛け・手の内', 311: '物見',\
               510: '大三', 511: '押し', 512: '引き', 601: '口割',\
               901: '弓倒し', 922: '退場'}          # ステップ名
  
# キーポイントのインデックスを定義
Kn2idx = {'nose':0, 'left_eye':1, 'right_eye':2, 'left_ear':3, 'right_ear':4, 
        'left_shoulder':5, 'right_shoulder':6, 'left_elbow':7, 'right_elbow':8, 
        'left_wrist':9, 'right_wrist':10, 'left_hip':11, 'right_hip':12,
        'left_knee':13, 'right_knee':14, 'left_ankle':15, 'right_ankle':16}  # キーポイント名

# Kyudo_dataテーブルの項目名
Kyudo_data_names = ['box_id', 'box_conf',\
                'box_w', 'box_h',\
                'rw_norm', 'rw_angle',\
                'lw_norm', 'lw_angle',\
                'rl_norm', 'rl_angle',\
                'hr_norm', 'hr_angle',\
                'er_angle', 'sl_angle',\
                'eyes_norm', 'hips_norm']

# 学習用データの読み込みリスト
Features_list_8 = ['rw_norm/box_h as rw_ratio',\
                'rw_angle/180.0 as rw_deg',\
                'lw_norm/box_h as lw_ratio',\
                'eyes_norm/box_w as eyes_ratio',\
                'hr_norm/box_h as hr_ratio',\
                'hr_angle/180.0 as hr_deg',\
                'section','completed']

Features_list_7 = ['rw_norm/box_h as rw_ratio',\
                'lw_norm/box_h as lw_ratio',\
                'eyes_norm/box_w as eyes_ratio',\
                'hr_norm/box_h as hr_ratio',\
                'hr_angle/180.0 as hr_deg',\
                'section','completed']
# 入力データの次元数
Input_dim = len(Features_list_7)
# 出力クラス数（ラベル[0=移行,1=完了,2=開始]の区分数）
Output_dim = 3 
# 2軸に指定できる'tracking_dat'テーブルのカラム名
Second_names = ['box_w', 'box_h', 'x', 'y', 'xy_conf', 'angle'] 

# 動作解析起点データのサンプリング間隔（フレーム数）
Sample_frames:int = 1
Sample_lag:int = 7
# ハイパーパラメータのデフォルト値設定
Sequence_frames:int = 128       # 入力シーケンスのフレーム数
Batch_size:int = 256
N_epoch:int = 501
Section_dim:int = 8
Completed_dim:int = 4
Hyper_parameters = (Sequence_frames, \
                    Batch_size, N_epoch,\
                    Section_dim, Completed_dim)    
# 移動平均のウィンドウサイズと重みの設定
Window_size = 8   # ウィンドウサイズを設定
WMA_weights = np.arange(1, Window_size + 1)
Param_max = 10    # パラメータの最大個数
#
# アラートID、メッセージの定義
#
Alart_Asibumi= 1     # 「正対不完全」のアラートID
Alart_Monomi = 3     # 「物見を定まらず」のアラートID
Alart_KaiNasi = 5    # 「会なし離れ」のアラートID
Alart_KaiFusoku = 6  # 「会不十分な離れ」のアラートID
Alart_Hanare = 7     # 「離れタイミングずれ」のアラートID
#
Alart_msg = {
   0:'',
   1:'Warning:Detected illegal action in section-1.(SEITAI fukanzen)',
   10:'<警告>：「正対不完全」を検知しました。',
   3:'Warning:Detected illegal action in section-3.(MONOMI sadamarazu)',
   30:'<警告>：「物見定まらず」を検知しました。',
   5:'Warning:Detected illegal action in section-5.(KAI nasi)',
   50:'<警告>：「会なし離れ」を検知しました。',
   6:'Warning:Detected illegal action in section-6.(KAI fusoku)',
   60:'<警告>：「会不十分な離れ」を検知しました。',
   7:'Warning:Detected illegal action in section-7.(Timing un-match)',
   70:'<警告>：「弓手押しタイミングの遅れ」を検知しました。'
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
#　カラー(B,G,R)
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
