f:
set-location share/YOLO
write-output $profile
write-output 'Hellow YOLO!!'
write-output '・次のコマンドを実行することで、射形動画解析ツールの使用ガイダンスが表示されます。'
write-output '> yolo   -help		：動画再生・解析ツール'
write-output '> chart  -help		：解析データ登録／プロットツール'
write-output '> kyudo  -help		：解析学習・予測／プロットツール'
# モデルオプション設定
$modelx = "-models"
#
# ハイパーパラメータ設定
#$s = 128    # シーケンス長
#$b = 256    # バッチサイズ
#$e = 301    # エポック数
$s = 96     # シーケンス長
$b = 192    # バッチサイズ
$e = 301    # エポック数
$hparam = "($s,$b,$e,,)"
# 登録ケース名リスト
$cases_list = "iijima_1.7s1-3",
              "anbe_1.7s1-3",
              "iwata_1.7s1-3",
              "okochi_1.7s1-3"
#              "iwata_1.7s1-3","iwata_1.7s2-3"
function yolo {
    param(
        [switch]$help,
        [switch]$h,
        [switch]$all,
        [string]$case,
        [string]$gru,
        [switch]$raw,
        [switch]$clip
    )
    $no=1
    $slevel='-s'
    $idx = $args.IndexOf("-level")
    $len = $args.Length
    if ( $idx -ge 0 -and  $len -gt ($idx + 1) ) {
        $no=-1
        if ( [int]::TryParse($args[$idx+1],[ref]$no) ){}
        if ( $no%10 -lt 1 -or $no%10 -gt 3 ) {
            $msg = '解析レベルには1～3(11～13)の数値を指定してください: ' + $args[$idx+1]
            write-output $msg
            return
        }
    } 
    $slevel = $slevel + $no
    #
    if ($help) {
        write-output '・コマンド -オプション'
        write-output '>yolo  -raw		：選択した動画ファイルを再生する（一時停止／巻戻し・スキップ／再生速度変更可）'
        write-output '>yolo  -clip		：選択した動画ファイルを切り取り（平面的／時間的）、別ファイルに保存する（モザイク処理範囲の指定可）'
        write-output '>yolo  -all [-level <no>]：選択した動画の射形を解析しながら再生する（no:解析レベル {1|2|3}）'
        write-output '>yolo  -case "<登録ケース名>" [-level <no>]：選択した動画の射形を解析しながら再生し,解析結果データをファイル出力する（解析結果画像のファイル保存可）'
        write-output '>yolo  -gru  "<GRUモデルファイル名>|non" [-level <no>]：選択した動画の射形を学習済GRUモデルで解析しながら再生する（no:解析レベル {11|12|13}）'
        write-output '>yolo  -h		：コマンドの詳細パラメータを表示する'
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
    elseif ($all) {
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
        $model='./kyudo_modelme_7-80-3.pt'
        if($gru -ne 'non'){
            $model=$gru
        }
        python ./src/yoloApp.py -d1 -a -m -gru  $model $slevel --
    }
    else{
        write-output '不正なパラメータが指定されました' 
    }
}
function yolo0 { 
	python ./src/yoloApp.py 0 
}
function chart {
    param(
        [switch]$help,
        [switch]$h,
        [switch]$list,
        [string]$import,
        [string]$case
    )
    if ($help) {
        write-output '・コマンド -オプション'
        write-output '>chart  -list				：登録済ケース名の一覧を表示する'
        write-output '>chart  -import  "<登録ケース名>" 	：解析結果データファイルのデータをデータベースに登録する'
        write-output '>chart  -case "<登録ケース名>"		：解析結果データをグラフ表示する'
        write-output '>chart  -h				：コマンドの詳細パラメータを表示する'
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
        python ./src/chart.py -d  right_wrist -case $case  -f0 0  -m -span 
    }
    else{
        write-output '不正なパラメータが指定されました' 
    }	
}
function kyudo {
    param(
        [switch]$help,
        [switch]$h,
        [switch]$multi,
        [switch]$list,
        [string]$delete,
        [string]$import,
        [string]$case,
        [string]$train,
        [switch]$section,
        [string]$predict
    )
    $model = "-model"
    if ($multi) {
        $modelx = "-modelm"
        $s = 96     # シーケンス長
        $b = 192    # バッチサイズ
        $e = 301    # エポック数
        $hparam = "($s,$b,$e,,)"
    }
    if ($help) {
        write-output '・コマンド -オプション'
        write-output '>kyudo  -list				：登録済ケース名の一覧を表示する'
        write-output '>kyudo  -import  "<登録ケース名>" 	：解析結果データファイルのデータをデータベースに登録する'
        write-output '>kyudo  -deletet  "<登録ケース名>"	：登録ケース名、データファイルを削除する'
        write-output '>kyudo  -case "<登録ケース名>"		：解析結果データをグラフ表示する'
        write-output '>kyudo  -train "<登録ケース名>" [-section] [-multi] -model [<モデルファイル>]	：解析結果データで学習する'
        write-output '>kyudo  -predict "<登録ケース名>" [-multi] -model <モデルファイル>        	：解析結果データで予測する'
        write-output '>kyudo  -h				：コマンドの詳細パラメータを表示する'
    } 
    elseif ($h) {
        python ./src/kyudoApp.py -h
    } 
    elseif ($list) {
        python ./src/kyudoApp.py  -d -case -L
    } 
    elseif ($delete -ne '') {
        python ./src/kyudoApp.py -d   -case $delete  -D
    }
    elseif ($import -ne '') {
        python ./src/kyudoApp.py  -d -case $import  -import -f0 0 -m
    }    
    elseif ($case -ne '') {
        python ./src/kyudoApp.py -d   -case $case  -f0 0  -m 
    }
    elseif ($train -ne '') {
        $idx = $args.IndexOf($model)
        $len = $args.Length
        if (-not $section ) {
            if ($train -ne 'list') {
                if ($idx -ge 0 -and $len -gt ($idx + 1) ) {
                    python ./src/kyudoApp.py -d -case $train classes=3 -hparam "$hparam" -train $modelx $args[$idx+1] -f0 0     
                }
                else {
                    python ./src/kyudoApp.py -d -case $train  classes=3 -hparam "$hparam" -train $modelx -f0 0   
                }
            }
            else {
                if ($idx -ge 0 -and $len -gt ($idx + 1) ) {
                    foreach ( $case_name in $cases_list ) {
                        python ./src/kyudoApp.py -d -case $case_name classes=3 -hparam "$hparam" -train $modelx $args[$idx+1] -f0 0 -n     
                    }
                }
                else {
                    write-output 'モデルファイル名を指定してください' 
                }
            }
        }
        elseif ( $idx -ge 0 -and $len -gt ($idx + 1) ) {
            for( $i=0; $i -lt 10; $i++) {
                python ./src/kyudoApp.py -d -case $train  classes=3 -hparam "$hparam" section=$i  -train $modelx $args[$idx+1] -f0 0 -n 
            } 
        }
        else{
            write-output 'モデルファイル名を指定してください' 
        }
    }
    elseif ($predict -ne '') {
        $idx = $args.IndexOf($model)
        $len = $args.Length
        if ($idx -ge 0 -and $len -gt $idx) {
            python ./src/kyudoApp.py -d -case $predict -hparam "$hparam" -predict $modelx $args[$idx+1] -f0 0 -m    
        }
        else {
            write-output '学習済モデルファイル名を指定してください' 
        }
    }
    else{
        write-output '不正なパラメータが指定されました' 
    }	
}
