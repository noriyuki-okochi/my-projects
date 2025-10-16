#
"""
"""
# kyudoApp main
#     
import sys
import os
# local
import pandas as pd
import plotly.graph_objects as go
#import plotly.figure_factory as ff
from plotly.subplots import make_subplots
from datetime import datetime

# local package
from kyudo.env import * 
from kyudo.param import * 
from mysqlite3.mysqlite3 import MyDb
from kyudo.kyudoModel import *
from kyudo.kyudoUtils import *

#print(http.__file__)
#
# start of main
#
#
verbose:bool = False         # debug write
m_flg:bool = False           # not display section/conf
slider:bool = False          # display slider
predict:bool = False         # predicted data
plot_csv:bool = False        # csv-file data
#
# connect db
db = MyDb(DB_PATH)
#
# print command line(arguments)
args = sys.argv
cmdline = ""
for arg in args:
    cmdline += f" {arg}"
#    
print(os.getcwd())
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
log_write(f'<< kyudoApp start at {timestamp} >>')
log_write(f"[kyudoApp]info:cmdline={cmdline}")
#print(db)
# コマンドライン引数を辞書に変換
args_dict = {arg: idx for idx, arg in enumerate(args)}
ulog.info(f"[kyudoApp]info:args={args_dict}")

key_names:str = [name for name in Kn2idx]
feature_names = ['box_conf', 'box_w', 'box_h',\
                 'rw_norm', 'lw_norm',\
                 'rl_norm', 'rl_angle', 'hr_norm', 'hr_angle',\
                 'er_angle', 'sl_angle',\
                 'eyes_norm', 'hips_norm']
key_names.extend(feature_names)

opts:str = [opt for opt in args if opt.startswith('-')]
if '-h' in opts:        #debug write
    print("kyudoApp.py -case {-L(ist)|'<case-name1>[,<case_name2>']} [-D(elete)] [-import [<csv-file-path>]] \n"\
         + "        [{<key_name1>|[ <key_name2>...]|*}|{-csv <csv-file-path>}] [-m(ulti)] [-b(ottom)] [-s(lider)]\n"\
         + "        [-second <col_name>] [-range '<min>[,<max>']]\n"\
         + "        [-p(ast-frames))] [-f(irst-frame)'<count1>[,<count2>']] [<display-frames>] \n"\
         + "        [<section>=<no>] [-train|-predict] [{-models|-modelm} ['<model-path>']] [-hparam '(<s_frame>,<batch_size>,<n_epoc>)']\n"\
         + "        [-h(elp)] [-d(ebug)]")
    exit(0)
# 
cmds:str = [ key for key in args if key not in key_names and not key.isnumeric()]
#
if '-d' in opts:        #debug write
    verbose = True   
#
# 対象ケース名を指定するコマンドオプションの解析
#
case_compare:bool = False
case_names:str = []
if '-case' in cmds:
    i = cmds.index('-case')
    if len(cmds) > (i + 1):
        names = cmds[i +1].split(',')
        case_names.append(names[0])
        if len(names) > 1 :
            # ケース比較時の、比較ケース名を追加
            case_names.append(names[1])
            case_compare = True
            
if len(case_names) > 0 and case_names[0] == '-L':
    #
    # 登録済ケースの一覧表示
    #
    fdf = db.pandas_read_frame()
    print(f"[kyudoApp]info:{fdf.shape}")
    rows, cols = fdf.shape
    for i in range(0, rows):
        print(f"----({i+1})----")
        print(fdf.iloc[i])        
    exit(0)

if len(case_names) > 0 and '-D' in opts:
    #
    # 登録済ケースの削除
    #
    for name in case_names:
        if db.delete_case(name) is True:
            print(f"[kyudoApp]:info: case_name='{name}' deleted.")
        else:
            print(f"[kyudoApp]:error: case_name='{name}' not found.")            
    exit(0)
if len(case_names) == 0:
    print("[kyudoApp]:error:'-case <name>' must be specified.")
    exit(0)

