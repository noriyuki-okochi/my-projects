#
"""
"""
# appUtil
#     
import os
# local
import pandas as pd

# local package
from  kyudo.env import * 
from  kyudo.param import * 
from  mysqlite3.mysqlite3 import MyDb

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
#
#eof
