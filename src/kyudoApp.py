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
from kyudo.appUtil import * 

#print(http.__file__)
#
# start of main
#
#
verbose:bool = False         # debug write
m_flg:bool = False           # not display section/conf
slider:bool = False          # display slider
predict:bool = False         # predict mode
plot_loss:bool = False       # loss-file data
plot_pred:bool = False       # predicted-file data
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
key_names.extend(Kyudo_data_names)

opts:str = [opt for opt in args if opt.startswith('-')]
if '-h' in opts:        #debug write
    print("kyudoApp.py -case {-L(ist)|'<case-name1>[,<case_name2>']} [-D(elete)] [-import [<csv-file-path>]] \n"\
         + "        [{<key_name1>|[ <key_name2>...]|*}|{-loss <loss-file-path>}|{-predicted <predicted-file-path>}] \n"\
         + "        [-m(ulti)] [-b(ottom)] [-s(lider)] [-second <col_name>] [-range '<min>[,<max>']]\n"\
         + "        [{-p(ast-frames)|-f(irst-frame)}'<count1>[,<count2>']] [<display-frames-count>] \n"\
         + "        [{-train|-predict}  [<classes>=<num>] [<section>=<no>]  {-models|-modelm} ['<model-path>']]\n"\
         + "        [-hparam '(<s_frame>,<batch_size>,<n_epoc>[,<section_embed_dim>,<completed_embed_dim>])']\n"\
         + "        [-h(elp)] [-d(ebug)]")
    exit(0)
# 
cmds:str = [ key for key in args if key not in key_names and not key.isnumeric()]
#
if '-d' in opts:        #debug write
    verbose = True   
#
# 表示範囲のindexを指定するコマンドオプションの解析
#
LAST_FRAMES = 501                   # display frames(default is 501)
last:int = 0                        # {-f|-p}指定時のデフォルト表示フレーム数      
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
    last = int(LAST_FRAMES)        # default display frames
    mlast[0] = mlast[1] = last
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
        delete_frame_info(db, name)
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
    if count == 0 and '-import' not in cmds:
        print(f"[kyudoApp]error:'{names} import count is zero.")
        exit(0)
#print(f"[kyudoApp]info:FPS={FPS:.3f}, import_count={count}")
#c
# CSVデータのインポートを指定するコマンドオプションの解析
#
if '-import' in cmds and len(case_names) > 0 :
    # 対象は先頭のケース名に限定
    if import_tracking_data(db, cmds, case_names[0]) is False:
        exit(0)
#
model_pth = None
model_opt = None
if '-models' in cmds: model_opt = '-models'
if '-modelm' in cmds: model_opt = '-modelm'
if model_opt is not None:
    i = cmds.index( model_opt )
    if len(cmds) > (i + 1) and cmds[i + 1][0] != '-' : 
        model_pth = cmds[i +1]
        if model_pth.startswith('classes') or model_pth.startswith('section'): 
            model_pth = None

# ハイパーパラメータの設定
# (s_frames, batch_size, n_epoch[, section_embed_dim, completed_embed_dim ])
# (1,2,3)までの指定時は、埋め込みなし
hyper_parameters = Hyper_parameters   
if '-hparam' in cmds:
    hyper_parameters = get_hyper_parameters( cmds, hyper_parameters )

# section=<no>の解析（指定セクションのデータのみ学習、またはプロット）
df_k = None     # 予測結果データフレーム
section:int = None
sect_opts = [opt for opt in args if opt.startswith('section')]
if len(sect_opts) > 0: 
    # section=<no>の解析
    params = sect_opts[0].split('=')
    if len(params) == 2 and params[1].isnumeric():
        section = int(params[1])

