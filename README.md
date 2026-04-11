(弓道射法八節動作解析アプリーインストール手順）  

１）ZIPファイルをダウンロードして解凍する  

	１．zipファイルを"右クリック＞全て展開"で解凍する  
	２．展開先フォルダーに”c:\Users\ユーザー名\”を指定する  
	３．展開後のトップフォルダーを"YOLO"にリネームする
		
２）pythonをMicrosoft Storeからインストールする

	 ・インストールの有無、インストール済pythonのバージョンはコンソールから確認  
        > python -V  
    （注）Visual Studio(C:\ProgramFile(x86)\Microsoft VisualStudio)がないときは、  
          Visual Studio Community206のインストールが必要。  
          https://visualstudio.microsoft.com/ja/vs/community/  
          （インストール時に、「Python開発」にチェックを入れる）
		
３）ターミナル（管理者）、またはPowerShell（管理者）でコンソールを開く（タスクバーのスタート右クリックメニュー）

	１.アプリ実行フォルダーに移動して、セットアッププロファイルを作成する。  
	   （コンソールオープン時に自動的に実行されるユーザープロファイルも作成可  
	   
	    >cd c:\Users\ユーザー名\YOLO  
	    >python ./src/setup.py $profile  
		
	２．セットアッププロファイルを実行する。 

	    >./SetupKyudo.ps1    
	
	　		① ユーザー許可のプロファイル実行ポリシーを恒常的に設定する。  
				> Set-ExecutionPolicy RemoteSigned  
	　		② カレントのフォルダー位置をアプリの実行フォルダーに設定する  
	　		③ 動画ファイルを保存するデフォルトのフォルダーを設定する  
	　		④ 必要に応じて、Pythonの仮想環境を作成する  
	　		⑤ アプリ実行に必要なパッケージをインストールする  
	  		（注）アンチウィルスソフトのリアルタイムスキャンを停止しておく  
				> python -m pip install -r  requirments.txt  
		
（実行手順）  

１）ターミナル、またはPowerShellでコンソールを開く。 

	（※）ユーザープロファイル未作成のとき、StartKyudo.ps1を実行する  
	
	> ./StartKyudo.ps1  
			
２）helpメニューに従ってコンソールからコマンドを入力する。  	
