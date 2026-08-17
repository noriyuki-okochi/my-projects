# Sqlite3データベースパス設定
$env:DB_PATH = './yolo-kyudo_local.db'
#$env:DB_PATH = './yolo-kyudo.db'
#
# 動画ファイル検索位置設定
$env:ROLL_PATH='E:/share/Pictures/Camera Roll/'
# ホームディレクトリ設定
$HOME_DIR = 'f:/share/YOLO'
#
# ホームディレクトリに移動
set-location $HOME_DIR
python -V
write-output 'Hellow YOLO!!'
$logfile = './log/console.log'
#
#
# 環境変数の設定
#
# データ入力キー設定
$env:INPUT_KEY="80"
$inputkey = $env:INPUT_KEY
$env:EVAL_INPUT_KEY="170"
$evalkey = $env:EVAL_INPUT_KEY
# モデルオプション設定
$env:MODEL_TYPE="-models"               # シングルヘッドをデフォルト
$env:EVAL_MODEL_TYPE="-modelc"          # 畳み込みモデルをデフォルト
$modelx = $env:MODEL_TYPE
# 学習済モデルファイル設定
$env:MODEL_PT="./kyudo2_80_modelse_8-96-3.pt"
$env:L2_LAMBDA="0.0"
$l2_lambda = $env:L2_LAMBDA
$env:EARLY_STOP="0"
# 重ね画像アルファ値設定
$env:ADD_WEIGHT="0.7"
#
# ハイパーパラメータ設定
$s = 96     # シーケンス長
$b = 32     # バッチサイズ
$e = 280    # エポック数
$r = 1.0    # 学習率の減衰率
$d_s = 8    # 埋め込み次元数(section)
$d_c = 4    # 埋め込み次元数(completed)
#
#$s = 128    # シーケンス長
#$b = 256    # バッチサイズ
#$e = 161    # エポック数
#$d_c = 6    # 埋め込み次元数(completed)
#
# Evalモデルのハイパーパラメータ設定
#$s = 48     # シーケンス長
#$b = 8      # バッチサイズ
#$e = 280    # エポック数
$env:HYPER_PARAM=($s,$b,$e,$r,$d_s,$d_c)
$hp_vals = @($s,$b,$e,$r,$d_s,$d_c)
$hparam = $hp_vals[0],$hp_vals[1],$hp_vals[2],$hp_vals[3],$hp_vals[4],$hp_vals[5]
#
# データ拡張（オーギュメント）パラメータ設定
$t_s = 3     # eval:縦軸シフト(下方向3フレーム以内)
$t_s = 3     # kyudo:ラベルシフト(前後3フレーム以内)
$t_w = 0.1   # eval:縦軸伸縮（0.1=10%）未使用
$t_w = 5.0   # kyudo:ラベル伸張(前後5フレーム)
$n = 0.02    # ノイズ（0.02=2%）
$env:AUGMENT_PARAM=($t_s,$t_w,$n)
$dp_vals = @($t_s,$t_w,$n)
$dparam = $dp_vals[0],$dp_vals[1],$dp_vals[2]
#
# 登録ケース名リスト
#
# 個別ケース設定例
$cases_list = "iijima_1.1", "iijima_1.2", "anbe_1.1"
$cases_list = "iijima_1.1", "iijima_1.2", "anbe_1.1", "anbe_1.2"
$cases_list = "iijima_1.1", "iijima_1.2", "iwata_1.1", "iwata_1.2"
$cases_list = "iijima_1.1", "iijima_1.2", "iwata_1.1", "iwata_1.2", "nemoto_1.3"
$cases_list = "iijima_2.0", "anbe_2.0", "iwata_2.0", "nemoto_2.1", "sato_2.1"
$cases_list = "nemoto_2.2", "sato_2.2", "yoshimo_2m.2"
# 一括ケース設定例
$cases_list = "iijima_2.0_1,anbe_2.0_1,iwata_2.0_1,y.shihan_2.0_1,yoshida_2.0_1,oshima_2.0_1,n.iijima_2.0_1,sato_2.1_1,nemoto_2.1_1,kanoda_2.3_1,sueyoshi_2.3_1,h.nakamura_2.0_1"
$env:CASE_LIST=$cases_list