# class=<num>の解析(出力クラス数の指定)
#num_classes = 3    # 0:完了への移行, 1:動作完了, 2:動作開始
#num_classes = 19   # (8セクションx2+2)=0~18 
num_classes:int = 3
num_opts = [opt for opt in args if opt.startswith('classes')]
if len(num_opts) > 0: 
    # classes=<no>の解析
    params = num_opts[0].split('=')
    if len(params) == 2 and params[1].isnumeric():
        num_classes = int(params[1])
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
    features = Features_list_7 if Input_dim == 7 else Features_list_8
    input_dim = len(features)
    log_write(f"[kyudoApp]:input_dim={input_dim}")
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
        df_y = db.pandas_read_kyudo( ['label as label'] )    # 教師ラベル(input_frames, 1)
    else:    
        df_y = db.pandas_read_kyudo_section( ['label as label'], section )  # section={section,section+1}を選択
    if verbose: df2csv(df_y, case_names[0], title=f'df_y on section = {section}')

    # 学習データの使用範囲の指定がある場合の処理
    pf_vals = None
    if len(pf_opt) > 0:
        print(f"[kyudoApp]df_x.shape={df_x.shape}")   
        print(f"[kyudoApp]info:mlast={mlast[0]}, last={last}")    # 表示フレーム数   
        if not p_option:   # '-fxxxx' は開始フレームをフレーム数で指定
            frame_length = df_x.index[-1] - df_x.index[0] + 1
            mlast[0] = frame_length - mlast[0]
        if last > mlast[0] or last == 0: 
            last = mlast[0]
        pf_vals = (mlast[0], last)               
        print(f"[kyudoApp]info:mlast={mlast[0]}, last={last}")
        df_x = df_x.tail(mlast[0])
        df_y = df_y.tail(mlast[0])
        df_x = df_x.head(last)
        df_y = df_y.head(last)   
    # numpy配列に変換
    x = df_x.to_numpy(dtype=np.float32)         # (input_frames, input_dim)
    y = df_y.to_numpy(dtype=np.int64)           # (input_frames, 1)
    # 学習パラメータ
    s_frames, batch_size, n_epoch, section_dim, completed_dim = hyper_parameters
    log_write(f"[kyudoApp]:num_classes:{num_classes}")
    log_write(f"[kyudoApp]:s_frames={s_frames}, s_time={(s_frames/FPS):.2f}[s]")    
    log_write(f"[kyudoApp]:batch_size={batch_size}, n_epoch={n_epoch}")
    log_write(f"[kyudoApp]:section_embed_dim={section_dim}, completed_embed_dim={completed_dim}")
    log_write(f"[kyudoApp]:section-option={section}")
    #
    # GRUモデルのインスタンスを生成する
    #
    if model_opt == '-models':
        model = KyudoGRUs( input_size = input_dim, output_size = num_classes,
                          section_embed_dim = section_dim,
                          completed_embed_dim = completed_dim )
        model.to( get_device() )
    elif model_opt == '-modelm':
        model = KyudoGRUm( input_size = input_dim, output_size = num_classes,
                          hidden_size = 32,
                          section_embed_dim = section_dim,
                          completed_embed_dim = completed_dim )
        model.to( get_device() )
    else:
        print(f"[kyudoApp]error:'Illegal model option:{model_opt}")
        exit(0)
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
    if not predict:      
        # 学習実行(train)
        train_Kyudo( model, x, y, s_frames, batch_size, n_epoch, pth = model_pth )
        csvfile = model.csvpath
        plot_loss = True
        df = pd.read_csv(csvfile, sep='\t')
        print(f"[kyudoApp]:read_csv:{df.shape}")
        mlast[0] = n_epoch
        last = n_epoch
        key_names.append('loss')
        args.append('loss') 
    else:
        # 予測実行(predict)
        y_pred = predict_Kyudo( model, x, s_frames )
        # 入力、ラベル、予測結果データフレームの作成
        #  （dtype='Int64'の指定でconcat後もintの型が保持された）
        df_yp = pd.DataFrame(y_pred, columns=['predicted'], dtype='Int64')
        df_p = pd.concat( [df_x, df_y, df_yp], axis=1 )
        # NaNを含む列がfloat型に変更される
        df_p = df_p.astype({'section':'Int64', 'completed':'Int64', 'label':'Int64'})
        out_csv = f"predict_{case_names[0]}.csv"
        df2csv(df_p, title=None, file=out_csv)
        print(f"[kyudoApp]info:predict data saved as '{out_csv}'")
        mlast[0] = x.shape[0]
        last = mlast[0]
        m_flg = True   # 入力データと予測結果グラフを表示
