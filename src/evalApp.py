#
"""
"""
# evalApp main
#     
import sys
import os
# local
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
#import plotly.figure_factory as ff
from plotly.subplots import make_subplots
from datetime import datetime

# local package
from kyudo.env import * 
from kyudo.param import * 
from mysqlite3.mysqlite3 import MyDb
from kyudo.evalModel import *
from kyudo.kyudoUtils import *
from kyudo.appUtil import * 

#print(http.__file__) 
# 特異値の補正
def correct_singular_values(df_x:pd.DataFrame, df_y:pd.DataFrame) :
    
    # 欠測値を直前・直後の値に置換する
    df_x.ffill(inplace=True)    
    df_x.bfill(inplace=True) 

    for col in df_x.columns:
        if '_ratio' in col :
            df_x[col] = df_x[col].where(df_x[col] < 1.0)                    # 1.0以上は欠測値(NaN)に置換する
        if col == 'section':
            df_x[col] = df_x[col].where(df_x[col] < 10, df_x[col]%10)       # 0-9に収まるように補正する
            df_x[col] = df_x[col].where((df_x[col] > 0) & (df_x[col] < 9))  # 1-8意外な値は欠測値(NaN)に置換する
            df_x = df_x.astype({col:'Int64'})                               # 整数型に変換する   
    # 欠測値を含む行を削除する
    df_y = df_y.where(df_x ['section'] != np.nan)                   # df_xの'section'列がNaNの行は、df_yもNaNにする
    df_x.dropna(inplace=True)
    df_y.dropna(inplace=True)   # df_xの欠測値を含む行を削除する(df_yも対応して削除される)
    return df_x, df_y