# データ拡張レベル設定例（個別ケース毎に指定：0=拡張なし,1=shift,2=warp,4=noize）
#$augment_list = '0,1,2,3,4,5,6,7'
$augment_list = ''
$env:AUGMENT_LIST=$augment_list
#
$dbg_level = '-d1'
$dbg_option = '-d'
#
function help {
    # プロファイルの表示
    write-output $profile
    write-output '・このプロファイルでは、射形動画解析ツールの使用に必要な環境変数の設定と、ツールのコマンドを定義しています。'
    write-output '・次のコマンドを実行することで、ツールの使用ガイダンスが表示されます。'
    write-output '> help         : このヘルプを表示する'
    write-output '> yoloAp -help : 動画再生・解析ツールの使用ガイダンスを表示する'
    write-output '> chart  -help : 解析データ登録／データ表示ツールの使用ガイダンスを表示する'
    write-output '> kyudo  -help : 姿勢解析データの登録／学習・予測／データ表示ツールの使用ガイダンスを表示する'
    write-output '> eval   -help : 射形評価データの学習・予測／データ表示ツールの使用ガイダンスを表示する'
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
        [string]$gru='',
        [string]$eval='',
        [string]$case='',
        [string]$pt='',
        [string]$hp='',
        [string]$dp='',
        [string]$roll='',
        [string]$augment='',
        [float]$l2=0.0,
        [int]$key=0,
        [int]$evalkey=0,
        [float]$alpha=1.0,
        [int]$stop=-1
    )
    if ($help) {
        write-output '・コマンド -オプション'
        write-output ">model -gru s|m                   ：GRUモデルタイプ('s':シングルヘッド|'m':マルチヘッド)を設定する"
        write-output ">model -key <input_key>           ：データ入力キーを設定する"
        write-output ">model -eval n|c                  ：評価モデルタイプ('n':全結合|'c':畳み込み)を設定する"
        write-output ">model -evalkey <input_key>       ：評価データ入力キーを設定する"
        write-output ">model -pt <model_pt_file_path>   ：学習済モデルファイルを設定する"
        write-output ">model -l2 <L2_lambda>            ：L2正則化係数を設定する"
        write-output ">model -hp ({<para>, }...)        ：ハイパーパラメータ（シーケンス長、バッチサイズ、エポック数、学習率の減衰率、埋め込み次元数）を設定する"
        write-output ">model -dp ({<para>, }...)        ：データ拡張パラメータ（シフト最大長、伸縮率、最大ノイズ率）を設定する"
        write-output ">model -case '{<case_name>,}...'  ：学習データリストを設定する（カンマ区切りで複数指定可。個別指定は’’不要）"
        write-output ">model -augment '{<level>,}...'   ：データ拡張レベルを設定する（level={0|1|2|3|4|5}をカンマ区切りでケースの個別指定単位に指定）"
        write-output ">model -roll *|'<roll-path>'      ：動画ファイルの検索位置を設定する（'*'指定時は、ダイアログで選択）"
        write-output ">model -alpha '<add-weight-alpha>'：重ね画像アルファ値を設定する"
        write-output ">model -stop '<early-stop>'       ：エポックを早期終了する条件（最小Loss値未更新回数）を設定する"
        write-output ">model		                  ：現在の環境変数を表示する"
        write-output ">actv26env	                  ：V26仮想環境をアクティベートする"
    }
    else {
        if ( $gru -ne '' ) {
            if ( $gru -eq 's' ) {
                $env:MODEL_TYPE="-models"
                $modelx = $env:MODEL_TYPE
                $str = '・モデルタイプがシングルヘッド(' + $modelx + ')に設定されました。'
                write-output $str
            }
            elseif ( $gru -eq 'm' ) {
                $env:MODEL_TYPE="-modelm"
                $modelx = $env:MODEL_TYPE
                $str = '・モデルタイプがマルチヘッド(' + $modelx + ')に設定されました。'
                write-output $str
            }
            else {
                $str = '不正なモデルタイプが指定されました。：' + $gru
                write-output $str
            }
        }
        elseif ( $eval -ne '' ) {
            if ( $eval -eq 'n' ) {
                $env:EVAL_MODEL_TYPE="-modeln"
                $modelx = $env:EVAL_MODEL_TYPE
                $str = '・評価モデルタイプが全結合(' + $modelx + ')に設定されました。'
                write-output $str
            }
            elseif ( $eval -eq 'c' ) {
                $env:EVAL_MODEL_TYPE="-modelc"
                $modelx = $env:EVAL_MODEL_TYPE
                $str = '・評価モデルタイプが畳み込み(' + $modelx + ')に設定されました。'
                write-output $str
            }
            else {
                $str = '不正な評価モデルタイプが指定されました。：' + $eval
                write-output $str
            }
        }
        elseif ( $case -ne '' ) {
            $env:CASE_LIST="$case"
            $cases_list = $env:CASE_LIST
            $str = '・学習データのリストが ' + $cases_list + ' に設定されました。'
            write-output $str
        }
        elseif ( $augment -ne '' ) {
            $env:AUGMENT_LIST="$augment"
            $augment_levels = $env:AUGMENT_LIST
            $str = '・データ拡張レベルが ' + $augment_levels + ' に設定されました。'
            write-output $str
        }
        elseif ( $key -gt 0 ) {
            $env:INPUT_KEY="$key"
            $inputkey = $env:INPUT_KEY
            $str = '・入力データキーが ' + $inputkey + ' に設定されました。'
            write-output $str
        }
        elseif ( $evalkey -gt 0 ) {
            $env:EVAL_INPUT_KEY="$evalkey"
            $evalkey = $env:EVAL_INPUT_KEY
            $str = '・評価データキーが ' + $evalkey + ' に設定されました。'
            write-output $str
        }
        elseif ( $pt -ne '' ) {
            $env:MODEL_PT="$pt"
            $modelpt = $env:MODEL_PT
            $str = '・学習済モデルが ' + $modelpt + ' に設定されました。'
            write-output $str
        }
        elseif ( $roll -ne '' ) {
            if ( $roll -eq '*' ) {
                Add-Type -AssemblyName System.Windows.Forms
                $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
                $dialog.RootFolder = 'Desktop'
                $dialog.Description = 'デフォルトの動画フォルダを選択してください'
                # フォルダ選択の有無を判定
                if($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){
                    $roll_path_new = $dialog.SelectedPath
                    Write-Host  ">>'$roll_path_new' selected:"
                    $env:ROLL_PATH="$roll_path_new"
                    $str = '・動画ファイル検索位置が ' + $roll_path_new + ' に設定されました。'
                    write-output $str
                }
                else {
                    Write-Host  ">>canceled."
                }
            }
            else {
                $ans = & Test-Path -Path $roll 2>&1
                if ( $ans ) {
                    $env:ROLL_PATH="$roll"
                    $str = '・動画ファイル検索位置が ' + $roll + ' に設定されました。'
                    write-output $str
                }
                else {
                    Write-Host  "・'$roll' does not exist."
                } 
            }
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
        elseif ( $dp -ne '' ) {
            $val_list = $dp.Split(' ')
            $i = 0
            foreach ( $val in $val_list ) {
                $dp_vals[$i] = $val
                $i++    
            }
            $dparam = $dp_vals -join ' '
            $env:AUGMENT_PARAM="$dparam"
            $str = '・データ拡張パラメータが ' + $dparam + ' に設定されました。'
            write-output $str
        }
        elseif ( $l2 -gt 0.0 ) {
            $env:L2_LAMBDA="$l2"
            $l2_lambda = $env:L2_LAMBDA
            $str = '・L2正則化係数が ' + $l2_lambda + ' に設定されました。'
            write-output $str
        }
        elseif ( $alpha -lt 1.0 ) {
            $env:ADD_WEIGHT="$alpha"
            $add_alpha = $env:ADD_WEIGHT
            $str = '・重ね画像アルファ値が ' + $add_alpha + ' に設定されました。'
            write-output $str
        }
        elseif ( $stop -ge 0 ) {
            $env:EARLY_STOP="$stop"
            $early_stop = $env:EARLY_STOP
            $str = '・早期停止回数が ' + $early_stop + ' に設定されました。'
            write-output $str
        }
        else{
            write-output '>>' 
            $str = '・GRUモデルタイプ     ：  ' + $env:MODEL_TYPE
            Write-Output $str
            $str = '・入力データキー      ： ' + $env:INPUT_KEY
            write-output $str
            $str = '・評価モデルタイプ    ：  ' + $env:EVAL_MODEL_TYPE
            Write-Output $str
            $str = '・評価入力データキー  ： ' + $env:EVAL_INPUT_KEY
            write-output $str
            $str = '・学習済モデル        ： ' + $env:MODEL_PT 
            write-output $str
            $str = '・ハイパーパラメータ  ： ' + $env:HYPER_PARAM
            write-output $str
            $str = '・データ拡張パラメータ： ' + $env:AUGMENT_PARAM
            write-output $str
            $str = '・早期停止回数        ： ' + $env:EARLY_STOP
            write-output $str
            $str = '・L2正則化係数        ： ' + $env:L2_LAMBDA 
            write-output $str
            $str = '・重ね画像アルファ値  ： ' + $env:ADD_WEIGHT
            write-output $str
            $str = '・動画ファイル検索位置： ' + $env:ROLL_PATH 
            Write-Output $str
            $str = '・ホームディレクトリ  ： ' + $HOME_DIR
            Write-Output $str
            if ( $env:DB_PATH -ne '') {
                $str = '・データベース名      ： ' + $env:DB_PATH
                Write-Output $str
            }
            $str = '・登録済ケースリスト  ： ' + $env:CASE_LIST 
            Write-Output $str
            $str = '・データ拡張リスト    ： ' + $env:AUGMENT_LIST 
            Write-Output $str
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
        [float]$fps=1.0,
        [switch]$yolo,
        [int]$kpt=3,
        [switch]$clip,
        [switch]$rotate,
        [string]$case,
        [string]$multi='',
        [string]$one='',
        [string]$comp='',
        [string]$at='1,1',
        [string]$gru,
        [string]$v8='s',
        [string]$v26='',
        [string]$sample='1.7',
        [switch]$mask
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
    $evalon = ''
    $eval_model = ''
    $idx = $args.IndexOf("-eval")
    if ( $idx -ge 0 ) {
        $evalon = '-eval'
        if ( $args.Length -gt ($idx + 1) ) {
            $eval_model = $args[$idx + 1]
            $evalon = '-eval'
        }
    }
    $maskon = ''
    if ( $mask ) {
        $maskon = '-z'
    }
    if ($rotate) {
        write-output '・動画を時計回りに90度回転して表示します'
    }
    #
    if ($help) {
        write-output '・コマンド -オプション'
        write-output '>yoloAp -update [-v8 {s|m}] -level <no>                    ：姿勢解析パラメータを更新する（no:解析レベル {0|1|2|3}）'
        write-output '>yoloAp -raw	[-at <開始フレーム>] [-fps <FPS-ratio>]    ：選択した動画ファイルを生再生する（一時停止／巻戻し・スキップ／再生速度変更可）'
        write-output '>yoloAp -clip	[-rotate]	        ：選択した動画ファイルを切り取り（平面的／時間的）、別ファイルに保存する（モザイク処理範囲の指定可）'
        write-output '>yoloAp -yolo	[-at <開始フレーム>] [-kpt <draw-kpt-no]   ：選択した動画ファイルを骨格解析して再生する'
        write-output ">yoloAp -multi '<開始フレーム1>,<開始フレーム2>'           ：選択した動画ファイルを重ねて再生する（一時停止／巻戻し・スキップ／再生速度変更可）"
        write-output '>yoloAp -man [-level <no>] [-v{8|26} {s|m}] [-mask] [-eval]：選択した動画の射形をロジック解析しながら再生する（no:解析レベル {0|1|2|3}）'
        write-output '>yoloAp -case <登録ケース名> [-level <no>]                 ：選択した動画の射形を解析しながら再生し,解析結果データ、画像をファイル出力する'
        write-output '>yoloAp -gru {<GRUモデル>|-} [-level <no>] [-v{8|26} {s|m}]：選択した動画の射形を学習済GRUモデルで解析しながら再生する（解析レベル指定でHybrid解析）'
        write-output ">yoloAp -one <登録ケース名> [-at <開始フレーム>]           ：指定したケースの動画ファイルを生再生する"
        write-output ">yoloAp -comp '<登録ケース名1>[,登録ケース名2>]' -at '<開始フレーム1>[,<開始フレーム2>]'：指定したケースの動画ファイルを重ねて再生する"
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
        python ./src/yoloApp.py $dbg_level -I $param_id $slevel
    }
    elseif ($man) {         
        # 動画再生・ロジック解析
        python ./src/yoloApp.py $dbg_level -a -m -w $v $slevel $maskon $evalon $eval_model --
    }
    elseif ($raw) {         
        # 動画生再生
        $l = $at.split(',')
        if( $l.Length -gt 1 ){
            # 未指定（デフォルト）時、1を再設定
            $at = '1'
        }
        $clockwise = ''
        if ($rotate) {
            $clockwise = '-rotate'
        }
        python ./src/yoloApp.py $dbg_level -a  -r $clockwise -w $fps -at $at --
    }
    elseif ($yolo) {         
        # 動画姿勢解析再生
        $l = $at.split(',')
        if( $l.Length -gt 1 ){
            # 未指定（デフォルト）時、1を再設定
            $at = '1'
        }
        python ./src/yoloApp.py $dbg_level -a $v -kpt $kpt -w -at $at --
    }
    elseif ($multi -ne '') {         
        # マルチ指定動画再生
        python ./src/yoloApp.py $dbg_level -a -multi $multi --
    }
    elseif ($one -ne '') {         
        # 単一ケース指定再生
        $l = $at.split(',')
        if( $l.Length -gt 1 ){
            # 未指定（デフォルト）時、1を再設定
            $at = '1'
        }
        python ./src/yoloApp.py $dbg_level -o  $one -at $at -r --
    }
    elseif ($comp -ne '') {         
        $case_list = $comp.Split(',')
        $i = $case_list.Length
        if ( $i -eq 1 ) {
            # 単一ケース動画再生（指定ケースの動画ファイルを再生）
            python ./src/yoloApp.py $dbg_level -o $comp -at $at -m --
        }
        else{
            # マルチ動画再生（指定ケースの動画ファイルを重ねて再生）
            python ./src/yoloApp.py $dbg_level -o $comp -multi $at -r --
        }
    }
    elseif ($clip) {        
        # 動画切り取り
        $clockwise = ''
        if ($rotate) {
            $clockwise = '-rotate'
        }
        python ./src/yoloApp.py $dbg_level -a -clip $clockwise --
    }
    elseif ($case -ne '' -and $gru -eq '') {    
        # 動画再生・ロジック解析、結果保存
        if ($slevel -eq '-s0') {
            # レベルのデフォルトは2に設定
            $slevel='-s2'
        }
        python ./src/yoloApp.py $dbg_level -a -w -t  $case  $v $slevel -f"$sample" classes=3 $maskon $evalon $eval_model --
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
            python ./src/yoloApp.py $dbg_level -a -m -gru  $model $v $slevel -f"$sample" -w -t $case $maskon $evalon $eval_model --
        }
        else{
            # 動画再生・GRU解析
            python ./src/yoloApp.py $dbg_level -a -m -gru  $model $v $slevel -f"$sample" -w $maskon $evalon $eval_model --
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
        [string]$list='',
        [string]$import='',
        [string]$case,
        [string]$key='',
        [string]$tb=''
    )
    if ($help) {
        write-output '・コマンド -オプション'
        write-output '>chart  -list case|point|tb                   ：登録済ケース名、ポイントキー名、Tensor boardフォルダ一覧を表示する'
        write-output ">chart  -tb   <Tensor board名>                ：指定されたTensor boardファルダのデータを表示する"
        write-output '>chart  -import <登録ケース名>                 ：解析結果ポイントデータファイルのデータをデータベースに登録する'
        write-output ">chart  -case   <登録ケース名> -key '<キー名>{,<キー名>}...' ：解析結果ポイントデータをグラフ表示する"
        write-output '>chart  -h	  ：コマンドの詳細パラメータを表示する'
    } 
    elseif ($h) {
        # 詳細ヘルプ表示
        python ./src/chart.py -h
    } 
    elseif ($list -ne '') {
        if ($list -eq 'case') {
            # 登録済ケース名一覧表示
            python ./src/chart.py  $dbg_option -case -L
        } 
        elseif ($list -eq 'point') {
            # ポイントキー名一覧表示
            python ./src/chart.py  $dbg_option -key
        }
        elseif ($list -eq 'tb') {
            # Tensor board一覧表示
            get-childitem ./*_tb
        }
    } 
    elseif ($tb -ne '') {
        # 指定されたTensor boardのデータを表示
        tensorboard --logdir $tb
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
                python ./src/chart.py $dbg_option  $keys[0] -case $case  -f0 0  -m 
            }
            elseif ( $i -eq 2-or $i -eq 4) {
                python ./src/chart.py $dbg_option  $keys[0] $keys[1] $keys[2] $keys[3] -case $case  -f0 0 
            }
            else {
                write-output '1、2、または4つのキーを指定してください' 
            }
        }
        else {
            # デフォルトキーのデータをグラフ表示
            python ./src/chart.py $dbg_option  right_wrist left_wrist right_elbow left_elbow -case $case  -f0 0      
        }
    }
    elseif ($import -ne '') {
        # 解析結果ポイントデータファイルのデータをデータベースに登録
        python ./src/chart.py  $dbg_option -case $import  -import -m -f0 0 right_wrist -second box_h
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
        [string]$update='',
        [string]$memo='',
        [string]$import,
        [string]$case,
        [string]$train,
        [string]$valid='none',
        [switch]$section,
        [int]$augment=-1,
        [string]$predict,
        [int]$input_frames = 0,
        [string]$input_key = '',
        [float]$eta = 0.001,
        [string]$eval=''
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
        write-output '>kyudo  -list	case|case_name|key|pt                     ：登録済ケース名、入力データキー、または作成済モデルファイルの一覧を表示する'
        write-output '>kyudo  -deletet <登録ケース名>	                          ：登録ケース名、データファイルを削除する'
        write-output '>kyudo  -rename  <登録ケース名> -to <変更ケース名>        ：登録ケース名をリネームする'
        write-output '>kyudo  -import  <登録ケース名>                           ：解析結果データファイルのデータをデータベースに登録する'
        write-output ">kyudo  -update  <登録ケース名> -memo '<メモ>'            ：登録ケース名のメモを更新する"
        write-output ">kyudo  -eval    '*'|'<登録ケース名>{,<登録ケース名>}'... ：評価データを表示する"
        write-output '>kyudo  -case    <登録ケース名> [-input_key <番号>] [-input_frames <表示フレーム数>]         ：解析結果データをグラフ表示する'
        write-output '>kyudo  -train   <登録ケース名>|list [-valid <検証ケース名>] [-section] [-augment <レベル>] [-model <モデルファイル>] [-eta <学習率>]'  
        write-output '-                                                                                            ：解析結果データで学習する'
        write-output '>kyudo  -predict <登録ケース名> [-model <モデルファイル>]      	                             ：解析結果データで予測する'
        write-output '>kyudo  -h		：コマンドの詳細パラメータを表示する'
    } 
    elseif ($h) {
        # 詳細ヘルプ表示
        python ./src/kyudoApp.py -h
    } 
    elseif ($list -ne '') {
        if ( $list -eq 'key' ) {
            # 入力データキー一覧表示
            python ./src/kyudoApp.py  $dbg_option -inputkey
        }
        elseif ( $list -eq 'case' ) {
            # 登録済ケース名一覧表示（詳細）
            python ./src/kyudoApp.py  $dbg_option -case -L
        }
        elseif ( $list -eq 'case_name' ) {
            # 登録済ケース名一覧表示
            python ./src/kyudoApp.py  $dbg_option -case -l
        }
        elseif ( $list -eq 'pt' ) {
            # 作成済モデルファイル一覧表示
            get-childitem ./kyudo*.pt
        }
    } 
    elseif ($delete -ne '') {
        # 登録ケース名、データファイル削除
        python ./src/kyudoApp.py $dbg_option -case $delete -D
    }
    elseif ($rename -ne '' -and $to -ne '') {
        # 登録ケース名リネーム
        python ./src/kyudoApp.py $dbg_option -case $rename,$to -R
    }
    elseif ($update -ne '') {
        if ($memo -ne '') {
            # 登録ケースのメモ更新
            python ./src/kyudoApp.py $dbg_option -case $update -U $memo
        }
    }
    elseif ($import -ne '') {
        # 解析結果データファイルのデータをデータベースに登録
        python ./src/kyudoApp.py $dbg_option inputkey=$input_key -case $import -import -m -f0 0
    }
    elseif ($eval -ne '') {
        # 評価データ表示
        python ./src/kyudoApp.py $dbg_option  -case $eval -eval | Tee-Object $logfile
    }    
    elseif ($case -ne '') {
        # 解析結果データをグラフ表示
        python ./src/kyudoApp.py $dbg_option inputkey=$input_key -case $case -f0 $input_frames  -m 
    }
    elseif ($train -ne '') {
        # 学習実行
        $idx = $args.IndexOf($model)
        $len = $args.Length
        # 検証ケース名が指定さた場合は、-valid オプションで指定する
        $valid_case = $valid
        $aug_level = $augment
        if (-not $section ) {
            if ($train -ne 'list') {
                # 単一ケース学習（登録ケース名指定）
                if ($aug_level -lt 0) {
                    # デフォルトは0に再設定
                    $aug_level = 0
                }
                if ($idx -ge 0 -and $len -gt ($idx + 1) ) {
                    python ./src/kyudoApp.py $dbg_option -case $train -valid $valid_case classes=3 augment=$aug_level eta=$eta -hparam "($hparam)" -train $modelx $args[$idx+1] -f0 $input_frames     
                }
                else {
                    python ./src/kyudoApp.py $dbg_option -case $train -valid $valid_case  classes=3 augment=$aug_level eta=$eta -hparam "($hparam)" -train $modelx -f0 $input_frames   
                }
            }
            else {
                # 複数ケース学習（環境変数CASE_LIST指定）
                $cases_list = $env:CASE_LIST.Split(' ')
                $str = '・学習データのリスト： (' + $cases_list.Length + 'ケース) ' + $cases_list
                write-output $str
                $aug_levels = @()
                if ($aug_level -lt 0 ) {
                    # オプションで指定されなかった場合、環境変数AUGMENT_LISTを参照する
                    if ($null -ne $env:AUGMENT_LIST) {
                        # ケース毎のデータ拡張レベルを配列に格納する
                        $aug_levels = $env:AUGMENT_LIST.Split(',')
                        $str = '・データ拡張のリスト： (' + $aug_levels.Length + 'ケース) ' + $aug_levels
                        write-output $str
                    }
                    else {
                        # 環境変数に未設定の時はデフォルトに再設定
                        $aug_level = 0
                    }
                }
                $i = 1
                foreach ( $case_name in $cases_list ) {
                    if ($aug_levels.Length -gt 0) {
                        # ケース毎のデータ拡張レベルを参照する
                        if ( $i -le $aug_levels.Length ) {
                            $aug_level = $aug_levels[$i-1]
                        }
                        else {
                            # デフォルトに再設定
                            $aug_level = 0
                        }
                    }
                    if ( $idx -ge 0 -and $len -gt ($idx + 1) ) {
                        python ./src/kyudoApp.py $dbg_option -case $case_name -valid $valid_case classes=3 augment=$aug_level eta=$eta -hparam "($hparam)" -train $modelx $args[$idx+1] -f0 $input_frames -n"$i" 
                    }
                    else {
                        python ./src/kyudoApp.py $dbg_option -case $case_name -valid $valid_case classes=3 augment=$aug_level eta=$eta -hparam "($hparam)" -train $modelx -f0 $input_frames -n"$i" 
                    }
                    #Write-Output $LASTEXITCODE
                    if ( $LASTEXITCODE -ne 0 ) {
                        break
                    }
                    $i++    
                }
            }
        }
        elseif ( $idx -ge 0 -and $len -gt ($idx + 1) ) {
            # セクション毎（0 -> 9）学習
            if ($aug_level -lt 0) {
                # デフォルトは0に再設定
                $aug_level = 0
            }
            for( $i=0; $i -lt 10; $i++) {
                python ./src/kyudoApp.py $dbg_option -case $train  classes=3 augment=$aug_level eta=$eta -hparam "($hparam)" section=$i  -train $modelx $args[$idx+1] -f0 $input_frames -n 
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
        $aug_level = $augment
        if ($aug_level -lt 0) {
            # デフォルトは0に再設定
            $aug_level = 0
        }
        python ./src/kyudoApp.py $dbg_option -case $predict augment=$aug_level -hparam "($hparam)" -predict $modelx $modelpt -f0 $input_frames -m    
    }
    else{
        write-output '不正なパラメータが指定されました' 
    }	
}
# 学習データ登録／学習・予測／データ表示ツール関数
function eval {
    param(
        [switch]$help,
        [switch]$h,
        [string]$list='',
        [string]$update='',
        [string]$score='',
        [string]$case,
        [switch]$img,
        [string]$train,
        [string]$valid='none',
        [int]$augment=-1,
        [string]$predict,
        [int]$input_frames = 0,
        [float]$eta = 0.001,
        [string]$print=''
    )    
    # ハイパーパラメータ取得
    $val_list = $env:HYPER_PARAM.Split(' ')
    $i = 0
    foreach ( $val in $val_list ) {
        $hp_vals[$i] = $val
        $i++    
    }
    $hparam = $hp_vals -join ','

    $aug_level = $augment

    # モデルタイプ取得
    $modelx = $env:EVAL_MODEL_TYPE
    $model = "-model"
    if ($help) {
        write-output '・コマンド -オプション'
        write-output '>eval  -list    key|pt                                                ：入力データキー,または作成済モデルファイルの一覧を表示する'
        write-output ">eval  -update  <登録ケース名> -score '<スコア>'                      ：登録ケース名の評価データのスコア（1～8節をカンマ区切り）を更新する"
        write-output ">eval  -print   '*'|'<登録ケース名>{,<登録ケース名>}'...                                  ：評価データを表示する"
        write-output '>eval  -case    <登録ケース名> [-img [-augment <レベル>]] [-input_frames <表示フレーム数>] ：評価データをグラフ表示する'
        write-output '>eval  -train   <登録ケース名>|list [-valid <検証ケース名>] [-augment <レベル>] [-model <モデルファイル>] [-eta <学習率>]'
        write-output '-                                                                                         ：解析結果データで学習する'
        write-output '>eval  -predict <登録ケース名> [-model <モデルファイル>]                                  ：解析結果データで予測する'
        write-output '>eval  -h	：コマンドの詳細パラメータを表示する'
    } 
    elseif ($h) {
        # 詳細ヘルプ表示
        python ./src/evalApp.py -h
    } 
    elseif ($list -ne '') {
        if ( $list -eq 'pt' ) {
            # 作成済モデルファイル一覧表示
            get-childitem ./eval*.pt
        }
        elseif ( $list -eq 'key' ) {
            # 入力データキー一覧表示
            python ./src/evalApp.py $dbg_option -inputkey
        }
    } 
    elseif ($update -ne '') {
        if ($score -ne '') {
            # 登録ケースのラベル更新
            python ./src/evalApp.py $dbg_option -case $update -E $score
        }
    }
    elseif ($print -ne '') {
        # 評価データ表示
        python ./src/evalApp.py $dbg_option  -case $print -eval | Tee-Object $logfile
    }    
    elseif ($case -ne '') {
        if ($img) {
            if ($aug_level -lt 0) {
                # デフォルトは0に再設定
                $aug_level = 0
            }
             # 解析結果画像を表示
            python ./src/evalApp.py $dbg_option  -case $case -img -hparam "($hparam)"  augment=$aug_level 
        }
        else {
            # 解析結果データをグラフ表示
            python ./src/evalApp.py $dbg_option  -case $case -f0 $input_frames  -m
            #python ./src/evalApp.py -d inputkey=$input_key -case $case -f0 $input_frames  -m
        } 
    }
    elseif ($train -ne '') {
        # 学習実行
        $idx = $args.IndexOf($model)
        $len = $args.Length
        # 検証ケース名が指定さた場合は、-valid オプションで指定する
        $valid_case = $valid
        if ($train -ne 'list') {
        # 単一ケース学習（登録ケース名指定）
            if ($aug_level -lt 0) {
                # デフォルトは0に再設定
                $aug_level = 0
            }
            if ($idx -ge 0 -and $len -gt ($idx + 1) ) {
                python ./src/evalApp.py $dbg_option -case $train -valid $valid_case classes=3 eta=$eta -hparam "($hparam)" augment=$aug_level -train $modelx $args[$idx+1] -f0 $input_frames     
            }
            else {
                python ./src/evalApp.py $dbg_option -case $train -valid $valid_case  classes=3 eta=$eta -hparam "($hparam)" augment=$aug_level -train $modelx -f0 $input_frames   
            }
        }
        else {
            # 複数ケース学習（環境変数CASE_LIST指定）
            $cases_list = $env:CASE_LIST.Split(' ')
            $str = '・学習データのリスト： (' + $cases_list.Length + 'ケース) ' + $cases_list
            write-output $str
            $aug_levels = @()
            if ($aug_level -lt 0) {
                if ($null -ne $env:AUGMENT_LIST) {
                    $aug_levels = $env:AUGMENT_LIST.Split(',')
                    $str = '・データ拡張のリスト： (' + $aug_levels.Length + 'ケース) ' + $aug_levels
                    write-output $str
                }
                else {
                    # デフォルトは0に再設定
                    $aug_level = 0
                }
            }
            $i = 1
            foreach ( $case_name in $cases_list ) {
                if ($aug_levels.Length -gt 0) {
                    if ( $i -le $aug_levels.Length ) {
                        $aug_level = $aug_levels[$i-1]
                    }
                    else {
                        $aug_level = 0
                    }
                }
                if ( $idx -ge 0 -and $len -gt ($idx + 1) ) {
                    python ./src/evalApp.py $dbg_option -case $case_name -valid $valid_case classes=3 eta=$eta -hparam "($hparam)" augment=$aug_level -train $modelx $args[$idx+1] -f0 $input_frames -n"$i" 
                }
                else {
                    python ./src/evalApp.py $dbg_option -case $case_name -valid $valid_case classes=3 eta=$eta -hparam "($hparam)" augment=$aug_level -train $modelx -f0 $input_frames -n"$i" 
                }
                #Write-Output $LASTEXITCODE
                if ( $LASTEXITCODE -ne 0 ) {
                    break
                }
                $i++    
            }
        }
    }
    elseif ($predict -ne '') {
        # 予測実行
        $idx = $args.IndexOf($model)
        $len = $args.Length
        if ($idx -ge 0 -and $len -gt $idx) {
            $modelpt = $args[$idx+1]
        }
        python ./src/evalApp.py $dbg_option -case $predict -hparam "($hparam)" -predict $modelx $modelpt -f0 $input_frames -m    
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
