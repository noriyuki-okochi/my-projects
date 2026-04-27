import os
import numpy as np

##############################
# 共通定数
##############################
# データベースの初期ファイルパス名
DB_PATH = './yolo-kyudo.db'
path = os.getenv('DB_PATH')
if path != None:
    DB_PATH = path
    
# 画像-カメラロールの初期ディレクトリ
PICT_PATH = 'C:/Users/USER/Pictures/Camera Roll/' 
path = os.getenv('ROLL_PATH')
if path != None:
    PICT_PATH = path
    
# 画像重ねのアルファ値
ADD_WEIGHT = '0.7'
weight = os.getenv('ADD_WEIGHT')
if weight != None:
    Add_WEIGHT = weight

V8_models_l = ['V8n', 'V8s', 'V8m', 'V26s', 'V26m' ]  # YOLOv8,26モデルのリスト   
# セクション名の定義
Section_names = [' ', '1.足踏み', '2.胴造り', '3.弓構え', '4.打起し', 
                  '5.引分け', '6.会', '7.離れ', '8.残身', '']  # セクション名
Step_names = { 201: '矢番え', 221: '取矢', 222: '取矢', 230: '弦調べ', 240:'箆調べ',\
               310: '取掛け・手の内', 311: '物見',\
               510: '大三', 511: '押し', 512: '引き', 601: '口割',\
               901: '弓倒し', 922: '退場'}          # ステップ名
  
# キーポイントのインデックスを定義
Kn2idx = {'nose':0, 'left_eye':1, 'right_eye':2, 'left_ear':3, 'right_ear':4, 
        'left_shoulder':5, 'right_shoulder':6, 'left_elbow':7, 'right_elbow':8, 
        'left_wrist':9, 'right_wrist':10, 'left_hip':11, 'right_hip':12,
        'left_knee':13, 'right_knee':14, 'left_ankle':15, 'right_ankle':16}  # キーポイント名

# Kyudo_dataテーブルの登録データ項目名リスト
# ・tracking_result()関数でセットするデータ項目名リスト(data_listの順序)
Kyudo_data_names = ['box_id', 'box_conf','box_w', 'box_h',\
                'rw_norm', 'rw_angle',\
                'lw_norm', 'lw_angle',\
                'rl_norm', 'rl_angle',\
                'hr_norm', 'hr_angle',\
                'sr_norm', 'sr_angle',\
                'sl_norm', 'sl_angle',\
                'rew_angle', 'rse_angle',\
                'lew_angle', 'lse_angle',\
                'eyes_norm', 'hips_norm'\
                'tag1', 'tag2'
                ]

# 学習用データの読み込みリスト
# ・データベースから読み込むSQL文のデータ項目名と別名
Features_list_50 = ['rw_norm/box_h as rw_ratio',\
                'lw_norm/box_h as lw_ratio',\
                'hr_norm/box_h as hr_ratio',\
                'section','completed'
                ]
Features_list_60 = ['rw_norm/box_h as rw_ratio',\
                'rl_norm/box_h as rl_ratio',\
                'eyes_norm/box_w as eyes_ratio',\
                'hr_norm/box_h as hr_ratio',\
                'section','completed'
                ]
Features_list_61 = ['rw_norm/box_h as rw_ratio',\
                'rl_norm/box_h as rl_ratio',\
                'hr_norm/box_h as hr_ratio',\
                'tag1 as face',\
                'section','completed'
                ]

Features_list_70 = ['rw_norm/box_h as rw_ratio',\
                'lw_norm/box_h as lw_ratio',\
                'eyes_norm/box_w as eyes_ratio',\
                'hr_norm/box_h as hr_ratio',\
                'hr_angle/180.0 as hr_deg',\
                'section','completed'
                ]
Features_list_71 = ['rw_norm/box_h as rw_ratio',\
                'rl_norm/box_h as rl_ratio',\
                'hr_norm/box_h as hr_ratio',\
                'hr_angle/180.0 as hr_deg',\
                'tag1 as face',\
                'section','completed'
                ]
Features_list_72 = ['rw_norm/box_h as rw_ratio',\
                'rl_norm/box_h as rl_ratio',\
                'hr_norm/box_h as hr_ratio',\
                'tag2 as body',\
                'tag1 as face',\
                'section','completed'
                ]

Features_list_80 = ['rw_norm/box_h as rw_ratio',\
                'rl_norm/box_h as rl_ratio',\
                'hr_norm/box_h as hr_ratio',\
                'hr_angle/180.0 as hr_deg',\
                'tag2 as body',\
                'tag1 as face',\
                'section','completed'
                ]
Features_list_81 = ['rw_norm/box_h as rw_ratio',\
                'lw_norm/box_h as lw_ratio',\
                'eyes_norm/box_w as eyes_ratio',\
                'rl_norm/box_h as rl_ratio',\
                'hr_norm/box_h as hr_ratio',\
                'hr_angle/180.0 as hr_deg',\
                'section','completed'
                ]

