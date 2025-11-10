#
"""
"""
# appUtil
#     
import os
import pandas as pd
import math

#
# local package
from  kyudo.env import * 
from  kyudo.param import * 
from  mysqlite3.mysqlite3 import MyDb
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
            print(f"[chart]error:No tracking data. you must import csv-file.")
            return False
    
    if csvfile == '' or os.path.isfile(csvfile) == False:
        # ファイルが存在しないとき終了
        print(f"[chart]error: csv-file({csvfile}) not found.")
        return False    
    # CSVファイルを読み込む
    df = pd.read_csv(csvfile)
    print(f"[chart]:read_csv:{df.shape}")
    
    # DBへトラッキングデータ登録
    db.delete_tracking_data()      # 登録済データの削除
    df.to_sql('tracking_data', db.conn, if_exists='append', index=None, method='multi', chunksize=1024)
    print(f"[chart]info:import '{csvfile}' to 'tracking_data'{df.shape}.")
    # インポート実行回数更新
    count += 1
    db.update_frame_info('import', count)
    
    # 姿勢解析データをkyudo_dataテーブルへ登録
    csvfile = csvfile.replace('track','kyudo')
    if csvfile == '' or os.path.isfile(csvfile) == False:
        # ファイルが存在しないとき終了
        print(f"[chart]error: csv-file({csvfile}) not found.")
        return False    
    # CSVファイルを読み込む
    df = pd.read_csv(csvfile)
    print(f"[chart]:read_csv:{df.shape}")
    
    db.delete_kyudo_data()         # 登録済データの削除
    df.to_sql('kyudo_data', db.conn, if_exists='append', index=None, method='multi', chunksize=1024)
    print(f"[chart]info:import '{csvfile}' to 'kyudo_data'{df.shape}.")
    return True
#
# 登録ケースの削除関数
# db: MyDbデータベースオブジェクト
# case_name: 削除ケース名 
def delete_frame_info(db:MyDb, case_name):
    _,csvfile = db.get_file_path(case_name)
    if csvfile is not None:
        if db.delete_case(case_name) == True:
            print(f"[delete_frame_info]:info: case_name='{case_name}' deleted.")
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
#eof