# ケース名の存在チェック
for name in case_names:
    db.case_name = name
    FPS, count = db.get_fps()
    if FPS is None:
        print(f"[kyudoApp]error:'{names} not found in frame_info table.")
        exit(0)
#print(f"[kyudoApp]info:FPS={FPS:.3f}, import_count={count}")
#
# CSVデータのインポートを指定するコマンドオプションの解析
#
if '-import' in cmds and len(case_names) > 0 :
    db.case_name = case_names[0]    # 対象は先頭のケース名に限定
    csvfile = ''
    i = cmds.index('-import')
    if len(cmds) > (i + 1):
        # トラッキングCSVファイルの切り出し
        if not cmds[i+1].startswith('-'): csvfile = cmds[i+1]
    if csvfile == '':
        # コマンドラインで指定のない時はframe_infoテーブルから取得
        i, csvfile = db.get_file_path()
    
    if csvfile == '' or os.path.isfile(csvfile) == False:
        # ファイルが存在しないとき終了
        print(f"[kyudoApp]error: csv-file({csvfile}) not found.")
        exit(0)    
    # CSVファイルを読み込む
    df = pd.read_csv(csvfile)
    print(f"[kyudoApp]:read_csv:{df.shape}")
    
    # DBへトラッキングデータ登録
    db.delete_tracking_data()      # 登録済データの削除
    df.to_sql('tracking_data', db.conn, if_exists='append', index=None, method='multi', chunksize=1024)
    print(f"[kyudoApp]info:import '{csvfile}' to 'tracking_data'{df.shape}.")
    # インポート実行回数更新
    count += 1
    db.update_frame_info('import', count)
    
    # 姿勢解析データをkyudo_dataテーブルへ変換登録
    csvfile = csvfile.replace('track','kyudo')
    if csvfile == '' or os.path.isfile(csvfile) == False:
        # ファイルが存在しないとき終了
        print(f"[chart]error: csv-file({csvfile}) not found.")
        exit(0)    
    # CSVファイルを読み込む
    df = pd.read_csv(csvfile)
    print(f"[chart]:read_csv:{df.shape}")
    
    db.delete_kyudo_data()         # 登録済データの削除
    df.to_sql('kyudo_data', db.conn, if_exists='append', index=None, method='multi', chunksize=1024)
    print(f"[chart]info:import '{csvfile}' to 'kyudo_data'{df.shape}.")
    
    # DBトラッキングデータをkyudo_dataテーブルへ変換登録
    #db.conv_tracking2kyudo()  # 変換登録
    #print(f"[chart]info:'conv tracking_data' -> 'kyudo_data'.")
#
if count == 0:
    print(f"[kyudoApp]error:No tracking data. you must import csv-file.")
    exit(0)
#
model_pth = None
model_opt = None
if '-models' in cmds: model_opt = '-models'
if '-modelm' in cmds: model_opt = '-modelm'
if model_opt is not None:
    i = cmds.index( model_opt )
    if len(cmds) > (i + 1) and cmds[i + 1][0] != '-' : model_pth = cmds[i +1]
#
hyper_parameters = (60, 16, 5)   # s_frames, batch_size, n_epoch 
if '-hparam' in cmds:
    i = cmds.index('-hparam')
    if len(cmds) > (i + 1):
        params = cmds[i+1][1:-1].split(',')
        if len(params) == 3 and \
           (params[0].isnumeric() and params[1].isnumeric() and params[2].isnumeric()):
            hyper_parameters = (int(params[0]), int(params[1]), int(params[2]))

# section=<no>の解析（指定セクションのデータのみ学習、またはプロット）
df_k = None     # 予測結果データフレーム
section:int = None
sect_opts = [opt for opt in args if opt.startswith('section')]
if len(sect_opts) > 0: 
    # section=<no>の解析
    params = sect_opts[0].split('=')
    if len(params) == 2 and params[1].isnumeric():
        section = int(params[1])
