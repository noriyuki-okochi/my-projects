(弓道射法八節動作解析アプリーインストール手順）		


１）	ZIPファイルをダウンロードして解凍する

	１．zipファイルを"右クリック＞全て展開"で解凍する	
	２．展開先フォルダーに”c:\Users\ユーザー名\”を指定する
	３．展開後のトップフォルダーを"YOLO"にリネームする
		
２）	pythonをMicrosoft Storeからインストールする	
		
３）	ターミナル（管理者）、またはPowerShell（管理者）でコンソールを開いて、SetupKyudo.ps1を実行する。	
		
	    >cd c:\Users\ユーザー名\YOLO	
	    >PowerShell -ExecutionPolicy RemoteSigned SetupProfile.ps1	
	①	ユーザー許可のプロファイル実行ポリシーを恒常的に設定する。
		> Set-ExecutionPolicy RemoteSigned
	②	カレントのフォルダー位置をアプリの実行フォルダーに設定する
	③	動画ファイルを保存するデフォルトのフォルダーを設定する
	④	コンソールオープン時に自動的に実行されるユーザープロファイルを作成する。
		（カレントのprofile.ps1をユーザープロファイルにコピーする）
	⑤	アプリ実行に必要なパッケージをインストールする
		> py -m pip install -r  requirment.txt
		
（実行）		
1）	ターミナル、またはPowerShellでコンソールを開く。	
		
	（※）ユーザープロファイル未作成のとき、StartKyudo.ps1を実行する	
	       > ./StartKyudo.ps1	
		
		
２)	Helpメニューに従ってコンソールからコマンドを入力する。	
		
