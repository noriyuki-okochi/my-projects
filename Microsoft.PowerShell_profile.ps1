# Sqlite3データベースパス設定
$env:DB_PATH = './yolo-kyudo_local.db'
#
# 動画ファイル検索位置設定
$env:ROLL_PATH='C:/Users/USER/Pictures/Camera Roll/'
# ホームディレクトリ設定
$HOME_DIR = 'f:/share/YOLO'
#
# ホームディレクトリに移動
set-location $HOME_DIR
python -V
write-output 'Hellow YOLO!!'
#
#
# 環境変数の設定
#
# データ入力キー設定
$env:INPUT_KEY="80"
$inputkey = $env:INPUT_KEY
# モデルオプション設定
# マルチヘッドモデル設定に変更（注：シングルヘッドをデフォルト、"-multi"オプションで指定時は関数kyudo内でハイパーパラメータを設定）
$env:MODEL_TYPE="-models"
$modelx = $env:MODEL_TYPE
# 学習済モデルファイル設定
$env:MODEL_PT="./kyudo2_80_modelse_8-96-3.pt"
$env:L2_LAMBDA="0.0"
$l2_lambda = $env:L2_LAMBDA
#
# ハイパーパラメータ設定
$s = 96     # シーケンス長
$b = 32     # バッチサイズ
$e = 280    # エポック数
$r = 1.0    # 学習率の減衰率
$d_s = 8    # 埋め込み次元数(section)
$d_c = 4    # 埋め込み次元数(completed)
#
#$s = 128     # シーケンス長
#$b = 256    # バッチサイズ
#$e = 161    # エポック数
#$d_c = 6    # 埋め込み次元数(completed)
$env:HYPER_PARAM=($s,$b,$e,$r,$d_s,$d_c)
$hp_vals = @($s,$b,$e,$r,$d_s,$d_c)
$hparam = $hp_vals[0],$hp_vals[1],$hp_vals[2],$hp_vals[3],$hp_vals[4],$hp_vals[5]
#
# 登録ケース名リスト
#
# 個別ケース設定例
$cases_list = "iwata_1.2", "okochi_1.2", "kanoda_1.2", "tuneyoshi_1.2"
$cases_list = "iijima_1.1", "iijima_1.2", "anbe_1.1","anbe_1.2"
$cases_list = "iijima_1.1", "iijima_1.2", "anbe_1.1"
$cases_list = "iijima_1.1", "iijima_1.2", "iwata_1.1","iwata_1.2"
$cases_list = "iijima_1.3", "iwata_1.1", "iwata_1.2", "nemoto_1.3"
$cases_list = "iijima_1.1","iijima_1.2", "iwata_1.1", "iwata_1.2", "nemoto_1.3"
$cases_list = "iijima_1.3", "anbe_1.3", "iwata_1.3", "nemoto_1.3"
$cases_list = "iijima_1.0", "anbe_1.0", "iwata_1.0", "nemoto_1.0"
$cases_list = "iijima_2.0", "anbe_2.0", "iwata_2.0", "nemoto_2.1", "sato_2.1"
$cases_list = "memoto_2.1", "sato_2.1", "yoshimoto_2m.0"
# 一括ケース設定例
#$cases_list = "iijima_1.3,anbe_1.3,iwata_1.3,nemoto_1.3"
$env:CASE_LIST=$cases_list
#
function help {
    # プロファイルの表示
    write-output $profile
    write-output '・このプロファイルでは、射形動画解析ツールの使用に必要な環境変数の設定と、ツールのコマンドを定義しています。'
    write-output '・次のコマンドを実行することで、ツールの使用ガイダンスが表示されます。'
    write-output '> help         : このヘルプを表示する'
    write-output '> yoloAp -help : 動画再生・解析ツールの使用ガイダンスを表示する'
    write-output '> chart  -help : 解析データ登録／データ表示ツールの使用ガイダンスを表示する'
    write-output '> kyudo  -help : 学習データ登録／学習・予測／データ表示ツールの使用ガイダンスを表示する'
    write-output '> model  -help : モデルのパラメータ表示／設定ツールの使用ガイダンスを表示する'
}
# 仮想環境アクティベート関数
function actv26env {
    .v26/Scripts/activate
    write-output '仮想環境:.v26がアクティブになりました。deactivateコマンドで仮想環境を終了できます。'
}
function home {
    set-location $HOME_DIR
    write-output 'ホームディレクトリに移動しました。'
}
# モデル設定関数
function model {
    param(
        [switch]$help,
        [string]$head='',
        [string]$case='',
        [string]$pt='',
        [string]$hp='',
        [string]$path='',
        [float]$l2=0.0,
        [int]$key=0
    )
    if ($help) {
        write-output '・コマンド -オプション'
        write-output ">model -head s|m                  ：モデルタイプ('s':シングルヘッド|'m':マルチヘッド)を設定する"
        write-output ">model -key <input_key>           ：データ入力キーを設定する"
        write-output ">model -pt <model_pt_file_path>   ：学習済モデルファイルを設定する"
        write-output ">model -l2 <L2_lambda>            ：L2正則化係数を設定する"
        write-output ">model -hp ({<para>, }...)        ：ハイパーパラメータ（シーケンス長、バッチサイズ、エポック数、学習率の減衰率、埋め込み次元数）を設定する"
        write-output ">model -case '{<case_name>,}...'  ：学習データリストを設定する（カンマ区切りで複数指定可。個別指定は’’不要）"
        write-output ">model -path '<picture-roll-path>'：動画ファイルの検索位置を設定する"
        write-output ">model		                  ：現在の環境変数（モデルタイプ、データ入力キー、GRUモデルファイル、L2正則化係数、ハイパーパラメータ、学習データリスト）を表示する"
        write-output ">actv26env	                  ：V26仮想環境をアクティベートする"
    }
    else {
        if ( $head -ne '' ) {
            if ( $head -eq 's' ) {
                $env:MODEL_TYPE="-models"
                $modelx = $env:MODEL_TYPE
                $str = '・モデルタイプがシングルヘッド(' + $modelx + ')に設定されました。'
                write-output $str
            }
            elseif ( $head -eq 'm' ) {
                $env:MODEL_TYPE="-modelm"
                $modelx = $env:MODEL_TYPE
                $str = '・モデルタイプがマルチヘッド(' + $modelx + ')に設定されました。'
                write-output $str
            }
            else {
                $str = '不正なモデルタイプが指定されました。：' + $head
                write-output $str
            }
        }
        elseif ( $case -ne '' ) {
            $env:CASE_LIST="$case"
            $cases_list = $env:CASE_LIST
            $str = '・学習データのリストが ' + $cases_list + ' に設定されました。'
            write-output $str
        }
        elseif ( $key -gt 0 ) {
            $env:INPUT_KEY="$key"
            $inputkey = $env:INPUT_KEY
            $str = '・入力データキーが ' + $inputkey + ' に設定されました。'
            write-output $str
        }
        elseif ( $pt -ne '' ) {
            $env:MODEL_PT="$pt"
            $modelpt = $env:MODEL_PT
            $str = '・学習済モデルが ' + $modelpt + ' に設定されました。'
            write-output $str
        }
        elseif ( $path -ne '' ) {
            $env:ROLL_PATH="$path"
            $str = '・動画ファイル検索位置が ' + $path + ' に設定されました。'
            write-output $str
        }
        elseif ( $hp -ne '' ) {
            $val_list = $hp.Split(' ')
            $i = 0
            foreach ( $val in $val_list ) {
                $hp_vals[$i] = $val
                $i++    
            }
            $hparam = $hp_vals -join ' '
            $env:HYPER_PARAM="$hparam"
            $str = '・ハイパーパラメータが ' + $hparam + ' に設定されました。'
            write-output $str
        }
        elseif ( $l2 -gt 0.0 ) {
            $env:L2_LAMBDA="$l2"
            $l2_lambda = $env:L2_LAMBDA
            $str = '・L2正則化係数が ' + $l2_lambda + ' に設定されました。'
            write-output $str
        }
        else{
            write-output '>>' 
            $str = '・モデルオプション    ：  ' + $env:MODEL_TYPE
            Write-Output $str
            $str = '・学習済モデル        ： ' + $env:MODEL_PT 
            write-output $str
            $str = '・ハイパーパラメータ  ： ' + $env:HYPER_PARAM
            write-output $str
            $str = '・入力データキー      ： ' + $env:INPUT_KEY
            write-output $str
            $str = '・L2正則化係数        ： ' + $env:L2_LAMBDA
            write-output $str
            $str = '・登録済ケースリスト  ： ' + $env:CASE_LIST 
            Write-Output $str
            $str = '・動画ファイル検索位置： ' + $env:ROLL_PATH 
            Write-Output $str
            $str = '・ホームディレクトリ  ： ' + $HOME_DIR
            Write-Output $str
            if ( $env:DB_PATH -ne '') {
                $str = '・データベース名      ： ' + $env:DB_PATH
                Write-Output $str
            }
        }
    }   
}
# 動画再生・解析ツール関数
function yoloAp {
    param(
        [switch]$help,
        [switch]$h,
        [switch]$update,
        [switch]$man,
        [switch]$raw,
        [switch]$clip,
        [string]$case,
        [string]$multi='',
        [string]$gru,
        [string]$v8='s',
        [string]$v26='',
        [string]$sample='1.7',
        [string]$mask=''
    )
    if ($v26 -eq '') {
        $param_id = '1.7-' + $v8
        $v = '-V8' + $v8
    }
    else {
        $param_id = '1.7-' + $v26
        $v = '-V26' + $v26
    }
    if ($man) {
        $no=2
        $slevel='-s2'
    }
    else {
        $no=0
        $slevel=''
    }
    $idx = $args.IndexOf("-level")
    $len = $args.Length
    if ( $idx -ge 0 -and  $len -gt ($idx + 1) ) {
        $no=-1
        if ( [int]::TryParse($args[$idx+1],[ref]$no) ){}
        if ( $no -lt 0 -or $no -gt 3 ) {
            $msg = '解析レベルには0～3の数値を指定してください: ' + $args[$idx+1]
            write-output $msg
            return
        }
        $slevel = '-s' + $no
    } 
    #write-output $gru
    #write-output $case
    if ($gru -eq '-level'){
        write-output 'GRUモデルファイル名を指定してください' 
        return
    }
    $mozic = '-z'
    if ( $mask -eq 'non' ) {
        $mozic = ''
    }
    #
    if ($help) {
        write-output '・コマンド -オプション'
        write-output '>yoloAp -update [-v8 {s|m}] -level <no>：姿勢解析パラメータを更新する（no:解析レベル {0|1|2|3}）'
        write-output '>yoloAp -raw		               ：選択した動画ファイルを生再生する（一時停止／巻戻し・スキップ／再生速度変更可）'
        write-output '>yoloAp -clip		               ：選択した動画ファイルを切り取り（平面的／時間的）、別ファイルに保存する（モザイク処理範囲の指定可）'
        write-output ">yoloAp -multi '<開始フレーム1>,<開始フレーム2>'           ：選択した動画ファイルを重ねて再生する（一時停止／巻戻し・スキップ／再生速度変更可）"
        write-output '>yoloAp -case <登録ケース名> [-level <no>]                 ：選択した動画の射形を解析しながら再生し,解析結果データ、画像をファイル出力する'
        write-output '>yoloAp -man [-level <no>] [-v{8|26} {s|m}]                ：選択した動画の射形をロジック解析しながら再生する（no:解析レベル {0|1|2|3}）'
        write-output '>yoloAp -gru {<GRUモデル>|-} [-level <no>] [-v{8|26} {s|m}]：選択した動画の射形を学習済GRUモデルで解析しながら再生する（解析レベル指定でHybrid解析）'
        write-output '>yoloAp -h               ：コマンドの詳細パラメータを表示する'
        write-output ''
        write-output '・動画再生中に、画面タップしてキー入力することで以下の処理ができます。'
        write-output ' 0 :解析開始'
        write-output ' 1-8:節の開始'
        write-output ' q :再生終了'
        write-output ' p :一時停止／再開'
        write-output ' r :繰り返し再生開始／停止（"-r"時のみ有効）'
        write-output ' z :矩形範囲のズーム表示'
        write-output ' w :ファイル出力開始／停止'
        write-output ' t :解析データ出力開始／停止'
        write-output ' s :スナップショットファイルの作成'
        write-output ' .(>):スキップ'
        write-output ' ,(<):巻き戻し'
        write-output ' k(K) :再生速度アップ'
        write-output ' l(L) :再生速度ダウン'
        write-output ' g :グリッド表示・非表示'
    } 
    elseif ($h) {           
        # 詳細ヘルプ表示
        python ./src/yoloApp.py -h
    } 
    elseif ($update) {      
        # 解析パラメータ更新
        python ./src/yoloApp.py -d1 -I $param_id $slevel
    }
    elseif ($man) {         
        # 動画再生・ロジック解析
        python ./src/yoloApp.py -d1 -a -m -w $v $slevel $mozic --
    }
    elseif ($raw) {         
        # 動画生再生
        python ./src/yoloApp.py -d1 -a  -r -w --
    }
    elseif ($multi -ne '') {         
        # マルチ動画再生
        python ./src/yoloApp.py -d1 -a -multi $multi --
    }
    elseif ($clip) {        
        # 動画切り取り
        python ./src/yoloApp.py -d1 -a -clip --
    }
    elseif ($case -ne '' -and $gru -eq '') {    
        # 動画再生・ロジック解析、結果保存
        if ($slevel -eq '-s0') {
            # レベルのデフォルトは2に設定
            $slevel='-s2'
        }
        python ./src/yoloApp.py -d1 -a -w -t  $case  $v $slevel -f"$sample" classes=3 $mozic --
    }
    elseif ($gru -ne '') {  
        # 動画再生・GRU解析
        if ($gru -eq '-') {
            # デフォルトモデル使用
            $modelpt = $env:MODEL_PT
            $model=$modelpt
        }
        else{
            # 指定モデル使用
            $model=$gru
        }
        if ( $case -ne '' ) {
            # 動画再生・GRU解析、結果保存
            python ./src/yoloApp.py -d1 -a -m -gru  $model $v $slevel -f"$sample" -t $case $mozic --
        }
        else{
            # 動画再生・GRU解析
            python ./src/yoloApp.py -d1 -a -m -gru  $model $v $slevel -f"$sample" -w $mozic --
        }
    }
    else{
        write-output '不正なパラメータが指定されました' 
    }
}
# YOLO解析レベル0関数
function yolo0 { 
	python ./src/yoloApp.py 0 
}
# 解析データ登録／データ表示ツール関数
function chart {
    param(
        [switch]$help,
        [switch]$h,
        [switch]$list_case,
        [switch]$list_key,
        [string]$import='',
        [string]$case,
        [string]$key=''
    )
    if ($help) {
        write-output '・コマンド -オプション'
        write-output '>chart  -list_case                    ：登録済ケース名の一覧を表示する'
        write-output '>chart  -list_key                     ：ポイントキー名の一覧を表示する'
        write-output '>chart  -import <登録ケース名>                 ：解析結果ポイントデータファイルのデータをデータベースに登録する'
        write-output ">chart  -case   <登録ケース名> -key '<キー名>{,<キー名>}...' ：解析結果ポイントデータをグラフ表示する"
        write-output '>chart  -h	  ：コマンドの詳細パラメータを表示する'
    } 
    elseif ($h) {
        # 詳細ヘルプ表示
        python ./src/chart.py -h
    } 
    elseif ($list_case) {
        # 登録済ケース名一覧表示
        python ./src/chart.py  -d -case -L
    } 
    elseif ($list_key) {
        # ポイントキー名一覧表示
        python ./src/chart.py  -d -key
    }
    elseif ($case -ne '') {
        # 解析結果ポイントデータをグラフ表示
        if ($key -ne '') {
            # 指定キーのデータをグラフ表示
            $key_list = $key.Split(',')
            $keys = @("","","","")
            $i = 0
            foreach ( $k in $key_list ) {
                if ( $i -ge 4 ) {
                    write-output '1、2、または4つのキーを指定してください' 
                    return
                }
                $keys[$i] = $k
                $i++
            }
            if ( $i -eq 1 ) {
                python ./src/chart.py -d  $keys[0] -case $case  -f0 0  -m 
            }
            elseif ( $i -eq 2-or $i -eq 4) {
                python ./src/chart.py -d  $keys[0] $keys[1] $keys[2] $keys[3] -case $case  -f0 0 
            }
            else {
                write-output '1、2、または4つのキーを指定してください' 
            }
        }
        else {
            # デフォルトキーのデータをグラフ表示
            python ./src/chart.py -d  right_wrist left_wrist right_elbow left_elbow -case $case  -f0 0      
        }
    }
    elseif ($import -ne '') {
        # 解析結果ポイントデータファイルのデータをデータベースに登録
        python ./src/chart.py  -d -case $import  -import
    }
    else{
        write-output '不正なパラメータが指定されました' 
    }	
}
# 学習データ登録／学習・予測／データ表示ツール関数
function kyudo {
    param(
        [switch]$help,
        [switch]$h,
        [string]$list='',
        [string]$delete,
        [string]$rename='',
        [string]$to='',
        [string]$import,
        [string]$case,
        [string]$train,
        [string]$valid='none',
        [switch]$section,
        [string]$predict,
        [int]$input_frames = 0,
        [string]$input_key = '',
        [float]$eta = 0.001
    )
    # ハイパーパラメータ取得
    $val_list = $env:HYPER_PARAM.Split(' ')
    $i = 0
    foreach ( $val in $val_list ) {
        $hp_vals[$i] = $val
        $i++    
    }
    $hparam = $hp_vals -join ','
    # 入力データキー設定
    if ( $input_key -eq '' ) {
        $input_key = $env:INPUT_KEY
    }
    # モデルタイプ取得
    $modelx = $env:MODEL_TYPE
    $model = "-model"
    if ($help) {
        write-output '・コマンド -オプション'
        write-output '>kyudo  -list	case|case_name|key|pt                ：登録済ケース名、入力データキー、または作成済モデルファイルの一覧を表示する'
        write-output '>kyudo  -deletet <登録ケース名>	                     ：登録ケース名、データファイルを削除する'
        write-output '>kyudo  -rename  <登録ケース名> -to <変更ケース名>   ：登録ケース名をリネームする'
        write-output '>kyudo  -import  <登録ケース名>                      ：解析結果データファイルのデータをデータベースに登録する'
        write-output '>kyudo  -case    <登録ケース名> [-input_key <番号>] [-input_frames <表示フレーム数>]         ：解析結果データをグラフ表示する'
        write-output '>kyudo  -train   <登録ケース名> [-valid <検証ケース名>] [-section] [-model <モデルファイル>] [-eta <学習率>]    ：解析結果データで学習する'
        write-output '>kyudo  -predict <登録ケース名> [-model <モデルファイル>]      	                            ：解析結果データで予測する'
        write-output '>kyudo  -h		：コマンドの詳細パラメータを表示する'
    } 
    elseif ($h) {
        # 詳細ヘルプ表示
        python ./src/kyudoApp.py -h
    } 
    elseif ($list -ne '') {
        if ( $list -eq 'key' ) {
            # 入力データキー一覧表示
            python ./src/kyudoApp.py  -d -inputkey
        }
        elseif ( $list -eq 'case' ) {
            # 登録済ケース名一覧表示（詳細）
            python ./src/kyudoApp.py  -d -case -L
        }
        elseif ( $list -eq 'case_name' ) {
            # 登録済ケース名一覧表示
            python ./src/kyudoApp.py  -d -case -l
        }
        elseif ( $list -eq 'pt' ) {
            # 作成済モデルファイル一覧表示
            get-childitem ./kyudo*.pt
        }
    } 
    elseif ($delete -ne '') {
        # 登録ケース名、データファイル削除
        python ./src/kyudoApp.py -d -case $delete -D
    }
    elseif ($rename -ne '' -and $to -ne '') {
        # 登録ケース名リネーム
        python ./src/kyudoApp.py -d -case $rename,$to -R
    }
    elseif ($import -ne '') {
        # 解析結果データファイルのデータをデータベースに登録
        python ./src/kyudoApp.py -d inputkey=$input_key -case $import -import
    }    
    elseif ($case -ne '') {
        # 解析結果データをグラフ表示
        python ./src/kyudoApp.py -d inputkey=$input_key -case $case -f0 $input_frames  -m 
    }
    elseif ($train -ne '') {
        # 学習実行
        $idx = $args.IndexOf($model)
        $len = $args.Length
        # 検証ケース名が指定さた場合は、-valid オプションで指定する
        $valid_case = $valid
        if (-not $section ) {
            if ($train -ne 'list') {
                # 単一ケース学習（登録ケース名指定）
                if ($idx -ge 0 -and $len -gt ($idx + 1) ) {
                    python ./src/kyudoApp.py -d -case $train -valid $valid_case classes=3 eta=$eta -hparam "($hparam)" -train $modelx $args[$idx+1] -f0 $input_frames     
                }
                else {
                    python ./src/kyudoApp.py -d -case $train -valid $valid_case  classes=3 eta=$eta -hparam "($hparam)" -train $modelx -f0 $input_frames   
                }
            }
            else {
                # 複数ケース学習（環境変数CASE_LIST指定）
                if ($idx -ge 0 -and $len -gt ($idx + 1) ) {
                    $cases_list = $env:CASE_LIST.Split(' ')
                    $str = '・学習データのリスト： (' + $cases_list.Length + 'ケース) ' + $cases_list
                    write-output $str
                    $i = 1
                    foreach ( $case_name in $cases_list ) {
                        python ./src/kyudoApp.py -d -case $case_name -valid $valid_case classes=3 eta=$eta -hparam "($hparam)" -train $modelx $args[$idx+1] -f0 $input_frames -n"$i" 
                        #Write-Output $LASTEXITCODE
                        if ( $LASTEXITCODE -ne 0 ) {
                            break
                        }
                        $i++    
                    }
                }
                else {
                    write-output 'モデルファイル名を指定してください' 
                }
            }
        }
        elseif ( $idx -ge 0 -and $len -gt ($idx + 1) ) {
            # セクション毎（0 -> 9）学習
            for( $i=0; $i -lt 10; $i++) {
                python ./src/kyudoApp.py -d -case $train  classes=3 eta=$eta -hparam "($hparam)" section=$i  -train $modelx $args[$idx+1] -f0 $input_frames -n 
            } 
        }
        else{
            write-output 'モデルファイル名を指定してください' 
        }
    }
    elseif ($predict -ne '') {
        # 予測実行
        $idx = $args.IndexOf($model)
        $len = $args.Length
        if ($idx -ge 0 -and $len -gt $idx) {
            $modelpt = $args[$idx+1]
        }
        python ./src/kyudoApp.py -d -case $predict -hparam "$hparam" -predict $modelx $modelpt -f0 $input_frames -m    
    }
    else{
        write-output '不正なパラメータが指定されました' 
    }	
}
# 仮想環境作成済の時は、プロファイル読み込み時に仮想環境をアクティベートする
if (Test-Path -Path .v26/Scripts/Activate.ps1) {
    actv26env
}
# コマンドエイリアス設定
#Set-Alias -Name help -Value help
# コマンドガイダンス表示
help
# モデル設定関数呼び出し（プロファイル読み込み時）
model