#
if ('-train' in cmds or '-predict' in cmds) and len(case_names) > 0 :
    #
    # GRUモデルの学習、または予測を指定するコマンドオプションの解析
    if '-predict' in cmds: predict = True
    if predict and model_pth is None:
        #  予測実行時は学習済モデルファイルの指定が必須
        print(f"[kyudoApp]error:'-predict' requires '-model <model-path>'")
        exit(0)
    #  学習用データの読み込み
    features = ['rw_norm/box_h as rw_ratio','lw_norm/box_h as lw_ratio',\
            'eyes_norm/box_w as eyes_ratio',\
            'hr_norm/box_h as hr_ratio','hr_angle/180.0 as hr_deg',\
            'section','completed']
    input_dim = len(features)
    log_write(f"[kyudoApp]:features:{features}")
    if section is None:
        # 指定ケース名の全セクションのデータを読み込み（frame_noをインデックスに設定）
        df_x = db.pandas_read_kyudo( features )        # 学習用特徴量(input_frames, input_dim)                       
    else:
        # 指定セクションのデータを読み込み（frame_noをインデックスに設定）
        # section={section,section+1}を選択
        df_x = db.pandas_read_kyudo_section( features, section )    
    # 特異値の補正
    for col in df_x.columns:
        if '_ratio' in col :
            df_x[col] = df_x[col].where(df_x[col] < 1.0)    # 1.0以上は欠測値(NaN)に置換する
    df_x.ffill(inplace=True)    # 欠測値を直前の値に置換する
    df_x.bfill(inplace=True)    # 欠測値を直後の値に置換する    
    if verbose: df2csv(df_x, case_names[0], title=f'df_x after clean on section = {section}')
    
    if section is None:
        df_y = db.pandas_read_kyudo( ['label'] )    # 教師ラベル(input_frames, 1)
    else:    
        df_y = db.pandas_read_kyudo_section( ['label'], section )  # section={section,section+1}を選択
    if verbose: df2csv(df_y, case_names[0], title=f'df_y on section = {section}')
    
    # numpy配列に変換
    x = df_x.to_numpy(dtype=np.float32)         # (input_frames, input_dim)
    y = df_y.to_numpy(dtype=np.int64)           # (input_frames, 1)
    #
    # GRUモデルの学習を実行する
    #
    #num_classes = 3    # 0:完了への移行, 1:動作完了, 2:動作開始
    num_classes = 19    
    # 0:完了への移行, 1:動作完了, 2:動作開始
    # (8セクションx2+2)=0~18
    if model_opt == '-models':
        model = KyudoGRUs( input_size = input_dim, output_size = num_classes )
        model.to( get_device() )
    else:
        model = KyudoGRUm( input_size = input_dim, output_size = num_classes )
        model.to( get_device() )
    # モデル情報の表示
    log_write(f"[kyudoApp]:model\n {model}")
    log_write(f"[kyudoApp]:input_size={input_dim}, output_size={num_classes}")
    
    # 学習済モデルの読み込み
    if model_pth is not None:
        if os.path.isfile(model_pth):
            model.load_state_dict(torch.load(model_pth, map_location=get_device()))
            log_write(f"[kyudoApp]:model loaded from {model_pth}")
        else:
            print(f"[kyudoApp]error:model-file({model_pth}) not found.")
            
    # 学習パラメータ
    s_frames, batch_size, n_epoch = hyper_parameters
    log_write(f"[kyudoApp]:s_frames={s_frames}, s_time={(s_frames/FPS):.2f}[s]")
    log_write(f"[kyudoApp]:batch_size={batch_size}, n_epoch={n_epoch}")
    log_write(f"[kyudoApp]:section:{section}")
    if not predict:      
        # 学習実行
        train_Kyudo( model, x, y, s_frames, batch_size, n_epoch, pth = model_pth )
        exit(0)
    else:
        # 予測実行
        y_pred = predict_Kyudo( model, x, s_frames )
        # 入力、ラベル、予測結果データフレームの作成
        df_yp = pd.DataFrame(y_pred, columns=['predicted'])
        df_p = pd.concat( [df_x, df_y, df_yp], axis=1 )
        
        out_csv = f"kyudo_predict_{case_names[0]}.csv"
        df2csv(df_p, title='df_p on predict', file=out_csv)
        print(f"[kyudoApp]info:predict data saved as '{out_csv}'")
