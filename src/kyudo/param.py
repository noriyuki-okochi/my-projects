
##############################
# 解析パラメータ
##############################
Param_max = 10    # パラメータテーブルの最大列数
# 動作完了解析パラメータ（act = 0）
CompleteAction_param = {'frame': '',      # <frame>-<model>
                      'step': 1,          # レベル
                      'act':0,            # 完了／開始(=0/1)
                      'param': []         # パラメータ
                      }

# 動作開始解析パラメータ（act = 1）
StartAction_param = {'frame': '', 
                     'step': 1, 
                     'act':1, 
                     'param': [] 
                     }
#
# 初期登録用動作完了解析パラメータ
#
InitAction_param_nms = ['8-n', '8-s', '1.7-s']
#
CompleteAction_params = [
    {'frame': '18-n',   #約1.0秒
     'step': 1,
     'act': 0,
     'param': [
        [None, None, None, None, None, None, None, None],            # 0.
        [0.028, 0.5, 0.035, 0.035, 0.035, 0.035, 1.000, 2],          # 1.足踏み
        [60.0, 95.0, 0.03, 2, 0.080, 5, None, None],                 # 2.胴作り
        [0.025, 0.025, 0.025, 0.025, 3, 0.027, 2, 0.034],            # 3.弓構え
        [0.020, 0.020, 0.020, 0.020, 3, None, None, None],           # 4.打起こし
        [0.000, 0, 0.000, 0.025, 1.000, 0.025, 1.000, 5, 0, 0.085],  # 5.引分け
        [0.017, 1.000, 0.017, 1.000, 5, 0.050, 0.00, None],          # 6.会
        [10, None, None, None, None, None, None, None],              # 7.離れ
        [0.10, 0.10, 3, None, None, None, None, None],               # 8.残心
        [25.0, 95.0, 0.030, 2, 0.085, None, None, None],             # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },
    {'frame': '8-n',  # 約0.5秒
     'step': 1,
     'act': 0,
     'param': [
        [None, None, None, None, None, None, None, None],            # 0.
        [0.028, 0.5, 0.015, 0.015, 0.015, 0.015, 1.000, 3],          # 1.足踏み
        [50.0, 95.0, 0.015, 2, 0.040, 5, None, None],                # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 3, 0.027, 2, 0.05 ],            # 3.弓構え
        [0.008, 0.008, 0.008, 0.008, 8, None, None, None],           # 4.打起こし
        [1.000, 0, 0.000, 0.008, 1.000, 0.008, 1.000, 5, 0, 0.085],  # 5.引分け
        [0.015, 1.000, 0.015, 1.000, 5, 0.050, 0.00, None],          # 6.会
        [5, None, None, None, None, None, None, None],               # 7.離れ
        [0.085, 0.085, 3, None, None, None, None, None],             # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],             # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },
   {'frame': '8-s',  # 約0.5秒
     'step': 1,
     'act': 0,
     'param': [
        [None, None, None, None, None, None, None, None],            # 0.
        [0.028, 0.5, 0.015, 0.015, 0.015, 0.015, 1.000, 9],          # 1.足踏み
        [50.0, 90.0, 0.015, 2, 0.040, 5, None, None],                # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.027, 2, 0.04 ],            # 3.弓構え
        [0.005, 0.005, 0.005, 0.005, 9, None, None, None],           # 4.打起こし
        [0.003, 8, 0.015, 0.008, 1.000, 0.008, 1.000, 5, 0, 0.085],  # 5.引分け
        [0.008, 0.008, 0.008, 0.008, 5, 0.050, 0.00, None],          # 6.会
        [5, None, None, None, None, None, None, None],               # 7.離れ
        [0.080, 0.080, 3, None, None, None, None, None],             # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],             # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },
   {'frame': '1.7-s',  # 約0.5秒
     'step': 1,
     'act': 0,
     'param': [
        [None, None, None, None, None, None, None, None],            # 0.
        [0.028, 0.5, 0.015, 0.015, 0.015, 0.015, 1.000, 9],          # 1.足踏み
        [50.0, 90.0, 0.015, 2, 0.040, 5, None, None],                # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.027, 2, 0.04 ],            # 3.弓構え
        [0.005, 0.005, 0.005, 0.005, 5, None, None, None],           # 4.打起こし
        [0.008, 8, 0.015, 0.008, 1.000, 0.008, 1.000, 5, 0, 0.085],  # 5.引分け
        [0.008, 0.008, 0.008, 0.008, 5, 0.050, 0.00, None],          # 6.会
        [5, None, None, None, None, None, None, None],               # 7.離れ
        [0.080, 0.080, 3, None, None, None, None, None],             # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],             # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },
   {'frame': '1.7-s',  # 約0.5秒
     'step': 2,
     'act': 0,
     'param': [
        [None, None, None, None, None, None, None, None],            # 0.
        [0.028, 0.5, 0.015, 0.015, 0.015, 0.015, 1.000, 9],          # 1.足踏み
        [50.0, 95.0, 0.015, 2, 0.040, 5, None, None],                # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.027, 2, 0.04 ],            # 3.弓構え
        [0.009, 0.009, 0.009, 0.009, 4, None, None, None],           # 4.打起こし
        [0.008, 8, 0.015, 0.008, 1.000, 0.008, 1.000, 5, 0, 0.085],  # 5.引分け
        [0.008, 0.008, 0.008, 0.008, 4, 0.050, 0.00, None],          # 6.会
        [5, None, None, None, None, None, None, None],               # 7.離れ
        [0.080, 0.080, 3, None, None, None, None, None],             # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],             # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    }
]

# 初期登録用動作開始解析パラメータ
StartAction_params = [
    {'frame': '18-n',   #約1.0秒
     'step': 1,
     'act': 1,
     'param': [
        [0.150, 0.140, None, None, None, None, None, None],          # 0.
        [0.080, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.030, 0.035, 4, None, None, None, None, None],             # 2.胴作り
        [0.034, 0.034, 6, None, None, None, None, None],             # 3.弓構え
        [0.035, 0.035, 0.90, 1, None, None, None, None],             # 4.打起こし
        [0.025, 1.000, 0.025, 1.000, 5, 0.050, None, None],          # 5.引分け
        [0.085, 0.085, None, None, None, None, None, None],          # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.085, 0.085, None, None, None, None, None, None],          # 8.残心
        [0.085, 2, 0.085, 2, None, None, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },          
    {'frame': '8-n',    # 約0.5秒
     'step': 1,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [0.080, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.030, 0.035, 3, None, None, None, None, None],             # 2.胴作り
        [0.050, 0.050, 3, None, None, None, None, None],             # 3.弓構え
        [0.010, 0.010, 0.90, 1, None, None, None, None],             # 4.打起こし
        [0.025, 1.000, 0.025, 1.000, 5, 0.050, None, None],          # 5.引分け
        [0.030, 0.020, 8, None, None, None, None, None],             # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.1, 0.1, None, None, None, None, None, None],              # 8.残心
        [0.085, 2, 0.085, 2, None, None, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },          
    {'frame': '8-s',    # 約0.5秒
     'step': 1,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [0.080, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.030, 0.035, 3, None, None, None, None, None],             # 2.胴作り
        [0.040, 0.040, 3, None, None, None, None, None],             # 3.弓構え
        [0.013, 0.015, 0.90, 1, None, None, None, None],             # 4.打起こし
        [0.008, 0.008, 0.008, 0.008, 6, 0.050, None, None],          # 5.引分け
        [0.050, 0.000, None, None, None, None, None, None],          # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.085, 0.085, None, None, None, None, None, None],          # 8.残心
        [0.085, 2, 0.085, 2, None, None, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },          
    {'frame': '1.7-s',    # 約0.5秒
     'step': 1,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [0.080, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.030, 0.035, 3, None, None, None, None, None],             # 2.胴作り
        [0.040, 0.040, 3, None, None, None, None, None],             # 3.弓構え
        [0.015, 0.015, 0.90, 2, None, None, None, None],             # 4.打起こし
        [0.008, 0.008, 0.008, 0.008, 6, 0.050, None, None],          # 5.引分け
        [0.050, 0.020, 8, None, None, None, None, None],             # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.085, 0.085, None, None, None, None, None, None],          # 8.残心
        [0.085, 2, 0.085, 2, None, None, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },          
    {'frame': '1.7-s',    # 約0.5秒
     'step': 2,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [0.080, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.030, 0.035, 3, None, None, None, None, None],             # 2.胴作り
        [0.040, 0.040, 3, None, None, None, None, None],             # 3.弓構え
        [0.025, 0.025, 0.90, 4, None, None, None, None],             # 4.打起こし
        [0.008, 0.008, 0.008, 0.008, 4, 0.050, None, None],          # 5.引分け
        [0.050, 0.020, 8, None, None, None, None, None],             # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.085, 0.085, None, None, None, None, None, None],          # 8.残心
        [0.085, 2, 0.085, 2, None, None, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    }          
]
# eof