Features_list_90 = ['rw_norm/box_h as rw_ratio',\
                'lw_norm/box_h as lw_ratio',\
                'eyes_norm/box_w as eyes_ratio',\
                'rl_norm/box_h as rl_ratio',\
                'hr_norm/box_h as hr_ratio',\
                'hr_angle/180.0 as hr_deg',\
                'tag1 as face',\
                'section','completed'
                ]
#
Features_lists = {
    50: Features_list_50,       # プロット専用特徴量リスト
    60: Features_list_60,
    61: Features_list_61,
    70: Features_list_70,
    71: Features_list_71,
    72: Features_list_72,
    80: Features_list_80,
    81: Features_list_81,
    90: Features_list_90
    }

# 学習済モデルファイルのデフォルト定義
Kyudo_model_pt = './kyudo80_modelse_8-96-3.pt'
# 環境変数 'MODEL_PT' が設定されていれば、それを使用する
model_pt = os.getenv('MODEL_PT')
if model_pt != None:
    Kyudo_model_pt = model_pt
    #print(f"Environment variable 'INPUT_KEY' found: Using Current_feature_key = {Current_feature_key}")

# 入力データの次元数
Current_feature_key = 80   # 使用する特徴量のキー番号
# 環境変数 'INPUT_KEY' が設定されていれば、それを使用する
input_key = os.getenv('INPUT_KEY')
if input_key != None:
    Current_feature_key = int(input_key)
    #print(f"Environment variable 'INPUT_KEY' found: Using Current_feature_key = {Current_feature_key}")
#
Input_dim = len(Features_lists[Current_feature_key])
# 出力クラス数（ラベル[0=移行,1=完了,2=開始]の区分数）
Output_dim = 3 
# 2軸に指定できる'tracking_dat'テーブルのカラム名
Second_names = ['box_w', 'box_h', 'x', 'y', 'xy_conf', 'angle'] 

# 動作解析起点データのサンプリング間隔（フレーム数）
Sample_frames:int = 1
Sample_lag:int = 7
Sample_lag_Max:int = 16
# ハイパーパラメータのデフォルト値設定
L2_lambda = 1e-5         # L2正則化の強度
l2_lambda = os.getenv('L2_LAMBDA')
if l2_lambda != None:
    L2_lambda = float(l2_lambda)
    
Sequence_frames:int = 96    # 入力シーケンスのフレーム数
Batch_size:int = 192
N_epoch:int = 301
R_factor:float = 1.0   # 学習率減衰の係数
Face_dim:int = 4       # 顔向き埋め込みベクトルの次元数
Section_dim:int = 8
Completed_dim:int = 4
Hyper_parameters = (Sequence_frames, \
                    Batch_size, N_epoch, R_factor, \
                    Section_dim, Completed_dim) 
Learning_rate:float = 0.001  # 学習率   
HiddenS_size:int = 64        # GRU（シングルヘッド）の隠れ層サイズ
HiddenM_size:int = 32        # GRU（マルチヘッド）の隠れ層サイズ
#
Body_front_threshold:float = 0.180  # 体の向きの閾値(tag2=1:正面,0:横)
#Face_front_threshold:float = 0.055  # 顔の向きの閾値(tag1=1:正面,2:横)
Face_front_threshold:float = 0.060  # 顔の向きの閾値(tag1=0:不定,1:正面,2:横)
Eyes_ratio_threshold:float = 0.0    # 目幅比率の閾値（補正しない場合は0.0に設定）
Eyes_ratio_max:float = 0.1          # 目幅比率の最大値
Eyes_ratio_min:float = 0.01         # 目幅比率の最小値
#
# 移動平均のウィンドウサイズと重みの設定
Window_size = 8   # ウィンドウサイズを設定
WMA_weights = np.arange(1, Window_size + 1)
Param_max = 10    # パラメータの最大個数
#
# アラートID、メッセージの定義
#
Alart_Asibumi= 10     # 「正対不完全」のアラートID
Alart_Monomi = 30     # 「物見を定まらず」のアラートID
Alart_Daisan = 40     # 「大三移行不安定」のアラートID
Alart_KaiNasi = 50    # 「会なし離れ」のアラートID
Alart_KaiFusoku = 60  # 「会不十分な離れ」のアラートID
Alart_Hanare = 70     # 「離れタイミングずれ」のアラートID
#
Alart_msg = {
   0:'',
   10:'Warning:Detected illegal action in section-1.(SEITAI fukanzen)',
   100:'<警告>：「正対不完全」を検知しました。',
   30:'Warning:Detected illegal action in section-3.(MONOMI sadamarazu)',
   300:'<警告>：「物見定まらず」を検知しました。',
   40:'Warning:Detected illegal action in section-5.(DAISAN fumeikaku)',
   400:'<警告>：「大三移行不安定」を検知しました。',
   50:'Warning:Detected illegal action in section-5.(KAI nasi)',
   500:'<警告>：「会なし離れ」を検知しました。',
   60:'Warning:Detected illegal action in section-6.(KAI fusoku)',
   600:'<警告>：「会不十分な離れ」を検知しました。',
   70:'Warning:Detected illegal action in section-7.(Timing un-match)',
   700:'<警告>：「弓手押しタイミングの遅れ」を検知しました。'
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