#
# CSVデータのプロットコマンド(-csv)オプションの解析
#
if '-csv' in cmds:
    csvfile = ''
    i = cmds.index('-csv')
    if len(cmds) > (i + 1):
        # トラッキングCSVファイルの切り出し
        if not cmds[i+1].startswith('-'): csvfile = cmds[i+1]
    if csvfile == '' or os.path.isfile(csvfile) == False:
        # ファイルが存在しないとき終了
        print(f"[kyudoApp]error: csv-file({csvfile}) not found.")
        exit(0)    
    # CSVファイルを読み込む     
    plot_csv = True
    df = pd.read_csv(csvfile)
    print(f"[kyudoApp]:read_csv:{df.shape}")
    key_names.append('csv')
    args.append('csv')      # key_namesに'csv'を追加
#
# 表示対象のキーポイントを指定するコマンドオプションの解析
#
selkeys:str = [key for key in args if key in key_names]
selnum:int = len(selkeys)
if selnum == 0: 
    selnum = 1
    selkeys.append('all')         # all keys
#
if plot_csv:
    selkeys[0] = df.columns[1]    # 2列目を対象)
    print(f"[kyudoApp]:selkeys:{selkeys}, df.columns:{df.columns}")    
#
# 1軸のrangeを指定するコマンドオプションの解析
#
range_min:float = 0.00
range_max:float = 0.40
if '-range' in args:
    i = args.index('-range')
    if len(args) > (i + 1):
        range = args[i+1].split(',')
        try:
            if range[0] != '': 
                range_min = float(range[0])
            if len(range) > 1 and range[1] != '': 
                range_max = float(range[1])
        except ValueError:
            pass
print(f"[kyudoApp]info:range_min={range_min},range_max={range_max}.")
#
# 2軸のカラムを指定するコマンドオプションの解析
#
second_name:str = None
if '-second' in args:
    i = args.index('-second')
    if len(args) > (i + 1):
        second_name = args[i+1]
        if second_name not in Col_names:
            print(f"[kyudoApp]error:'{second_name}' not found. following names variable.")
            print(Col_names)
            exit()
#
#
# 表示範囲のindexを指定するコマンドオプションの解析
#
LAST_FRAMES = 500               # display frames(default is 500 frames)
last:int = int(LAST_FRAMES)     # 表示フレーム数      
mlast:int = [None, None]
p_option:bool = True            # '-p'オプションは遡って表示するフレーム数を指定  


#
nums = [int(num) for num in args if num.isnumeric()]
if len(nums) > 0:               # display frames
    last = int(nums[0])         # frames
#
pf_opt = [opt[1:] for opt in opts if (opt.startswith('-p') and not opt.startswith('-pred')) or opt.startswith('-f')]
# '-pxxx'は最後から遡るフレーム数を指定、 '-fxxxx'は開始フレーム数を指定
#  -f'xxxx,yyyy'はケース比較時の、各ケースに対する開始フレーム数を指定
if len(pf_opt) > 0:
    nums = pf_opt[0].split(',')
    if nums[0][0] == 'f':       
        p_option = False
    if nums[0][1:].isnumeric(): mlast[0] = int(nums[0][1:])
    if len(nums) > 1 and nums[1].isnumeric():  mlast[1] = int(nums[1])
    else: mlast[1] = mlast[0]
else:
    mlast[0] = mlast[1] = last

# その他、コマンドオプションの解析
#
if '-m' in opts :       # 信頼度データとセクション移行グラフを表示
    if case_compare == True or plot_csv == True:
        print("[chrart]error: '(multi case-name' or csv plot) and '-m' cannot be specified at the same time.")
        exit(0)
    while len(selkeys) > 1: del selkeys[1]      # 先頭キーポイントのみ対象
    m_flg = True