#
# CSVデータのプロットコマンド(-loss|-predicted)オプションの解析
#
if '-loss' in cmds or '-predicted' in cmds:
    csvfile = ''
    i = cmds.index('-loss') if '-loss' in cmds else cmds.index('-predicted')
    if len(cmds) > (i + 1):
        # トラッキングCSVファイルの切り出し
        if not cmds[i+1].startswith('-'): csvfile = cmds[i+1]
    if csvfile == '' or os.path.isfile(csvfile) == False:
        # ファイルが存在しないとき終了
        print(f"[kyudoApp]error: csv-file({csvfile}) not found.")
        exit(0)    
    # CSVファイル区分判定 
    key = 'loss' if '-loss' in cmds else 'predicted'
    # CSVファイルを読み込む
    if key == 'predicted':  
        df = pd.read_csv(csvfile, sep='\t', index_col=0)
        plot_pred = True
        m_flg = True
    else:  
        df = pd.read_csv(csvfile, sep='\t')
        plot_loss = True 
    print(f"[kyudoApp]:read_csv:{csvfile}, {df.shape}")
    x_len = df.shape[0]
    mlast[0] = x_len
    last = x_len
    key_names.append(key)
    args.append(key)      # key_namesに'loss' or 'predicted'を追加
#
# 2軸のカラムを指定するコマンドオプションの解析
#
second_name:str = None
if '-second' in args:
    i = args.index('-second')
    if len(args) > (i + 1):
        second_name = args[i+1]
        if second_name not in Kyudo_data_names:
            print(f"[kyudoApp]error:'{second_name}' not found. following names variable.")
            print(Kyudo_data_names)
            exit()
#
# 表示対象のキーポイントを指定するコマンドオプションの解析
#
selkeys:str = [key for key in args if key in key_names]
selnum:int = len(selkeys)
if second_name in selkeys:
    selkeys.remove(second_name)
    selnum -= 1

if selnum == 0: 
    selnum = 1
    selkeys.append('all')         # all keys
#
if plot_loss:
    selkeys[0] = df.columns[1]    # 2列目を対象
    print(f"[kyudoApp]:selkeys:{selkeys}, df.columns:{df.columns}")    
#
# 1軸のrangeを指定するコマンドオプションの解析
#
range_min:float = None
range_max:float = None
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
# その他、コマンドオプションの解析
#
if '-m' in opts :       # 信頼度データとセクション移行グラフを表示
    if case_compare is False and plot_loss is False:
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
        if len(selkeys) > 0 :
            if selkeys[0] == 'all':\
                titles = ['features','predicted label'] if predict else ['features','section/completed/label']
            elif selkeys[0] == 'predicted':
                titles = [selkeys[0],'real']
            else:
                titles = [selkeys[0],'section/completed/label']
            fig = make_subplots(rows=2, cols=1, vertical_spacing=0.2,
                            subplot_titles=titles,
                            shared_xaxes=True,
                            specs=[[{"secondary_y": True}], [{"secondary_y": True}]])
    elif case_compare == True:
        fig = make_subplots(rows=2, cols=1, vertical_spacing=0.1,
                            subplot_titles=[key for key in case_names],
                            shared_xaxes=True,
                            specs=[[{"secondary_y": True}], [{"secondary_y": True}]])
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
    print(f"[kyudoApp]option:{opts}")                 # オプション引数
    print(f"[kyudoApp]selkeys:{selkeys}")             # 選択キーポイント名
    print(f"[kyudoApp]case_names:{case_names}")
    print(f"[kyudoApp]mlast:{mlast}, last:{last}")    # 表示フレーム数   
    print(f"[kyudoApp]case_compare={case_compare}, section_conf={m_flg}")   
    print(f"[kyudoApp]selnum:{selnum}")           
    fig.print_grid()
