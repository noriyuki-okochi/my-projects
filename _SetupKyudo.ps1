#PowerShell -ExecutionPolicy RemoteSigned SetupKyudo.ps1
# プロファイルの実行ポリシーをRemoteSignedに設定することで、ローカルで作成したスクリプトを実行できるようになります。
Set-ExecutionPolicy RemoteSigned 
Write-Host  ">>'Set ExecutionPolicy' to RemoteSigned."
# ホームディレクトリ（カレントディレクトリ）設定
$home_dir = (Get-Location).Path
# StartKyudo.ps1のユーザ名とホームディレクトリを置換
(Get-content ./StartKyudo.ps1) | ForEach-Object { $_ -replace 'user-home', $home_dir } | Set-Content .\StartKyudo.ps1
(Get-content ./StartKyudo.ps1) | ForEach-Object { $_ -replace 'user-name', $env:USERNAME } | Set-Content .\StartKyudo.ps1
Write-Host  ">>'user-home' replaced with '$home_dir' in StartKyudo.ps1."
Write-Host  ">>'user-name' replaced with '$env:USERNAME' in StartKyudo.ps1."
#
# ユーザープロファイルのパスを取得
$profile_pass = $profile
$ans = & Test-Path -Path $profile_pass 2>&1 
Write-Host  ">>'$profile_pass' exists: $ans"
if ($ans) {
    Write-Host  ">>デフォルトのユーザープロファイルが'$profile_pass' に存在しています。"
    $answer = Read-Host "> このプロファイルを、本’Kyudo’プロジェクトで使用しますか? (Y/n)"
    if ($answer -ne "Y") {
        $ans = $false
    }
}
if ($ans) {
    (Get-content $profile_pass) | ForEach-Object { $_ -replace 'user-home', $home_dir } | Set-Content $profile_pass
    (Get-content $profile_pass) | ForEach-Object { $_ -replace 'user-name', $env:USERNAME } | Set-Content $profile_pass
    Write-Host  ">>'user-home' replaced with '$home_dir' in $profile_pass."
    Write-Host  ">>'user-name' replaced with '$env:USERNAME' in $profile_pass."
}
$roll_path = "C:/Users/$env:USERNAME/Pictures/Camera Roll/"
Write-Host  ">>デフォルトの動画フォルダ：'$roll_path'"
$answer = Read-Host "> デフォルトの動画フォルダを '$roll_path' 以外に変更しますか? (Y/n)"
if ($answer -eq "Y") {
    #$roll_path_new = Read-Host "> 新しい動画フォルダのパスを入力してください (例: C:/Users/YourName/Pictures/Camera Roll/)"
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.RootFolder = 'Desktop'
    $dialog.Description = 'デフォルトの動画フォルダを選択してください'
    # フォルダ選択の有無を判定
    if($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){

        $roll_path_new = $dialog.SelectedPath
        Write-Host  ">>'$roll_path_new' selected:"
        if($ans){
            (Get-content $profile_pass) | ForEach-Object { $_ -replace $roll_path, $roll_path_new } | Set-Content $profile_pass
            Write-Host  ">>Updated ROLL_PATH to '$roll_path_new' in $profile_pass."
        }
        (Get-content ./StartKyudo.ps1) | ForEach-Object { $_ -replace $roll_path, $roll_path_new } | Set-Content .\StartKyudo.ps1
        Write-Host  ">>Updated ROLL_PATH to '$roll_path_new' in StartKyudo.ps1."
    }
    else {
        Write-Host  ">>canceled."
    }
}
# Python 3のインストール確認
$version = & python -V 2>&1 
if ($version -match "Python 3") {
    Write-Host  ">>$version is installed."
    # Python仮想環境の作成と有効化
    $answer = Read-Host "> Python仮想環境を作成しますか? (Y/n)"
    if ($answer -eq "Y") {
        python -m venv .venv
        Write-Host  ">>Python virtual environment '.venv' created."
        ./.venv/Scripts/Activate.ps1
        Write-Host  ">>Python virtual environment '.venv' activated."
        write-Host  ">>deavtivateコマンドで仮想環境を終了できます。"
    }
    # Kyudoプロジェクトの依存パッケージのインストール
    $answer = Read-Host "> 本'Kyudo'プロジェクトの依存パッケージをインストールしますか? (Y/n)"
    if ($answer -eq "Y") {
         python -m pip install -r requirements.txt
    } else {
        Write-Host ">>Skipping package installation. You can install the required packages later by running 'python -m pip install -r requirement.txt'."
    }
} else {
    Write-Host "Python 3 is not installed. Please install Python 3 from Microsoft-Store to use Kyudo."
}