#
if '-b' in opts:        #凡例の表示位置
    legend_dict = dict(x=0.01,y=0.01,xanchor='left',yanchor='bottom',orientation='h')
else:
    legend_dict = dict(x=0.01,y=0.99,xanchor='left',yanchor='top',orientation='h')
#
if '-s' in opts:        #display slider
    slider = True   
#
# コマンドオプションの合理性判定
#
if m_flg or case_compare: 
    selnum = 1                                  # 選択キーポイント数を1に設定
    while len(selkeys) > 1: del selkeys[1]      # 先頭キーポイントのみ対象    
#
if case_compare and second_name is not None:
    print("[kyudoApp]info:'-second' was ignored.")
    second_name = None
#
# プロットのサブプロット領域の定義、作成
#
if selnum == 4:
    fig = make_subplots(rows=2, cols=2, vertical_spacing=0.1,
                        x_title='Frame count', y_title='Norm/Height',
                        subplot_titles=[key for key in selkeys])
elif selnum == 1:
    if m_flg == True :
        if len(selkeys) > 0 and selkeys[0] != 'all':
            fig = make_subplots(rows=2, cols=1, vertical_spacing=0.2,
                            subplot_titles=[selkeys[0],'xy_conf'],
                            shared_xaxes=True,
                            specs=[[{"secondary_y": True}], [{"secondary_y": True}]])
        else:
            fig = make_subplots(rows=2, cols=1, vertical_spacing=0.2,
                            subplot_titles=['Features','Predict'],
                            shared_xaxes=True,
                            specs=[[{"secondary_y": True}], [{"secondary_y": True}]])
    elif case_compare == True:
        fig = make_subplots(rows=2, cols=1, vertical_spacing=0.1,
                            subplot_titles=[key for key in case_names])
    else:
        if len(selkeys) > 0 and selkeys[0] != 'all':
            fig = make_subplots(rows=1, cols=1, 
                            subplot_titles=[selkeys[0]],
                            specs=[[{"secondary_y": True}]])
        else:
            fig = make_subplots(rows=1, cols=1, 
                            subplot_titles=['Features'],
                            specs=[[{"secondary_y": True}]])
else:
    fig = make_subplots(rows=2, cols=1, vertical_spacing=0.1,
                        subplot_titles=[key for key in selkeys if key != ''])
#
if verbose:
    print(f"option:{opts}")             # オプション引数
    print(f"selkeys:{selkeys}")         # 選択キーポイント名
    print(f"case_names:{case_names}")
    print(f"last:{last}")               # 表示フレーム数   
    print(f"mlast:{mlast}")             # 表示フレーム数   
    print(f"case_compare={case_compare}, section_conf={m_flg}")   
    print(f"selnum:{selnum}")           
    fig.print_grid()