#
#  データのプロット実行メイン
#
for icount, key in enumerate(selkeys, start=1):
    print(f"[kyudoApp]info:Plot icount={icount},key={key}")
    if icount > 2:
        print(f"[kyudoApp]info:icount({icount}) > 2 break.")
        break
    for icase, case_name in enumerate(case_names):
        print(f"[kyudoApp]info:Plot icase={icase},case={case_name}")
        # 表示ブロック(irow,icol)の指定
        if selnum == 4:
            irow = int((icount+1)/2)
            icol = int((icount+1)%2 + 1)
        else:
            irow = icount + icase
            icol = 1
        #
        # 'kyudo-data'テーブルからのデータ読み込み
        # (-lossオプション指定時はCSVファイルから読み込み)
        db.case_name = case_name
        if plot_loss:
            # CSVファイル読み込みのlossデータ
            dfk = df
        elif plot_pred:
            # CSVファイル読み込みの予測データ
            df.dropna(how="any", inplace=True)  # 欠測値(NaN)を含む行を削除
            act_np = df['predicted'].to_numpy(dtype=np.int64)
            # 予測データ(action)からセクション、完了フラグの再計算
            sect_np = np.zeros_like(act_np)
            comp_np = np.zeros_like(act_np)
            section_np = df['section'].to_numpy(dtype=np.int64)
            completed_np = df['completed'].to_numpy(dtype=np.int64)
            section = section_np[0]
            completed = completed_np[0]
            for i in range(len(act_np)):
                act = act_np[i]
                if act == 1: completed = 1  # 動作完了
                if act == 2:                # 次セクションの動作開始
                    if section == 9:    # 最終セクション
                        section = 2     # 胴づくり
                    else: section += 1
                    completed = 0
                sect_np[i] = section
                comp_np[i] = completed
            dfk = pd.DataFrame( {'predicted': act_np,
                                 'section': sect_np,
                                 'completed': comp_np }, index=df.index )
            print(f"[kyudoApp]info:dfk{dfk.shape}")
            # 実測データの読み込み
            df = db.pandas_read_kyudo()
            print(f"[kyudoApp]info:df{df.shape}")
        elif predict:
            # 予測結果データフレームの読み込み
            dfk = df_p  
            dfk.dropna(how="any", inplace=True)  # 欠測値(NaN)を含む行を削除
            mdfk = dfk
            # 実測データの読み込み
            df = db.pandas_read_kyudo()
            print(f"[kyudoApp]info:df{df.shape}")
            if pf_vals is not None:            
                mdf = df.tail(pf_vals[0])
                mdf = mdf.head(pf_vals[1])
                print(f"[kyudoApp]info:mdf{mdf.shape}")
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
        if icount == 1 and not (plot_loss or plot_pred or predict):
            if not p_option:   # '-fxxxx' は開始フレームをフレーム数で指定
                mlast[icase] = frame_length - mlast[icase]
            if last > mlast[icase] or last == 0: 
                last = mlast[icase]
            print(f"[kyudoApp]info:mlast[{icase}]={mlast[icase]}, last={last}")               
        #
        if not predict:
            mdf = df.tail(mlast[icase])
            mdf = mdf.head(last)
            mdfk = dfk.tail(mlast[icase])
            mdfk = mdfk.head(last)

        print(f"[kyudoApp]info:mdfk{mdfk.shape}")
        print(f"[kyudoApp]info:frame_no = [{mdfk.index[0]} -> {mdfk.index[-1]}]")
        #
        # データのプロット
        #
        if key == 'all':        # 学習データの入力項目プロット
            # < rw_ratio >
            fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                        name="rw_ratio",
                                        y=mdfk["rw_ratio"], 
                                        mode="lines"),
                                row = irow, 
                                col = icol   
                            )
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
        #              
        elif key == 'predicted':    # CSVファイル入力の予測結果データのプロット
            #< label >
            fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                    name="predicted",
                                    y=mdfk["predicted"], 
                                    marker_color= 'black',
                                    mode="markers"),
                            row = 1, 
                            col = 1   
                        )
            # < section >
            fig = fig.add_trace( go.Bar(x=mdfk.index, 
                                    name="section",
                                    y=mdfk["section"],
                                    marker_color='grey'),
                            row = 1, 
                            col = 1,
                            secondary_y=True
                        )
            # < completed >
            fig = fig.add_trace( go.Bar(x=mdfk.index, 
                                    name="completed",
                                    y=mdfk["completed"],
                                    marker_color='black'),
                            row = 1, 
                            col = 1,
                            secondary_y=True
                        )
        else:                       # 学習用生データ
            # <one of kyudo_data >
            fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                        name=key,
                                        y=mdfk[key], 
                                        mode="lines"),
                                        #line_color= 'gray',                                  
                                        #line={'dash':'dot'},
                                row = irow, 
                                col = icol   
                            )
        # < add secondary column >  #   二軸指定の学習用生データ
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
                                    marker_color= 'black',
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
            if predict:             # 予測結果データのプロット
                fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                        name="predicted",
                                        y=mdfk["predicted"], 
                                        marker_color= 'red',
                                        mode="markers"),
                                row = 2, 
                                col = 1   
                            )
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
    if range_min is not None and range_max is not None:
        fig.update_yaxes(range=(range_min, range_max))
    fig.update_layout(
        showlegend = False
    )
