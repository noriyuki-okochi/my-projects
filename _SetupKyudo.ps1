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
    Write-Host  ">>Profile file already exists at '$profile_pass'."
    $answer = Read-Host "> Do you want to replace the above items in the existing profile file? (Y/n)"
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
Write-Host  ">>Setting ROLL_PATH to '$roll_path'."
$answer = Read-Host "> Do you want to set ROLL_PATH to other than '$roll_path'? (Y/n)"
if ($answer -eq "Y") {
    $roll_path_new = Read-Host "> Please enter the path for ROLL_PATH (e.g., C:/Users/YourName/Pictures/Camera Roll/)"
    (Get-content $profile_pass) | ForEach-Object { $_ -replace '$roll_path', $roll_path_new } | Set-Content $profile_pass
    (Get-content ./StartKyudo.ps1) | ForEach-Object { $_ -replace '$roll_path', $roll_path_new } | Set-Content .\StartKyudo.ps1
    Write-Host  ">>Updated ROLL_PATH to '$roll_path_new' in $profile_pass."
}
# Python 3のインストール確認
$version = & python -V 2>&1 
if ($version -match "Python 3") {
    Write-Host  ">>$version is installed."
    $answer = Read-Host "> Do you want to install the required packages for Kyudo? (Y/n)"
    if ($answer -eq "Y") {
         python -m pip install -r requirements.txt
    } else {
        Write-Host ">>Skipping package installation. You can install the required packages later by running 'python -m pip install -r requirement.txt'."
    }
} else {
    Write-Host "Python 3 is not installed. Please install Python 3 from Microsoft-Store to use Kyudo."
}