#
# start of main
#
#
def main():
    global  Eval_output_dim, Eval_model_pt, Learning_rate, Augment_level
    verbose:bool = False         # debug write
    m_flg:bool = False           # not display section/conf
    slider:bool = False          # display slider
    predict:bool = False         # predict mode
    plot_loss:bool = False       # loss-file data
    plot_pred:bool = False       # predicted-file data 
    prompt:bool = True           # change csv-file name
    #
    # connect db
    db = MyDb(DB_PATH)
    #
    # print command line(arguments)
    args = sys.argv
    cmdline = "python "
    for arg in args:
        cmdline += f" {arg}"
    #    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_write( f'<< evalApp start at {timestamp} >>')
    log_write( f"[evalApp]:{cmdline}")
    mlog.info(f"[evalApp]:{cmdline}")
    #print(db)
    # コマンドライン引数を辞書に変換
    args_dict = {arg: idx for idx, arg in enumerate(args)}
    #log_write( f"[evalApp]info:args={args_dict}")

    key_names:str = []
    key_names.extend(Eval_data_names)


    opts:str = [opt for opt in args if opt.startswith('-')]
    if '-h' in opts:        #debug write
        print("evalApp.py -case {*|'<case-name>{,<case_name>'}... |-E(val) <label>|-eval|-img}\n"\
            + "        [<key_name1>[{ <key_name2>}...]|*]|{-loss <loss-file-path>}|{-predicted <predicted-file-path>}] \n"\
            + "        [-m(ulti)] [-b(ottom)] [-s(lider)] [-second <col_name1>{ <col_name2>}...] [-range '<min>[,<max>']]\n"\
            + "        [{-p(ast-frames)|-f(irst-frame)}'<count1>[,<count2>']] [<display-frames-count>] \n"\
            + "        [ {-train|-predict} [eta=<rate>] [{-modeln|-modelc} ['<model-path>']] ]\n"\
            + "        [-valid <case_name>|none] [augment=<level>]\n"\
            + "        [-hparam '(<s_frame>,<batch_size>,<n_epoc>[,<r_factor>,<section_embed_dim>,<completed_embed_dim>])']\n"\
            + "        [-dparam '(<t_shift>,<t_warp>,<noise>)']\n"\
            + "        [-inputkey][-h(elp)] [-d(ebug)] [-n(o-prompt)]\n")
        print(" --- Notation---")
        print(" '|': or,  '[]': optional,  '{}': group,  '...': repeat,  '<>': value")
        exit(0)
    # 
    cmds:str = [ key for key in args if key not in key_names and not key.isnumeric()]
    #
    if '-d' in opts:        #debug write
        verbose = True   
        mlog.setLevel(INFO)  

    if '-inputkey' in cmds:
        # 入力データキー一覧を表示して終了
        print(f"[evalApp]info:Input-Features-lists: default input_key={Eval_feature_key}   ")
        for key, features in Eval_Features_lists.items():
            print(f"  Input_key={key}:")
            for feat in features:
                print(f"    {feat}")
        exit(0)
        
    prompt_val:int = 0
    nvals = [opt[1:] for opt in opts if opt.startswith('-n')]
    if len(nvals) > 0:        #no prompt
        prompt = False
        if len(nvals[0]) > 1 and  nvals[0][1:].isnumeric(): prompt_val = int(nvals[0][1:])
        print(f"[evalApp]info:prompt:{prompt},val={prompt_val}")
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
    #
    # 対象ケース名を指定するコマンドオプションの解析
    #
    case_compare:bool = False
    case_names:str = []
    if '-case' in cmds:
        i = cmds.index('-case')
        if len(cmds) > (i + 1):
            # ケース名の指定は、カンマ区切りで複数指定可能
            names = cmds[i +1].split(',')
            for name in names:
                name = name.strip()
                if name != '': case_names.append(name)
            if len(names) > 1 and '-train' not in cmds:
                # ケース比較時の、比較ケース名を追加
                case_compare = True
                
    if len(case_names) == 0:
        print("[evalApp]:error:'-case <name>' must be specified.")
        exit(1)

    if len(case_names) and '-E' in opts:
        # Evalテーブルのlabelを更新
        label_l, _ = get_opt_values(args, '-E', 'c', '=')
        if len(label_l) == 2 and label_l[0].isnumeric() and label_l[1].isnumeric():
            # '<section>=<score>'の指定がある場合
            section = int(label_l[0])
            score = int(label_l[1])
            db.update_eval_label(case_names[0], section, score)
            exit(1)
        else:
            label_l, _ = get_opt_values(args, '-E', 'c', ',')
            # '<label1>,<label2>,...'の指定がある場合
            for i, label in enumerate(label_l):
                if label.isnumeric(): 
                    section = (i + 1) if i < 8 else ((i - 7) + 10)
                    db.update_eval_label(case_names[0], section, int(label))
        exit(0)
            
    valid_case:str = []
    if '-valid' in cmds:
        #検証対象ケース名の指定
        i = cmds.index('-valid')
        if len(cmds) > (i + 1) and cmds[i + 1] != 'none':
            valid_case.append(cmds[i +1])
            print(f"[evalApp]:valid_case:{valid_case}")
    #
    if '-eval' in cmds:
        # 指定ケースの評価用データを出力する
        print_eval_data(db, case_names)
        exit(0)

    # ケース名の存在チェック
    names = case_names.copy()
    if len(valid_case) > 0 and valid_case[0] not in names:
        names.append(valid_case[0])
    for name in names:
        db.case_name = name
        FPS, count = db.get_fps()
        if FPS is None:
            print(f"[evalApp]error:'{name}' not found in frame_info table.")
            exit(1)
        if count == 0 and '-import' not in cmds:
            print(f"[evalApp]error:'{name} import count is zero.")
            exit(1)

    #
    model_pth = None
    model_opt = None
    if   '-modeln' in cmds: model_opt = '-modeln'
    elif '-modelc' in cmds: model_opt = '-modelc'
    if model_opt is not None:
        i = cmds.index(model_opt)
        if len(cmds) > (i + 1) and cmds[i + 1][0] != '-' :
            model_pth = cmds[i +1]

    # ハイパーパラメータの設定
    # (s_frames, batch_size, n_epoch[, section_embed_dim, completed_embed_dim ])
    # (1,2,3)までの指定時は、埋め込みなし
    hyper_parameters = Hyper_parameters   
    if '-hparam' in cmds:
        hyper_parameters = get_hyper_parameters( cmds, '-hparam', hyper_parameters )
        log_write( f"[evalApp]:hyper_parameters={hyper_parameters}")
    

    df_k = None     # 予測結果データフレーム
    num_classes:int = Eval_output_dim
            
    # inputkey=<num>の解析(使用する特徴量の抽出パターンの指定)
    input_key:int = Eval_feature_key

    # eta=<rate>の解析(学習率の指定)
    num_opts = [opt for opt in args if opt.startswith('eta')]
    if len(num_opts) > 0: 
        # inputkey=<no>の解析
        params = num_opts[0].split('=')
        if len(params) == 2:
            Learning_rate = float(params[1])
    print(f"[evalApp]info:Learning_rate = {Learning_rate}")

    # データ拡張レベルの指定(augment=<level>)
    augment_level:int = Augment_level
    num_opts = [opt for opt in args if opt.startswith('augment')]
    if len(num_opts) > 0:
        params = num_opts[0].split('=')
        if len(params) == 2 and params[1].isnumeric():
            augment_level = int(params[1])
    print(f"[evalApp]info:Augment_level = {augment_level}, Augment_param={Augment_param}")
    
    augment_params = get_augment_parameters( Augment_param, augment_level )
    log_write( f"[evalApp]:augment_params={augment_params}")
    
    #
    # <<< NNモデルの学習、または予測の実行 >>>
    #
    if ('-train' in cmds or '-predict' in cmds) and len(case_names) > 0 :
        #
        # GRUモデルの学習、または予測を指定するコマンドオプションの解析
        if '-predict' in cmds: predict = True
        if predict and model_pth is None:
            #  予測実行時は学習済モデルファイルの指定が必須
            #print(f"[evalApp]error:'-predict' requires '-model <model-path>'")
            #exit(0)
            model_pth = Eval_model_pt      # デフォルトの学習済モデルファイルを使用する
        
        #  
        # 学習用データの読み込み
        features = Eval_Features_lists[input_key]
        input_dim = len(features)
        if input_key >= 170:
            # 特徴量の抽出パターンが170以上の場合、sectionのone-hot encodingを使用
            input_dim -= 1   # sectionの列(-1)は削除する
        log_write( f"[evalApp]:features:{features}")
        # 指定ケース名の全セクションのデータを読み込み（frame_noをインデックスに設定）
        df_x = db.pandas_read_eval( features, case_names )     # 学習用特徴量(input_frames, input_dim)                       
        # 教師ラベルデータの読み込み
        df_y = db.pandas_read_eval( ['label as label'] , case_names)    # 教師ラベル(input_frames, 1)
        df_x, df_y = correct_singular_values(df_x, df_y)   # 特異値の補正
        if verbose:
            # debug write 
            df2csv(df_x, case_names[0], title=f'df_x ', file=f'./log/eval_debug_{case_names[0]}.csv')
            df2csv(df_y, case_names[0], title=f'df_y ', file=f'./log/eval_debug_{case_names[0]}.csv')

        print(f"[evalApp]:df_x.shape={df_x.shape}, df_y.shape={df_y.shape}")   
        
        # 学習データの使用範囲の指定がある場合の処理
        pf_vals = (df_x.shape[0],df_x.shape[0])   # (max_frames, display_frames)

        # numpy配列に変換
        x = df_x.to_numpy(dtype=np.float32)         # (input_frames, input_dim)
        y = df_y.to_numpy(dtype=np.int64)           # (input_frames, 1)
        np_train = (x, y)
        
        # 検証用データの読み込みとnumpy配列への変換
        np_valid = None #TODO
        if len(valid_case) > 0:  
            df_x = db.pandas_read_eval( features, valid_case )             # 評価用特徴量(input_frames, input_dim)                       
            df_y = db.pandas_read_eval( ['label as label'] , valid_case)   # 教師ラベル(input_frames, 1)
            df_x, df_y = correct_singular_values(df_x, df_y)                # 特異値の補正
            print(f"[evalApp]:val_x.shape={df_x.shape}, val_y.shape={df_y.shape}")   
            np_valid = (df_x.to_numpy(dtype=np.float32), df_y.to_numpy(dtype=np.int64))
        
        # 学習パラメータ
        s_frames, batch_size, n_epoch, r_factor, section_dim, completed_dim = hyper_parameters
        completed_dim = 0
        log_write( f"[evalApp]:num_classes:{num_classes}")
        log_write( f"[evalApp]:s_frames={s_frames}, s_time={(s_frames/FPS):.2f}[s]")    
        log_write( f"[evalApp]:section_embed_dim={section_dim}, completed_embed_dim={completed_dim}")
        #
        # Evalモデルのインスタンスを生成する
        #
        if model_opt == '-modeln':
            model = EvalNN( input_dim = input_dim, 
                            s_frames = s_frames,
                            output_size = num_classes,
                            section_embed_dim = section_dim)
            model.to( get_device() )
        elif model_opt == '-modelc':
            model = EvalCN( input_dim = input_dim, 
                            s_frames = s_frames,
                            output_size = num_classes)
            model.to( get_device() )
        else:
            print(f"[evalApp]error:'Illegal model option:{model_opt}")
            exit(1)
        # モデル情報の表示
        log_write( f"[evalApp]:model\n {model}")
        log_write( f"[evalApp]:input_dim={input_dim}, output_size={num_classes}")
        numel_params = [p.numel() for p in model.parameters() if p.requires_grad]
        log_write( f"[evalApp]: numel parameters={sum(numel_params)}, {numel_params}")   
        
        # 学習済モデルの読み込み
        if model_pth is not None:
            if os.path.isfile(model_pth):
                model.load_state_dict(torch.load(model_pth, map_location=get_device()))
                log_write(f"[evalApp]:model loaded from {model_pth}")
            elif predict:
                print(f"[evalApp]error:model-file({model_pth}) not found.")
                exit(1)
            else:
                print(f"[evalApp]:model-file({model_pth}) will be created.")
        
        # 学習、または予測の実行前の確認プロンプト
        if prompt or (prompt_val == 1):
            print(f">Are you sure?: [y/n]")
            value = input(f">")
            if value != 'y' or len(value) == 0: exit(1)
        
        # 学習、または予測の実行
        if not predict:   
            # 学習実行前のパラメータの表示   
            log_write( f"[evalApp]:batch_size={batch_size}, n_epoch={n_epoch}")
            log_write( f"[evalApp]:Learning_rate={Learning_rate:.5f}, r_factor={r_factor:.2f}")
            log_write( f"[evalApp]:L2_lambda={L2_lambda:.5f}, Early_stop={Early_stop}")
            # 学習実行(train)
            train_Model( model, s_frames, np_train, np_valid, batch_size, n_epoch, r_factor, 
                        pth = model_pth, augment_params=augment_params )
            
            # 学習結果のlossデータの読み込み、プロット準備
            csvfile = model.csvpath
            plot_loss = True
            df = pd.read_csv(csvfile, sep='\t')
            print(f"[evalApp]:read_csv:{df.shape}")
            mlast[0] = n_epoch
            last = n_epoch
            key_names.append('loss')
            args.append('loss') 
            if len(case_names) > 1: 
                name = case_names[0]
                case_names.clear()
                case_names.append(name)
        else:
            # 予測実行(predict)
            y_pred = predict_Eval( model, x, s_frames ) # x=numpy(input_frames, input_dim)
            print(f"[predict_Eval]:y_pred={y_pred}")   
            exit(0)
            '''
            
            # 入力、ラベル、予測結果データフレームの作成、保存、プロット準備
            #  （dtype='Int64'の指定でconcat後もintの型が保持された）
            df_yp = pd.DataFrame(y_pred, columns=['predicted'], dtype='Int64')
            df_p = pd.concat( [df_x, df_y, df_yp], axis=1 )
            # NaNを含む列がfloat型に変更される
            df_p = df_p.astype({'section':'Int64', 'completed':'Int64', 'label':'Int64'})
            out_csv = f"predict_{case_names[0]}.csv"
            df2csv(df_p, title=None, file=out_csv)
            print(f"[evalApp]info:predict data saved as '{out_csv}'")
            mlast[0] = x.shape[0]
            last = mlast[0]
            m_flg = True   # 入力データと予測結果グラフを表示
            '''
    if '-img' in opts:
        # 指定ケースの評価用データをグレースケール画像で表示するコマンドオプションの解析
        if len(case_names) > 0 :
            # 学習用データの読み込み
            features = Eval_Features_lists[input_key]
            input_dim = len(features)
            # 指定ケース名の全セクションのデータを読み込み（frame_noをインデックスに設定）
            df_x = db.pandas_read_eval( features, case_names )              # 学習用特徴量(input_frames, input_dim)                       
            # 教師ラベルデータの読み込み
            df_y = db.pandas_read_eval( ['label as label'] , case_names)    # 教師ラベル(input_frames, 1)
            df_x, df_y = correct_singular_values(df_x, df_y)                # 特異値の補正
            df_x['section'] = df_x['section'] / 8
            np_x = df_x.to_numpy(dtype=np.float32)                          # (input_frames, input_dim)
            np_y = df_y.to_numpy(dtype=np.int64)                            # (input_frames, 1)
            print(f"[evalApp]info:np_x.shape={np_x.shape}")

            # section毎にフレーム数をs_framesに合わせて切り出す
            s_frames, _, _, _, _, _ = hyper_parameters                      # 1サンプルのフレーム数         np_x, _ = eval_data_squeeze(np_x, np_y, s_frames)     
            np_ch, _ = eval_data_unSqueeze(np_x, np_y, s_frames)            # (input_samples, s_frames, input_dim)
            inum, s_frames, input_dim = np_ch.shape
            print(f"[evalApp]info:inum={inum}, s_frames={s_frames}, input_dim={input_dim}")
            
            if augment_params is not None:
                # データをTensorに変換しデータ拡張する（データ拡張の効果を視覚的に確認するため）
                device = get_device()
                x_tensor = torch.tensor(np_ch, dtype=torch.float32).to(device )   #[inum, s_frames, input_dim]
                print(f"[evalApp]:x_tensor={x_tensor.shape}")            
                # データ拡張
                for i in range( inum ):
                    x_tensor[i] = eval_data_augment( x_tensor[i], augment_params )
                np_ch = x_tensor.to('cpu').detach().numpy().copy()

            # 節ごとのデータを列方向に連結して表示する
            sections = []
            gray_img = np_ch[0,:, :]                                        # (s_frames, input_dim)
            sections.append(np_ch[0, 0, -1])            
            for i in range(1, inum):
                gray_img = np.concatenate( (gray_img, np_ch[i,:, :]), axis=1 )         # (i*s_frames, input_dim)
                sections.append(np_ch[i, 0, -1])
                
            print(f"[evalApp]info:gray_img.shape={gray_img.shape}")
            fig = px.imshow(gray_img, color_continuous_scale='gray', title=f"Eval-data({sections}) Image plot")
            fig.update_xaxes(range=(1, inum*input_dim), dtick=input_dim)
            fig.show()
        else:
            print("[evalApp]error:'-img' requires '-case <name>'.")
        exit(0)
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
            print(f"[evalApp]error: csv-file({csvfile}) not found.")
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
        print(f"[evalApp]:read_csv:{csvfile}, {df.shape}")
        x_len = df.shape[0]
        mlast[0] = x_len
        last = x_len
        key_names.append(key)
        args.append(key)      # key_namesに'loss' or 'predicted'を追加
    #
    # 2軸のカラムを指定するコマンドオプションの解析
    #
    second_names:str = []
    if '-second' in args:
        idx = args.index('-second') + 1
        while idx < len(args):
            name = args[idx]
            if name in Eval_data_names: second_names.append(name)
            idx += 1
    #
    m_compare:bool = False
    if '-m' in opts :       # 信頼度データとセクション移行グラフを表示
    #    if case_compare is False and plot_loss is False:
        if plot_loss is False:
            m_flg = True
            if case_compare: m_compare = True
    print(f"[evalApp]info:m_flg={m_flg}, m_compare={m_compare}")    
    #
    # 表示対象のキーポイントを指定するコマンドオプションの解析
    #
    selkeys:str = [key for key in args if key in key_names]
    selnum:int = len(selkeys)
    if m_compare:
        selnum = 1
        selkeys.clear()
        selkeys.append('m_compare')
    # 二軸指定のキーポイントは表示対象から除外する
    for name in second_names:
        if name in selkeys:
            selkeys.remove(name)
            selnum -= 1

    if selnum == 0: 
        selnum = 1
        selkeys.append('all')         # all keys
    #
    if plot_loss:
        selkeys[0] = df.columns[1]    # 2列目を対象
        print(f"[evalApp]:selkeys:{selkeys}, df.columns:{df.columns}")    
    #
    # 1軸のrangeを指定するコマンドオプションの解析
    #
    range_min:float = None
    range_max:float = None
    if '-range' in args:
        i = args.index('-range')
        if len(args) > (i + 1):
            ranges = args[i+1].split(',')
            try:
                if ranges[0] != '': 
                    range_min = float(ranges[0])
                if len(ranges) > 1 and ranges[1] != '': 
                    range_max = float(ranges[1])
            except ValueError:
                pass
    print(f"[evalApp]info:range_min={range_min},range_max={range_max}.")
    #
    # その他、コマンドオプションの解析
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
    if case_compare and len(second_names) > 0:
        print("[evalApp]info:'-second' was ignored.")
        second_names.clear()
    #
    #
    #  <<< プロットのサブプロット領域の定義、作成 >>>
    #
    if selnum == 4:
        fig = make_subplots(rows=2, cols=2, vertical_spacing=0.1,
                            x_title='Frame count', y_title='Norm/Height',
                            subplot_titles=[key for key in selkeys],
                            specs=[[{"secondary_y": True}, {"secondary_y": True}],
                                [{"secondary_y": True}, {"secondary_y": True}]])
    elif selnum == 1:
        if m_flg == True and not m_compare:
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
                            subplot_titles=[key for key in selkeys if key != ''],
                            specs=[[{"secondary_y": True}], [{"secondary_y": True}]])
    #
    if verbose:
        print(f"[evalApp]option:{opts}")                 # オプション引数
        print(f"[evalApp]selkeys:{selkeys}")             # 選択キーポイント名
        print(f"[evalApp]seconds:{second_names}")        # 二軸選択キーポイント名
        print(f"[evalApp]case_names:{case_names}")
        print(f"[evalApp]mlast:{mlast}, last:{last}")    # 表示フレーム数   
        print(f"[evalApp]case_compare={case_compare}, section_conf={m_flg}")   
        print(f"[evalApp]selnum:{selnum}")           
        fig.print_grid()
    #
    # <<< データのプロット実行メイン >>>
    #
    for icount, key in enumerate(selkeys, start=1):
        print(f"[evalApp]info:Plot icount={icount},key={key}")
        #if icount > 2:
        #    print(f"[evalApp]info:icount({icount}) > 2 break.")
        #    break
        for icase, case_name in enumerate(case_names):
            print(f"[evalApp]info:Plot icase={icase},case={case_name}")
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
            cols:list = []
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
                print(f"[evalApp]info:dfk{dfk.shape}")
                # 実測データの読み込み
                df = db.pandas_read_kyudo()
                print(f"[evalApp]info:df{df.shape}")
            elif predict:
                # 予測結果データフレームの読み込み
                features = Features_lists[Current_feature_key]
                cols = get_feature_colnames( features )
                #dfk = df_p  
                dfk.dropna(how="any", inplace=True)  # 欠測値(NaN)を含む行を削除
                mdfk = dfk
                # 実測データの読み込み
                df = db.pandas_read_kyudo()
                print(f"[evalApp]info:df{df.shape}")
                if pf_vals is not None:            
                    mdf = df.tail(pf_vals[0])
                    mdf = mdf.head(pf_vals[1])
                    print(f"[evalApp]info:mdf{mdf.shape}")
            else:
                features = Eval_Features_lists[input_key]
                dfk = db.pandas_read_eval(features, case_names, index=None)
                df = db.pandas_read_eval( ['label as label'] , case_names)    # 教師ラベル(input_frames, 1)
                dfk, df = correct_singular_values(dfk, df)   # 特異値の補正
                print(f"[evalApp]info:dfk{dfk.shape}")
                # 特異値の補正
                for col in dfk.columns:
                    if ('_deg' in col) or ('_ratio' in col) :
                        cols.append(col)
                if Eyes_ratio_threshold > 0.0:
                    dfk['eyes_ratio'] = dfk['eyes_ratio'].where(dfk['eyes_ratio'] > Eyes_ratio_threshold, Eyes_ratio_min)
                    dfk['eyes_ratio'] = dfk['eyes_ratio'].where(dfk['eyes_ratio'] == Eyes_ratio_min, Eyes_ratio_max)
            #
            # フレーム範囲の取得    
            start_frame_no = dfk.index[0]
            last_frame_no = dfk.index[-1]
            frame_length = last_frame_no - start_frame_no + 1
            print(f"[evalApp]info:frame_no = [{start_frame_no} -> {last_frame_no}]")
            #
            # データの作成、編集
            # 表示範囲の計算とデータの抽出
            #
            if icount == 1 and not (plot_loss or plot_pred or predict):
                if not p_option:   # '-fxxxx' は開始フレームをフレーム数で指定
                    mlast[icase] = frame_length - mlast[icase]
                if last > mlast[icase] or last == 0: 
                    last = mlast[icase]
                print(f"[evalApp]info:mlast[{icase}]={mlast[icase]}, last={last}")               
            #
            if not predict:
                mdf = df.tail(mlast[icase])
                mdf = mdf.head(last)
                mdfk = dfk.tail(mlast[icase])
                mdfk = mdfk.head(last)

            print(f"[evalApp]info:mdfk{mdfk.shape}")
            print(f"[evalApp]info:frame_no = [{mdfk.index[0]} -> {mdfk.index[-1]}]")
            #
            # データのプロット
            #
            if key == 'all':        # 学習データの入力項目プロット
                for name in cols:
                    secondary:bool = True if 'deg' in name else False
                    try :
                        fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                                    name = name,
                                                    y = mdfk[name], 
                                                    mode = "lines"),
                                            row = irow, 
                                            col = icol,   
                                            secondary_y = secondary
                                        )
                    except KeyError:
                        print(f"[evalApp]warning:{name} not found.")            
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
            elif not m_compare:             # 学習用生データ
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
            if icount <= len(second_names):
                print(f"[evalApp]info:icount:{icount}, secondary-key:{second_names[icount - 1]}")
                fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                            name=second_names[icount - 1],
                                            y=mdfk[second_names[icount - 1]], 
                                            mode="lines"),
                                    row = irow, 
                                    col = icol,   
                                    secondary_y=True
                                )
            # < section/conf >
            if m_flg == True:
                irow = irow if m_compare else 2
                #< label >
                fig = fig.add_trace( go.Scatter(x=mdf.index, 
                                        name="label",
                                        y=mdf["label"], 
                                        marker_color= 'black',
                                        mode="markers"),
                                row = irow,
                                col = 1   
                            )
                # < tag1:face>
                fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                            name = "split",
                                            y = mdfk["split_m"], 
                                            mode = "lines"),
                                    row = irow, 
                                    col = 1,   
                                    secondary_y = False
                            )
                # < tag2:body>
                '''                
                fig = fig.add_trace( go.Scatter(x=mdfk.index, 
                                            name = "alart",
                                            y = mdfk["alart"], 
                                            mode = "lines"),
                                    row = irow, 
                                    col = 1,   
                                    secondary_y = False
                            )
                '''
                # < section >
                fig = fig.add_trace( go.Bar(x=mdfk.index, 
                                        name="section",
                                        y=mdfk["section"],
                                        marker_color='grey'),
                                row = irow, 
                                col = 1,
                                secondary_y=True
                            )
                # < completed >
                fig = fig.add_trace( go.Bar(x=mdfk.index, 
                                        name="completed",
                                        y=mdfk["completed"],
                                        marker_color='black'),
                                row = irow, 
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
                                    row = irow, 
                                    col = 1   
                                )
            #signal
            #next case
        #
        #next symbol
    #
    # <<< レイアウト詳細設定 >>>
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
            if len(second_names) > 1:
                fig.update_yaxes(title_text=second_names[1],  
                                secondary_y=True, showgrid=False,
                                row=2, col=1)
        elif selnum == 1:
            if len(second_names) > 0:
                fig.update_yaxes(title_text=second_names[0],  
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
            if len(second_names) > 0:
                fig.update_yaxes(title_text=second_names[0], secondary_y=True, showgrid=False,
                                row=2, col=1)
            fig.update_yaxes(title_text="label/face/body", range=(0, 3), secondary_y=False,
                                row=2, col=1)
            fig.update_yaxes(title_text="section-no/completed", range=(0, 10), secondary_y=True, showgrid=True, 
                                row=2, col=1)
            fig.update_traces(dict(showlegend = False), 
                                row=2, col=1)
            if m_compare:
                fig.update_yaxes(title_text="label/face", range=(0, 3), secondary_y=False,
                                    row=1, col=1)
                fig.update_yaxes(title_text="section-no", range=(0, 10), secondary_y=True, showgrid=True, 
                                    row=1, col=1)
                fig.update_traces(dict(showlegend = False), 
                                    row=1, col=1)
    #
    # <<< プロットの表示(open the figure in  web-browser) >>>
    #
    fig.show()
    # 
    #fig.write_html('candle_figure.html', auto_open=True)
    #
    # <<< CSVファイルのリネーム処理 >>>
    #
    if prompt and (plot_loss or predict):
        while True:
            value = ''
            #if predict: csvfile = out_csv
            promptStr = csvfile[-18:-4] if plot_loss else csvfile[8:-4]
            print(f">Please input new-file-name( {csvfile} ).!: [/:cancle]")
            value = input(f"{promptStr} -> :")
            if value == '/' or len(value) == 0: break
            prefix = csvfile[:-18] if plot_loss else csvfile[:8]
            newfile = f"{prefix}{value}.csv" 
            if os.path.isfile(newfile) == True:
                print(f"{newfile} is already exsit.Overwrite? [y/n]:")
                value = input(f":")
                if value.lower() == 'n': continue
                os.remove(newfile)
            os.rename(csvfile, newfile)
            print(f"[evalApp]info:{csvfile} renamed to '{newfile}'")
            break
    return
#
#
if __name__ == "__main__":
    print(os.getcwd())
    main()

#eof
