import os
import sys
import subprocess
from datetime import datetime
#
# SJISテキストファイルのコピー関数
#
def file_copy(src, dst):
    # srcファイルの存在チェック    
    if not os.path.exists(src):
        print(f"Source file '{src}' does not exist")
        return 0
    counter = 0
    # SJISで読み込み、SJISで追記
    with open(src, "r", encoding="shift_jis", errors="ignore") as f_in, \
        open(dst, "a", encoding="shift_jis") as f_out:
        for line in f_in:
            f_out.write(line)
            counter += 1
    print(f"Copied {counter} lines from {src} to {dst}")
    return counter

#
# コマンドライン
#   python setup.py  $profile
#
def main():
    # コマンドライン引数の処理
    if len(sys.argv) < 2:
        print("Usage: python setup.py $profile")
        return
    profile = sys.argv[1]
    print(f"デフォルトのユーザプロファイル: {profile}")
    #
    # プロファイルの存在チェック
    if not os.path.exists(profile):
        print(f"デフォルトのユーザープロファイルが存在しません.")
        print(f"デフォルトのユーザープロファイルはターミナルオープン時に自動で実行されます.")
        print(f">作成しますか? [Y/n]")
        ans = input(f">:")
        if ans == 'Y':
            # プロファイルが存在しない場合、空のファイルを作成する
            res = subprocess.run(f"powershell -Command New-Item -Path {profile} -ItemType File -Force", 
                                stdout=subprocess.PIPE, shell=True, encoding="cp932")
            #print(f"subprocess[New-Item] result: {res.stdout}")
            print(f" Profile '{profile}' is created.")
            # './_profile.ps1'を'profile'にコピーする
            ret = file_copy("./_profile.ps1", profile)
            if ret == 0:
                print(f"Failed to copy './_profile.ps1' to '{profile}'")
                return
    # './SetupKyudo.ps1'の存在チェック
    if not os.path.exists("./SetupKyudo.ps1"):
        #空のファイルを作成する
        with open("./SetupKyudo.ps1", "w") as f: pass
        print(f"File './SetupKyudo.ps1' is created.")
        # './_SetupKyudo.ps1'を'./SetupKyudo.ps1'にコピーする
        ret = file_copy("./_SetupKyudo.ps1", "./SetupKyudo.ps1")
        if ret == 0:
            print(f"Failed to copy './_SetupKyudo.ps1' to './SetupKyudo.ps1'")
            return
    # 
    # './StartKyudo.ps1'の存在チェック
    if not os.path.exists("./StartKyudo.ps1"):
        #空のファイルを作成する
        with open("./StartKyudo.ps1", "w") as f: pass
        print(f"File './StartKyudo.ps1' is created.")
        # './_StartKyudo.ps1'を'./StartKyudo.ps1'にコピーする
        ret = file_copy("./_StartKyudo.ps1", "./StartKyudo.ps1")
        if ret == 0:
            print(f"Failed to copy './_StartKyudo.ps1' to './StartKyudo.ps1'")
            return
        
    print(f">>セットアッププロファイル('./SetupKyudo.ps1')を実行してインストールを続行してください.")
    '''
    #
    # プロファイルの実行ポリシーをRemoteSignedに設定する
    res = subprocess.run(f"powershell -Command Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force", 
        stdout=subprocess.PIPE, shell=True, encoding="cp932")
    print(f"subprocess[Set-ExecutionPolicy] result: {res.stdout}")
    #
    # プロファイル'SetupKyudo.ps1'の内容を実行する
    res = subprocess.run(f"powershell -Command .\\SetupKyudo.ps1", 
        stdout=subprocess.PIPE, shell=True, encoding="cp932")
    print(f"subprocess[SetupKyudo.ps1] result: {res.stdout}")
    '''
    #
if __name__ == "__main__":
    print(datetime.now())
    print(os.getcwd())
    main()
# eof