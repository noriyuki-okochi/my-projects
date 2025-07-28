#
"""
"""
# chart main
#     
import sys
import os
# local
import pandas as pd
import plotly.graph_objects as go
#import plotly.figure_factory as ff
from plotly.subplots import make_subplots

# local package
from  env import * 
from mysqlite3.mysqlite3 import MyDb

#print(http.__file__)
#
# start of main
#
#
verbose:bool = False         # debug write
m_flg:bool = False           # not display section/conf
#
# connect db
db = MyDb(DB_PATH)
#
# print command line(arguments)
args = sys.argv
cmdline = ""
for arg in args:
    cmdline += f" {arg}"
    
print(os.getcwd())
print('<< chart start >>')
print(cmdline)
#print(db)

key_names:str = [name for name in Kn2idx]

opts:str = [opt for opt in args if opt.startswith('-')]
if '-h' in opts:        #debug write
    print("chart.py -case {'<case-name1>[,<case_name2>']|-L(ist-case_names)} [-import [<csv-file-path>]] \n"\
         + "        {<key_name1>|[ <key_name2>...]|*} [-range '<min>[,<max>']] [-second <col_name>] [-span] [-SMA <window> [-WMA <window>\n"\
         + "        [-p(ast-frames))] [-f(irst-frame)'<count1>[,<count2>']] [<display-frames>] \n"\
         + "        [-m(ulti)] [-b(ottom)] [-h(elp)] [-d(ebug)]")
    exit(0)
# 
cmds:str = [ key for key in args if key not in key_names and not key.isnumeric()]

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
    print(f"[chart]info:{fdf.shape}")
    rows, cols = fdf.shape
    for i in range(0, rows):
        print(f"----({i+1})----")
        print(fdf.iloc[i])        
    exit(0)

if len(case_names) == 0:
    print("[chart]:error:'-case <name>' must be specified.")
    exit(0)

# ケース名の存在チェック
for name in case_names:
    db.case_name = name
    FPS, count = db.get_fps()
    if FPS is None:
        print(f"[chart]error:'{names} not found in frame_info table.")
        exit(0)
#print(f"[chart]info:FPS={FPS:.3f}, import_count={count}")
#
# CSVデータのインポートを指定するコマンドオプションの解析
#
if '-import' in cmds:
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
        print(f"[chart]error: csv-file({csvfile}) not found.")
        exit(0)    
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
#
if count == 0:
    print(f"[chart]error:No tracking data. you must import csv-file.")
    exit(0)
#
# 表示対象のキーポイントを指定するコマンドオプションの解析
#
selkeys:str = [key for key in args if key in key_names]
selnum:int = len(selkeys)
if selnum == 0:
    for key in key_names[7:11]:
        selkeys.append(key)         # all keys
    selnum = 4   
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
print(f"[chart]info:range_min={range_min},range_max={range_max}.")
#
# 2軸のカラムを指定するコマンドオプションの解析
#
second_name:str = None
if '-second' in args:
    i = args.index('-second')
    if len(args) > (i + 1):
        second_name = args[i+1]
        if second_name not in Col_names:
            print(f"[chart]error:'{second_name}' not found. following names variable.")
            print(Col_names)
            exit()
#
# spanデータの表示を指定するコマンドオプションの解析
#
span_visible:bool = False
if '-span' in args:
    span_visible = True
#
## 移動平均データの表示を指定するコマンドオプションの解析
sma_visible:bool = False
sma_window:int = Window_size
wma_visible:bool = False
wma_window:int = Window_size

if '-SMA' in args:
    sma_visible = True
    i = args.index('-SMA')
    if len(args) > (i + 1) and args[i+1].isnumeric():
        sma_window = int(args[i+1])
        if sma_window < 2 or sma_window > 20:
            print(f"[chart]error:illegal SMA window size:{sma_window}.")
            exit(0)
if '-WMA' in args:
    wma_visible = True
    i = args.index('-WMA')
    if len(args) > (i + 1) and args[i+1].isnumeric():
        wma_window = int(args[i+1])
        if wma_window < 2 or wma_window > 20:
            print(f"[chart]error:illegal WMA window size:{wma_window}.")
            exit(0)
##
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
pf_opt = [opt[1:] for opt in opts if opt.startswith('-p') or opt.startswith('-f')]
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
    if case_compare == True:
        print("[chrart]error: 'multi case-name' and '-m' cannot be specified at the same time.")
        exit(0)
    while len(selkeys) > 1: del selkeys[1]      # 先頭キーポイントのみ対象
    m_flg = True
#
if '-b' in opts:        #凡例の表示位置
    legend_dict = dict(x=0.01,y=0.01,xanchor='left',yanchor='bottom',orientation='h')
else:
    legend_dict = dict(x=0.01,y=0.99,xanchor='left',yanchor='top',orientation='h')
#
if '-d' in opts:        #debug write
    verbose = True   
#
# コマンドオプションの合理性判定
#
if m_flg or case_compare: 
    selnum = 1                                  # 選択キーポイント数を1に設定
    while len(selkeys) > 1: del selkeys[1]      # 先頭キーポイントのみ対象    
