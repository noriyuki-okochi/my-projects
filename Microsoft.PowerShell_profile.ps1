f:
set-location share/YOLO
# プロファイルの表示
write-output $profile
#
write-output 'Hellow YOLO!!'
write-output '・次のコマンドを実行することで、射形動画解析ツールの使用ガイダンスが表示されます。'
write-output '> yolo   -help		：動画再生・解析ツール'
write-output '> chart  -help		：解析データ登録／データ表示ツール'
write-output '> kyudo  -help		：学習データ登録／学習・予測／データ表示ツール'
# 環境変数の設定
$env:INPUT_KEY="80"
$inputkey = $env:INPUT_KEY
# モデルオプション設定
# マルチヘッドモデル設定に変更（注：シングルヘッドをデフォルト、"-multi"オプションで指定時は関数kyudo内でハイパーパラメータを設定）
$env:MODEL_TYPE="-models"
$modelx = $env:MODEL_TYPE
$env:MODEL_PT="./kyudo80a_modelse_8-96-3.pt"
$modelpt = $env:MODEL_PT
#
# ハイパーパラメータ設定
$s = 96     # シーケンス長
$b = 192    # バッチサイズ
$e = 281    # エポック数
$d_s = 8    # 埋め込み次元数(section)
$d_c = 4    # 埋め込み次元数(completed)
#
#$s = 128     # シーケンス長
#$b = 256    # バッチサイズ
#$e = 161    # エポック数
#$d_c = 6    # 埋め込み次元数(completed)
$hparam = "($s,$b,$e,$d_s,$d_c)"
#
# 登録ケース名リスト
$cases_list = "iijima_1.7s1-8-3", "anbe_1.7s1-8-3","iwata_1.7s1-8-3", "okochi_1.7s2-8-3", "kanoda_1.7s2-8-3", "tuneyoshi_1.7s2-8-3"
$cases_list = "iijima_1.7s1-8-3", "anbe_1.7s1-8-3","iwata_1.7s1-8-3"
$cases_list = "iijima_1.7s1-6-3", "anbe_1.7s2-6-3","iwata_1.7s1-6-3"
$cases_list = "iijima_1.7s1-3", "iijima_1.7s2-3", "anbe_1.7s1-3","anbe_1.7s2-3"
$cases_list = "iwata_1.7s2-3", "okochi_1.7s2-3", "kanoda_1.7s2-3", "tuneyoshi_1.7s2-3"
$cases_list = "iijima_1.7s1-3", "iijima_1.7s2-3", "anbe_1.7s1-3","anbe_1.7s2-3"
$cases_list = "iijima_1.7s1-3", "iijima_1.7s2-3", "anbe_1.7s1-3"
$cases_list = "iwata_1.7s1-3","iwata_1.7s2-3"
$cases_list = "iijima_1.7s3-3", "iwata_1.7s1-3","iwata_1.7s2-3","iwata_1.7s3-3"
$cases_list = "iijima_1.7s3-3", "iwata_1.7s1-3", "iwata_1.7s3-3"
$cases_list = "iijima_1.7s1-3", "iijima_1.7s2-3", "iwata_1.7s1-3","iwata_1.7s2-3"
$cases_list = "iijima_1.7s3-3", "anbe_1.7s3-3", "iwata_1.7s3-3", "nemoto_1.7s3-3"
$env:CASE_LIST=$cases_list
# モデル設定関数
function model {
    param(
        [switch]$help,
        [string]$head='',
        [string]$case='',
        [string]$pt='',
        [int]$key=0
    )
    if ($help) {
        write-output '・コマンド -オプション'
        write-output ">model -head s|m                  ：モデルタイプ('s':シングルヘッド|'m':マルチヘッド)を設定する"
        write-output ">model -key <input_key>           ：データ入力キーを設定する"
        write-output ">model -case '{<case_name> }...'  ：学習データリストを設定する"
        write-output ">model -pt '{<gru_model_pt> }...' ：学習済モデルファイルを設定する"
        write-output ">model		          ：現在のモデルタイプ、データ入力キー、学習データリスト、GRUモデルファイル（環境変数）を表示する"
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
            $case_list = $env:CASE_LIST
            $str = '・学習データのリストが ' + $case_list + ' に設定されました。'
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
        else{
            write-output '>>' 
            $str = '・モデルオプション  ：  ' + $env:MODEL_TYPE
            Write-Output $str
            $str = '・学習済モデル      ： ' + $env:MODEL_PT 
            write-output $str
            $str = '・ハイパーパラメータ： ' + $hparam
            write-output $str
            $str = '・入力データキー    ： ' + $env:INPUT_KEY
            write-output $str
            $str = '・登録済ケースリスト： ' + $env:CASE_LIST 
            Write-Output $str
        }
    }   
}
# 動画再生・解析ツール関数
function yolo {
    param(
        [switch]$help,
        [switch]$h,
        [switch]$update,
        [switch]$man,
        [switch]$raw,
        [switch]$clip,
        [string]$case,
        [string]$gru
    )
    $param_id = '1.7-s'
    $no=1
    $slevel='s80'
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
    if ($gru -ne '' -and $case -ne ''){
        write-output '不正なパラメータが指定されました' 
        return
    }
    #
    if ($help) {
        write-output '・コマンド -オプション'
        write-output '>yolo  -update -level <no>：姿勢解析パラメータを更新する（no:解析レベル {0|1|2|3}）'
        write-output '>yolo  -raw		：選択した動画ファイルを再生する（一時停止／巻戻し・スキップ／再生速度変更可）'
        write-output '>yolo  -clip		：選択した動画ファイルを切り取り（平面的／時間的）、別ファイルに保存する（モザイク処理範囲の指定可）'
        write-output '>yolo  -man  [-level <no>]                ：選択した動画の射形を解析しながら再生する（no:解析レベル {0|1|2|3}）'
        write-output '>yolo  -case <登録ケース名> [-level <no>] ：選択した動画の射形を解析しながら再生し,解析結果データをファイル出力する（解析結果画像のファイル保存可）'
        write-output '>yolo  -gru  {<GRUモデルファイル名>|-} [-level <no>]：選択した動画の射形を学習済GRUモデルで解析しながら再生する（解析レベル指定でHybrid解析）'
        write-output '>yolo  -h         ：コマンドの詳細パラメータを表示する'
        write-output ''
        write-output '・動画再生中に、画面タップしてキー入力することで以下の処理ができます。'
        write-output ' 0 :解析開始'
        write-output ' 1-8:節の開始'
        write-output ' q :再生終了'
        write-output ' p :一時停止／再開'
        write-output ' r :繰り返し再生開始／停止（"-r"時のみ有効）'
        write-output ' w :ファイル出力開始／停止'
        write-output ' t :解析データ出力開始／停止'
        write-output ' s :スナップショットファイルの作成'
        write-output ' .(>):スキップ'
        write-output ' ,(<):巻き戻し'
        write-output ' k(K) :再生速度アップ'
        write-output ' l(L) :再生速度ダウン'
        write-output ' g :グリッド表示・非表示（"-r"時無効）'
    } 
    elseif ($h) {
        python ./src/yoloApp.py -h
    } 
    elseif ($update) {
        python ./src/yoloApp.py -d1 -I $param_id $slevel
    }
    elseif ($man) {
        python ./src/yoloApp.py -d1 -a -m $slevel --
    }
    elseif ($raw) {
        python ./src/yoloApp.py -d1 -a  -r --
    }
    elseif ($clip) {
        python ./src/yoloApp.py -d1 -a -clip --
    }
    elseif ($case -ne '') {
        python ./src/yoloApp.py -d1 -a -w -t  $case  $slevel classes=3 --
    }
    elseif ($gru -ne '') {
        #$cmdline = 'python ./src/yoloApp.py -d1 -a -m -gru  ' + $gru + ' --' 
        #write-output $cmdline
        if ($gru -eq '-') {
            $model=$modelpt
        }
        else{
            $model=$gru
        }
        python ./src/yoloApp.py -d1 -a -m -gru  $model $slevel --
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
        [switch]$list,
        [string]$import,
        [string]$case,
        [string]$key=''
    )
    if ($help) {
        write-output '・コマンド -オプション'
        write-output '>chart  -list				：登録済ケース名の一覧を表示する'
        write-output '>chart  -import <登録ケース名>                ：解析結果ポイントデータファイルのデータをデータベースに登録する'
        write-output '>chart  -case   <登録ケース名> [-key <データ名>] ：解析結果ポイントデータをグラフ表示する'
        write-output '>chart  -h	  ：コマンドの詳細パラメータを表示する'
    } 
    elseif ($h) {
        python ./src/chart.py -h
    } 
    elseif ($list) {
        python ./src/chart.py  -d -case -L
    } 
    elseif ($import -ne '') {
        python ./src/chart.py  -d -case $import  -import -f0 0 -m
    }
    elseif ($case -ne '') {
        if ($key -ne '') {
            python ./src/chart.py -d  $key -case $case  -f0 0  -m -span 
        }
        else {
            python ./src/chart.py -d  right_wrist left_wrist right_elbow left_elbow -case $case  -f0 0      
        }
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
        [switch]$multi,
        [string]$list='',
        [string]$delete,
        [string]$rename='',
        [string]$to='',
        [string]$import,
        [string]$case,
        [string]$train,
        [switch]$section,
        [string]$predict,
        [int]$input_frames = 0,
        [string]$input_key = '',
        [float]$eta = 0.001
    )
    if ( $input_key -eq '' ) {
        $input_key = $env:INPUT_KEY
    }
    $modelx = $env:MODEL_TYPE
    if ($multi) {
        $modelx = "-modelm"
        $s = 96     # シーケンス長
        $b = 192    # バッチサイズ
        $e = 301    # エポック数
        $d_s = 8    # 埋め込み次元数(section)
        $d_c = 4    # 埋め込み次元数(completed)
        $hparam = "($s,$b,$e,$d_s,$d_c)"
    }
    $model = "-model"
    if ($help) {
        write-output '・コマンド -オプション'
        write-output '>kyudo  -list	case|key|pt                          ：登録済ケース名、入力データキー、または作成済モデルファイルの一覧を表示する'
        write-output '>kyudo  -deletet <登録ケース名>	                     ：登録ケース名、データファイルを削除する'
        write-output '>kyudo  -rename  <登録ケース名> -to <変更ケース名>   ：登録ケース名をリネームする'
        write-output '>kyudo  -import  <登録ケース名>                      ：解析結果データファイルのデータをデータベースに登録する'
        write-output '>kyudo  -case    <登録ケース名> [-input_key <番号>] [-input_frames <表示フレーム数>]          ：解析結果データをグラフ表示する'
        write-output '>kyudo  -train   <登録ケース名> [-section] [-multi] [-model <モデルファイル>] [-eta <学習率>] ：解析結果データで学習する'
        write-output '>kyudo  -predict <登録ケース名> [-multi] -model <モデルファイル>        	              ：解析結果データで予測する'
        write-output '>kyudo  -h		：コマンドの詳細パラメータを表示する'
    } 
    elseif ($h) {
        python ./src/kyudoApp.py -h
    } 
    elseif ($list -ne '') {
        if ( $list -eq 'key' ) {
            python ./src/kyudoApp.py  -d -inputkey
        }
        elseif ( $list -eq 'case' ) {
            python ./src/kyudoApp.py  -d -case -L
        }
        elseif ( $list -eq 'pt' ) {
            get-childitem ./kyudo*.pt
        }
    } 
    elseif ($delete -ne '') {
        python ./src/kyudoApp.py -d -case $delete -D
    }
    elseif ($rename -ne '' -and $to -ne '') {
        python ./src/kyudoApp.py -d -case $rename,$to -R
    }
    elseif ($import -ne '') {
        python ./src/kyudoApp.py -d inputkey=$input_key -case $import -import -f0 0 -m
    }    
    elseif ($case -ne '') {
        python ./src/kyudoApp.py -d inputkey=$input_key -case $case -f0 $input_frames  -m 
    }
    elseif ($train -ne '') {
        $idx = $args.IndexOf($model)
        $len = $args.Length
        if (-not $section ) {
            if ($train -ne 'list') {
                if ($idx -ge 0 -and $len -gt ($idx + 1) ) {
                    python ./src/kyudoApp.py -d -case $train classes=3 eta=$eta -hparam "$hparam" -train $modelx $args[$idx+1] -f0 $input_frames     
                }
                else {
                    python ./src/kyudoApp.py -d -case $train  classes=3 eta=$eta -hparam "$hparam" -train $modelx -f0 $input_frames   
                }
            }
            else {
                if ($idx -ge 0 -and $len -gt ($idx + 1) ) {
                    $case_list = $env:CASE_LIST
                    $str = '・学習データのリスト： ' + $case_list
                    write-output $str
                    $i = 1
                    foreach ( $case_name in $cases_list ) {
                        python ./src/kyudoApp.py -d -case $case_name classes=3 eta=$eta -hparam "$hparam" -train $modelx $args[$idx+1] -f0 $input_frames -n"$i" 
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
            for( $i=0; $i -lt 10; $i++) {
                python ./src/kyudoApp.py -d -case $train  classes=3 eta=$eta -hparam "$hparam" section=$i  -train $modelx $args[$idx+1] -f0 $input_frames -n 
            } 
        }
        else{
            write-output 'モデルファイル名を指定してください' 
        }
    }
    elseif ($predict -ne '') {
        $idx = $args.IndexOf($model)
        $len = $args.Length
        if ($idx -ge 0 ) {
            if ( $len -gt $idx) {
                $modelpt = $args[$idx+1]
            }
            python ./src/kyudoApp.py -d -case $predict -hparam "$hparam" -predict $modelx $modelpt -f0 $input_frames -m    
        }
        else {
            write-output '学習済モデルファイル名を指定してください' 
        }
    }
    else{
        write-output '不正なパラメータが指定されました' 
    }	
}
# モデル設定関数呼び出し（プロファイル読み込み時）
model