#
#  データのプロット実行メイン
#
for icount, key in enumerate(selkeys, start=1):
    for icase, case_name in enumerate(case_names):
        # 表示ブロック(irow,icol)の指定
        if selnum == 4:
            irow = int((icount+1)/2)
            icol = int((icount+1)%2 + 1)
        else:
            irow = icount + icase
            icol = 1
        #
        # 'kyudo-data'テーブルからのデータ読み込み
        # (-csvオプション指定時はCSVファイルから読み込み)
        db.case_name = case_name
        if plot_csv:
            dfk = df
        elif predict:
            dfk = df_p
            dfk.dropna(how="any", inplace=True)  # 欠測値(NaN)を含む行を削除
            df = db.pandas_read_kyudo()
            print(f"[kyudoApp]info:df{df.shape}")
        else:
            if section is not None:
                dfk = db.pandas_read_kyudo_section(section = section)
            else:  dfk = db.pandas_read_kyudo()
            df = dfk
            print(f"[kyudoApp]info:dfk{dfk.shape}")
            # 特異値の補正
            for col in dfk.columns:
                if '_norm' in col :
                    # box_w以上は欠測地(NaN)に置換する
                    dfk[col] = dfk[col].where(dfk[col] < dfk['box_w'])
            dfk.ffill(inplace=True)    # 欠測値を直前の値に置換する
            dfk.bfill(inplace=True)    # 欠測値を直後の値に置換する
            # データの正規化
            dfk['rw_ratio'] = dfk["rw_norm"]/dfk["box_h"] 
            dfk['lw_ratio'] = dfk["lw_norm"]/dfk["box_h"] 
            dfk['eyes_ratio'] = dfk["eyes_norm"]/dfk["box_w"] 
            dfk['hr_ratio'] = dfk["hr_norm"]/dfk["box_h"]
            dfk['hr_deg'] = dfk["hr_angle"]/180.0
        # フレーム範囲の取得    
        start_frame_no = dfk.index[0]
        last_frame_no = dfk.index[-1]
        frame_length = last_frame_no - start_frame_no + 1
        print(f"[kyudoApp]info:frame_no = [{start_frame_no} -> {last_frame_no}]")
        #
        # データの作成、編集
        # 表示範囲の計算とデータの抽出
        #
        if icount == 1:
            if not p_option:   # '-fxxxx' は開始フレームをフレーム数で指定
                mlast[icase] = frame_length - mlast[icase]
            if last > mlast[icase] or last == 0: 
                last = mlast[icase]
            print(f"[kyudoApp]info:mlast[{icase}]={mlast[icase]}, last={last}")               
        #
        mdf = df.tail(mlast[icase])
        mdfk = dfk.tail(mlast[icase])
        if mlast[icase] > last:
            mdf = mdf.head(last)
            mdfk = mdfk.head(last)
        print(f"[kyudoApp]info:mdfk{mdfk.shape}")
        print(f"[kyudoApp]info:frame_no = [{mdfk.index[0]} -> {mdfk.index[-1]}]")
        #
        # データのプロット
        #
        if key != 'all':
            # < ratio >
            fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                        name=key,
                                        y=mdfk[key], 
                                        mode="lines"),
                                        #line_color= 'gray',                                  
                                        #line={'dash':'dot'},
                                row = irow, 
                                col = icol   
                            )
        else:
            # < rw_ratio >
            fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                        name="rw_ratio",
                                        y=mdfk["rw_ratio"], 
                                        mode="lines"),
                                row = irow, 
                                col = icol   
                            )
            '''
            # < lw_ratio >
            fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                        name="lw_ratio",
                                        y=mdfk["lw_ratio"], 
                                        mode="lines"),
                                row = irow, 
                                col = icol   
                            )
            '''
            # < eyes_ratio >            
            fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                        name="eyes_ratio",
                                        y=mdfk["eyes_ratio"], 
                                        mode="lines"),
                                row = irow, 
                                col = icol   
                            )
            # < rl_ratio >
            # < hr_ratio >
            fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                        name="hr_ratio",
                                        y=mdfk["hr_ratio"], 
                                        mode="lines"),
                                row = irow, 
                                col = icol,   
                                secondary_y=True
                            )
            '''
            # < rl_deg >
            # < hr_deg >
            fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                        name="hr_deg",
                                        y=mdfk["hr_deg"], 
                                        mode="lines"),
                                row = irow, 
                                col = icol,   
                                secondary_y=True
                            )
            '''
        #              
        # < add secondary column >
        if selnum == 1 and second_name is not None:
            fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                        name=second_name,
                                        y=mdfk[second_name], 
                                        mode="lines"),
                                row = irow, 
                                col = icol,   
                                secondary_y=True
                            )
        # < section/conf >
        if m_flg == True:
            #< label >
            fig = fig.add_trace( go.Scatter(x=mdf.index, 
                                    name="label",
                                    y=mdf["label"], 
                                    marker_color= 'red',
                                    mode="markers"),
                            row = 2, 
                            col = 1   
                        )
            # < section >
            fig = fig.add_trace( go.Bar(x=mdf.index, 
                                    name="section",
                                    y=mdf["section"],
                                    marker_color='grey'),
                            row = 2, 
                            col = 1,
                            secondary_y=True
                        )
            # < completed >
            fig = fig.add_trace( go.Bar(x=mdf.index, 
                                    name="completed",
                                    y=mdf["completed"],
                                    marker_color='black'),
                            row = 2, 
                            col = 1,
                            secondary_y=True
                        )
            #< predict >
            if predict:
                fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                        name="predicted",
                                        y=mdfk["predicted"], 
                                        marker_color= 'black',
                                        mode="markers"),
                                row = 2, 
                                col = 1   
                            )
                # < section >
                '''
                fig = fig.add_trace( go.Bar(x=mdfk.index, 
                                        name="section",
                                        y=mdfk["section"],
                                        marker_color='white'),
                                row = 2, 
                                col = 1,
                                secondary_y=True
                            )
                '''
            '''
            # < tag1(completed) >
            fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                    name="tag1",
                                    y=mdfk["tag1"],
                                    marker_color= 'cyan',
                                    mode="markers"),
                            row = 2, 
                            col = 1,
                            secondary_y=True
                        )
            # < tag2(started) >
            fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                    name="tag2",
                                    y=mdfk["tag2"],
                                    marker_color= 'blue',
                                    mode="markers"),
                            row = 2, 
                            col = 1,
                            secondary_y=True
                        )
            '''
        #signal
        #next case
    #
    #next symbol