else:
    if selnum == 2:
        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update(layout_xaxis2_rangeslider_visible=False)
        fig.update(layout_xaxis2_showticklabels = False)
        #fig.update_traces(dict(showlegend = False), row=2, col=1)
        if range_min is not None and range_max is not None:
            fig.update_yaxes(range=(range_min, range_max))
        #fig.update_xaxes(showticklabels = False)
    elif selnum == 1:
        if second_name is not None:
            fig.update_yaxes(title_text=second_name,  
                            secondary_y=True, showgrid=False,
                            row=1, col=1)
        if plot_loss is True:
            fig.update_xaxes(title_text="epoch-count")
        else:
            fig.update_xaxes(title_text=f"frame-count (1/{FPS:.2f}={1/FPS:.2f}sec.)")  
        if plot_pred: 
            fig.update_yaxes(title_text="label", range=(0, 3), secondary_y=False,
                            row=1, col=1)
            fig.update_yaxes(title_text="section-no", range=(0, 10), secondary_y=True,
                            row=1, col=1)
    if m_flg == True :
        if slider:
            fig.update(layout_xaxis2_rangeslider_visible=True)
        fig.update(layout_xaxis2_showticklabels = True)
        fig.update_layout(
            #xaxis_rangeslider = dict(visible=True),
            xaxis1_title = "frame count", 
            #yaxis = dict(title='norm/height',range=(range_min, range_max),showgrid=True), 
            yaxis3= dict(title='label', side='left', showgrid=True), 
            showlegend = True
        )
        if second_name is not None:
            fig.update_yaxes(title_text=second_name, secondary_y=True, showgrid=False,
                            row=1, col=1)
        fig.update_yaxes(title_text="label", range=(0, 3), secondary_y=False,
                            row=2, col=1)
        fig.update_yaxes(title_text="section-no", range=(0, 10), secondary_y=True, showgrid=True, 
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
if plot_loss or predict:
    while True:
        value = ''
        if predict: csvfile = out_csv
        prompt = csvfile[-18:-4] if plot_loss else csvfile[8:-4]
        print(f">Please input new-file-name( {csvfile} ).!: [/:cancle]")
        value = input(f"{prompt} -> :")
        if value == '/' or len(value) == 0: break
        prefix = csvfile[:-18] if plot_loss else csvfile[:8]
        newfile = f"{prefix}{value}.csv" 
        if os.path.isfile(newfile) == True:
            print(f"{newfile} is already exsit.Overwrite? [y/n]:")
            value = input(f":")
            if value.lower() == 'n': continue
            os.remove(newfile)
        os.rename(csvfile, newfile)
        print(f"[kyudoApp]info:{csvfile} renamed to '{newfile}'")
        break
#
#
#eof