#
if case_compare and second_name is not None:
    print("[chart]info:'-second' was ignored.")
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
        fig = make_subplots(rows=2, cols=1, vertical_spacing=0.2,
                            subplot_titles=[selkeys[0],'xy_conf'],
                            specs=[[{"secondary_y": True}], [{"secondary_y": True}]])
    elif case_compare == True:
        fig = make_subplots(rows=2, cols=1, vertical_spacing=0.1,
                            subplot_titles=[key for key in case_names])
    else:
        fig = make_subplots(rows=1, cols=1, 
                            subplot_titles=[selkeys[0]],
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
        # 'tracking-data'テーブルからのデータ読み込み
        #
        db.case_name = case_name
        df = db.pandas_read_tracking( Kn2idx[key] )
        print(f"[chart]info:{df.shape}")
        start_frame_no = df.index[0]
        last_frame_no = df.index[-1]
        frame_length = last_frame_no - start_frame_no + 1
        print(f"[chart]info:frame_no = [{start_frame_no} -> {last_frame_no}]")
        #
        # データの作成、編集
        #
        if span_visible:
            df['eyes_ratio'] = df["eyes_span"]/df["box_h"]                       # バウンダリーボックスの高さに対する比率に変換
            df['eyes_ratio'] = df['eyes_ratio'].where(df['eyes_ratio'] < 0.5)   #  0.5以上は欠測地(NaN)に置換する
            df['eyes_ratio'].ffill()                                            # 欠測値を直前の値に置換する
            
            df['shds_ratio'] = df["shds_span"]/df["box_h"]
            df['hips_ratio'] = df["hips_span"]/df["box_h"]

        if sma_visible:        
            # 単純移動平均
            df['SMA_norm'] = df["ratio"].rolling(sma_window).mean()   
            
        if wma_visible:        
            # 加重移動平均
            #weights = [0.1, 0.2, 0.3, 0.4, 0.5]
            #weights = np.arange(1, wma_window + 1)
            weights = WMA_weights
            df['WMA_norm'] = df["ratio"].rolling(wma_window).apply(lambda x: np.dot(x, weights) / sum(weights), raw=True)
        #
        # 表示範囲の計算とデータの抽出
        #
        if icount == 1:
            if not p_option:   # '-fxxxx' は開始フレームをフレーム数で指定
                mlast[icase] = frame_length - mlast[icase]
            if last > mlast[icase] or last == 0: 
                last = mlast[icase]
            print(f"[chart]info: mlast[{icase}]={mlast[icase]}, last={last}")                
                
        #
        mdf = df.tail(mlast[icase])
        if mlast[icase] > last:
            mdf = mdf.head(last)
        print(f"[chart]info:{mdf.shape}")
        print(f"[chart]info:frame_no = [{mdf.index[0]} -> {mdf.index[-1]}]")
        #
        # データのプロット
        # < ratio >
        fig = fig.add_trace( go.Scatter(x=mdf.index, 
                                    name="ratio",
                                    y=mdf["ratio"], 
                                    mode="lines"),
                                    #line_color= 'gray',                                  
                                    #line={'dash':'dot'},
                            row = irow, 
                            col = icol   
                        )
        #  
        if sma_visible:
            #  < 単純移動平均 >
            fig = fig.add_trace( go.Scatter(x=mdf.index, 
                                        name=f"SMA{sma_window}",
                                        y=mdf["SMA_norm"], 
                                        mode="lines",
                                        #line_color= 'gray',                                  
                                        line={'dash':'dot'}),
                                row = irow, 
                                col = icol   
                            )
        if wma_visible:
            #  < 加重移動平均 >
            fig = fig.add_trace( go.Scatter(x=mdf.index, 
                                        name=f"WMA{wma_window}",
                                        y=mdf["WMA_norm"], 
                                        mode="lines",
                                        #line_color= 'gray',                                  
                                        line={'dash':'dot'}),
                                row = irow, 
                                col = icol   
                            )
            
        if span_visible:
            # < eyes_span >
            fig = fig.add_trace( go.Scatter(x=mdf.index, 
                                        name="eyes-span",
                                        y=mdf["eyes_ratio"], 
                                        mode="lines"),
                                row = irow, 
                                col = icol   
                            )
            # < shds_span >
            fig = fig.add_trace( go.Scatter(x=mdf.index, 
                                        name="shoulders-span",
                                        y=mdf["shds_ratio"], 
                                        mode="lines"),
                                row = irow, 
                                col = icol   
                            )
            # < hips_span >
            fig = fig.add_trace( go.Scatter(x=mdf.index, 
                                        name="hips-span",
                                        y=mdf["hips_ratio"], 
                                        mode="lines"),
                                row = irow, 
                                col = icol   
                            )
        # < add secondary column >
        if selnum == 1 and second_name is not None:
            fig = fig.add_trace( go.Scatter(x=mdf.index, 
                                        name=second_name,
                                        y=mdf[second_name], 
                                        mode="lines"),
                                row = irow, 
                                col = icol,   
                                secondary_y=True
                            )
        # < section/conf >
        if m_flg == True:
            #< conf >
            fig = fig.add_trace( go.Scatter(x=mdf.index, 
                                    name="conf",
                                    y=mdf["xy_conf"], 
                                    line_color= 'green',
                                    mode="lines"),
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
            # < tag1(completed) >
            fig = fig.add_trace( go.Scatter(x=mdf.index, 
                                    name="tag1",
                                    y=mdf["tag1"],
                                    marker_color= 'cyan',
                                    mode="markers"),
                            row = 2, 
                            col = 1,
                            secondary_y=True
                        )
            # < tag2(started) >
            fig = fig.add_trace( go.Scatter(x=mdf.index, 
                                    name="tag2",
                                    y=mdf["tag2"],
                                    marker_color= 'blue',
                                    mode="markers"),
                            row = 2, 
                            col = 1,
                            secondary_y=True
                        )
        #signal
        #next case
    #
    #next symbol
#
# レイアウト詳細設定
#
main_title = "YOLOv8 - Form-Chart"
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
        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update(layout_xaxis2_showticklabels = False)
        fig.update_layout(
            #xaxis_rangeslider = dict(visible=True),
            xaxis1_title = "Frame count", 
            yaxis = dict(title='norm/height',range=(range_min, range_max),showgrid=True), 
            yaxis3= dict(title='conf', side='left', showgrid=True), 
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