#
# レイアウト詳細設定
#
main_title = "GRU - Model-Chart"
if not case_compare:
    main_title = f"{main_title}({case_names[0]})"
else:
    main_title = f"{main_title}({selkeys[0]})"
        
fig.update_layout(
    #autosize = False,
    title = {
        "text": main_title,
        "y": 0.9,
        "x": 0.5,
    },
    legend = legend_dict,
 )
fig.update_traces(dict(showlegend = False), selector = dict(type='Scatter'))

if selnum == 4:
    fig.update(layout_xaxis_rangeslider_visible=False)
    fig.update(layout_xaxis2_rangeslider_visible=False)
    fig.update(layout_xaxis3_rangeslider_visible=False)
    fig.update(layout_xaxis4_rangeslider_visible=False)
    fig.update_yaxes(range=(range_min, range_max))
    fig.update_layout(
        showlegend = False
    )
else:
    if selnum == 2:
        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update(layout_xaxis2_rangeslider_visible=False)
        fig.update(layout_xaxis2_showticklabels = False)
        fig.update_traces(dict(showlegend = False), row=2, col=1)
        fig.update_yaxes(range=(range_min, range_max))
        #fig.update_xaxes(showticklabels = False)
    elif selnum == 1:
        if second_name is not None:
            fig.update_yaxes(title_text=second_name,  
                            secondary_y=True, showgrid=False,
                            row=1, col=1)
    if m_flg == True :
        if slider:
            fig.update(layout_xaxis2_rangeslider_visible=True)
        fig.update(layout_xaxis2_showticklabels = True)
        fig.update_layout(
            #xaxis_rangeslider = dict(visible=True),
            xaxis1_title = "Frame count", 
            #yaxis = dict(title='norm/height',range=(range_min, range_max),showgrid=True), 
            yaxis3= dict(title='label', side='left', showgrid=True), 
            showlegend = True
        )
        if second_name is not None:
            fig.update_yaxes(title_text=second_name, secondary_y=True, showgrid=False,
                            row=1, col=1)
        fig.update_yaxes(title_text="section-no", range=(0, 14), secondary_y=True, showgrid=True, 
                            row=2, col=1)
        fig.update_traces(dict(showlegend = False), 
                            row=2, col=1)
#
# プロットの表示(open the figure in  web-browser)
#
fig.show()
# 
#fig.write_html('candle_figure.html', auto_open=True)
#
#
#eof
