
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
#InitAction_param_nms = ['8-s', '1.7-s']
InitAction_param_nms = ['1.7-s', '1.7-m']            # 実用では'8-s'は使用しない
#
CompleteAction_params = [
   {'frame': '1.7-s',  # 約0.5秒
     'step': 0,
     'act': 0,
     'param': [
        [None, None, None, None, None, None, None, None],            # 0.
        [0.150, 0.9, 0.015, 0.015, 0.015, 0.015, 1.000, 9],          # 1.足踏み
        [50.0, 100.0, 120.0, 0.015, 2, 0.040, 3, 5, 0.00],           # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.027, 2, 0.04 ],            # 3.弓構え
        [0.005, 1.000, 1.000, 1.000, 9, None, None, None],           # 4.打起こし
        [0.009, 6, 0.015, 0.006, 1.000, 0.006, 1.000, 3, 0, 0.085],  # 5.引分け
        [0.006, 0.006, 0.006, 0.006, 9, 0.050, 0.00, None],          # 6.会
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
        [0.180, 0.9, 0.015, 0.015, 0.015, 0.015, 1.000, 9],          # 1.足踏み
        [50.0, 90.0, 120.0, 0.015, 2, 0.040, 2, 5, 0.03],            # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.027, 2, 0.04 ],            # 3.弓構え
        [0.006, 0.006, 0.006, 0.006, 5, None, None, None],           # 4.打起こし
        [0.0045, 6, 0.015, 0.0045,1.000, 0.0045,1.000, 3, 0, 0.085], # 5.引分け
        [0.006, 0.006, 0.006, 0.006, 5, 0.050, 0.00, None],          # 6.会
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
        [0.180, 0.9, 0.015, 0.015, 0.015, 0.015, 1.000, 9],          # 1.足踏み
        [50.0, 90.0, 120.0, 0.015, 2, 0.040, 2, 5, 0.03],            # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.027, 2, 0.04 ],            # 3.弓構え
        [0.006, 0.006, 0.006, 0.006, 5, None, None, None],           # 4.打起こし
        [0.008, 6, 0.015, 0.006, 1.000, 0.006, 1.000, 3, 0, 0.085],  # 5.引分け
        [0.006, 0.006, 0.006, 0.006, 5, 0.050, 0.00, None],          # 6.会
        [5, None, None, None, None, None, None, None],               # 7.離れ
        [0.080, 0.080, 3, None, None, None, None, None],             # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],             # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },
   {'frame': '1.7-s',  # 約0.5秒
     'step': 3,
     'act': 0,
     'param': [
        [None, None, None, None, None, None, None, None],            # 0.
        [0.180, 0.9, 1.000, 0.015, 0.015, 0.015, 1.000, 5],          # 1.足踏み
        [45.0, 95.0, 120.0, 0.015, 2, 0.040, 2, 3, 0.03],            # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.032, 1, 0.040],            # 3.弓構え
        [0.009, 1.000, 1.000, 1.000, 5, None, None, None],           # 4.打起こし
        [0.008, 6, 0.015, 0.008, 1.000, 0.008, 1.000, 5, 0, 0.085],  # 5.引分け
        [0.008, 0.008, 0.008, 0.008, 4, 0.050, 0.00, None],          # 6.会
        [5, None, None, None, None, None, None, None],               # 7.離れ
        [0.080, 0.080, 3, None, None, None, None, None],             # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],             # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },
   {'frame': '1.7-s',  # 約0.5秒
     'step': 9,
     'act': 0,
     'param': [
        [None, None, None, None, None, None, None, None],            # 0.
        [0.150, 0.9, 0.015, 0.015, 0.015, 0.015, 1.000, 9],          # 1.足踏み
        [50.0, 100.0, 120.0, 0.015, 2, 0.040, 3, 5, 0.00],           # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.027, 2, 0.04 ],            # 3.弓構え
        [0.005, 1.000, 1.000, 1.000, 9, None, None, None],           # 4.打起こし
        [0.009, 6, 0.015, 0.006, 1.000, 0.006, 1.000, 3, 0, 0.085],  # 5.引分け
        [0.006, 0.006, 0.006, 0.006, 9, 0.050, 0.00, None],          # 6.会
        [5, None, None, None, None, None, None, None],               # 7.離れ
        [0.080, 0.080, 3, None, None, None, None, None],             # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],             # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },
   {'frame': '1.7-m',  # 約0.5秒
     'step': 0,
     'act': 0,
     'param': [
        [None, None, None, None, None, None, None, None],            # 0.
        [0.180, 0.9, 0.015, 0.015, 0.015, 0.015, 1.000, 9],          # 1.足踏み
        [50.0, 90.0, 120.0, 0.012, 2, 0.040, 2, 5, 0.00],            # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.030, 2, 0.04 ],            # 3.弓構え
        [0.006, 0.006, 1.000, 1.000, 5, None, None, None],           # 4.打起こし
        [0.009, 6, 0.015, 0.006, 1.000, 0.006, 1.000, 3, 0, 0.085],  # 5.引分け
        [0.006, 0.006, 0.006, 0.006, 5, 0.050, 0.00, None],          # 6.会
        [5, None, None, None, None, None, None, None],               # 7.離れ
        [0.080, 0.080, 3, None, None, None, None, None],             # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],             # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },
   {'frame': '1.7-m',  # 約0.5秒
     'step': 1,
     'act': 0,
     'param': [
        [None, None, None, None, None, None, None, None],            # 0.
        [0.180, 0.9, 0.015, 0.015, 0.015, 0.015, 1.000, 9],          # 1.足踏み
        [50.0, 90.0, 120.0, 0.015, 2, 0.040, 2, 5, 0.03],            # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.027, 2, 0.04 ],            # 3.弓構え
        [0.006, 0.006, 0.006, 0.006, 5, None, None, None],           # 4.打起こし
        [0.008, 6, 0.015, 0.006, 1.000, 0.006, 1.000, 3, 0, 0.085],  # 5.引分け
        [0.006, 0.006, 0.006, 0.006, 5, 0.050, 0.00, None],          # 6.会
        [5, None, None, None, None, None, None, None],               # 7.離れ
        [0.080, 0.080, 3, None, None, None, None, None],             # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],             # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },
   {'frame': '1.7-m',  # 約0.5秒
     'step': 2,
     'act': 0,
     'param': [
        [None, None, None, None, None, None, None, None],            # 0.
        [0.180, 0.9, 0.015, 0.015, 0.015, 0.015, 1.000, 9],          # 1.足踏み
        [50.0, 90.0, 120.0, 0.015, 2, 0.040, 2, 5, 0.03],            # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.027, 2, 0.04 ],            # 3.弓構え
        [0.006, 0.006, 0.006, 0.006, 5, None, None, None],           # 4.打起こし
        [0.008, 6, 0.015, 0.006, 1.000, 0.006, 1.000, 3, 0, 0.085],  # 5.引分け
        [0.006, 0.006, 0.006, 0.006, 5, 0.050, 0.00, None],          # 6.会
        [5, None, None, None, None, None, None, None],               # 7.離れ
        [0.080, 0.080, 3, None, None, None, None, None],             # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],             # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },
   {'frame': '1.7-m',  # 約0.5秒
     'step': 9,
     'act': 0,
     'param': [
        [None, None, None, None, None, None, None, None],            # 0.
        [0.180, 0.9, 0.015, 0.015, 0.015, 0.015, 1.000, 9],          # 1.足踏み
        [50.0, 90.0, 120.0, 0.012, 2, 0.040, 2, 5, 0.00],            # 2.胴作り
        [0.015, 0.015, 0.015, 0.015, 5, 0.030, 2, 0.04 ],            # 3.弓構え
        [0.006, 0.006, 1.000, 1.000, 5, None, None, None],           # 4.打起こし
        [0.009, 6, 0.015, 0.006, 1.000, 0.006, 1.000, 3, 0, 0.085],  # 5.引分け
        [0.006, 0.006, 0.006, 0.006, 5, 0.050, 0.00, None],          # 6.会
        [5, None, None, None, None, None, None, None],               # 7.離れ
        [0.080, 0.080, 3, None, None, None, None, None],             # 8.残心
        [25.0, 95.0, 0.030, 5, 0.085, None, None, None],             # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    }
]

# 初期登録用動作開始解析パラメータ
StartAction_params = [
    {'frame': '1.7-s',    # 約0.5秒
     'step': 0,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [1.000, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.035, 0.035, 3, None, None, None, None, None],             # 2.胴作り
        [0.025, 0.025, 5, None, None, None, None, None],             # 3.弓構え
        [1.000, 0.015, -45.0, 45.0, 9, None, None, None],            # 4.打起こし
        [0.006, 0.006, 0.006, 0.006, 3, 0.050, None, None],          # 5.引分け
        [0.050, 0.020, 8, None, None, None, None, None],             # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.050, 0.050, 3, None, None, None, None, None],             # 8.残心
        [0.085, 2, 0.085, 2, -45.0, 45.0, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },          
    {'frame': '1.7-s',    # 約0.5秒
     'step': 1,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [0.080, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.035, 0.035, 3, None, None, None, None, None],             # 2.胴作り
        [0.025, 0.025, 3, None, None, None, None, None],             # 3.弓構え
        [0.015, 0.015, -45.0, 45.0, 2, None, None, None],            # 4.打起こし
        [0.005, 0.005, 0.005, 0.005, 5, 0.050, None, None],          # 5.引分け
        [0.050, 0.020, 10, None, None, None, None, None],            # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.050, 0.050, 2,   None, None, None, None, None],           # 8.残心
        [0.085, 2, 0.085, 2, -45.0, 45.0, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },          
    {'frame': '1.7-s',    # 約0.5秒
     'step': 2,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [0.080, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.035, 0.035, 3, None, None, None, None, None],             # 2.胴作り
        [0.025, 0.025, 3, None, None, None, None, None],             # 3.弓構え
        [0.015, 0.015, -45.0, 45.0, 2, None, None, None],            # 4.打起こし
        [0.006, 0.006, 0.006, 0.006, 5, 0.050, None, None],          # 5.引分け
        [0.050, 0.020, 10, None, None, None, None, None],            # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.050, 0.050, 2,   None, None, None, None, None],           # 8.残心
        [0.085, 2, 0.085, 2, -45.0, 45.0, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },          
    {'frame': '1.7-s',    # 約0.5秒
     'step': 3,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [0.080, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.035, 0.035, 3, None, None, None, None, None],             # 2.胴作り
        [0.025, 0.025, 3, None, None, None, None, None],             # 3.弓構え
        [0.025, 0.025, -45.0, 45.0, 5, None, None, None],            # 4.打起こし
        [0.008, 0.008, 0.008, 0.008, 4, 0.050, None, None],          # 5.引分け
        [0.050, 0.020, 10, None, None, None, None, None],            # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.085, 0.085, 2, None, None, None, None, None],          # 8.残心
        [0.085, 2, 0.085, 2, -45.0, 45.0, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },          
    {'frame': '1.7-s',    # 約0.5秒
     'step': 9,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [1.000, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.035, 0.035, 3, None, None, None, None, None],             # 2.胴作り
        [0.025, 0.025, 5, None, None, None, None, None],             # 3.弓構え
        [1.000, 0.015, -45.0, 45.0, 9, None, None, None],            # 4.打起こし
        [0.006, 0.006, 0.006, 0.006, 3, 0.050, None, None],          # 5.引分け
        [0.050, 0.020, 8, None, None, None, None, None],             # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.050, 0.050, 3, None, None, None, None, None],             # 8.残心
        [0.085, 2, 0.085, 2, -45.0, 45.0, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },          
    {'frame': '1.7-m',    # 約0.5秒
     'step': 0,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [0.080, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.035, 0.035, 5, None, None, None, None, None],             # 2.胴作り
        [0.025, 0.025, 3, None, None, None, None, None],             # 3.弓構え
        [0.015, 0.015, -45.0, 45.0, 2, None, None, None],            # 4.打起こし
        [0.006, 0.006, 0.006, 0.006, 3, 0.050, None, None],          # 5.引分け
        [0.050, 0.020, 10, None, None, None, None, None],            # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.050, 0.050, 2,   None, None, None, None, None],           # 8.残心
        [0.085, 2, 0.085, 2, -45.0, 45.0, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },          
    {'frame': '1.7-m',    # 約0.5秒
     'step': 1,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [0.080, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.035, 0.035, 3, None, None, None, None, None],             # 2.胴作り
        [0.025, 0.025, 3, None, None, None, None, None],             # 3.弓構え
        [0.015, 0.015, -45.0, 45.0, 2, None, None, None],            # 4.打起こし
        [0.006, 0.006, 0.006, 0.006, 5, 0.050, None, None],          # 5.引分け
        [0.050, 0.020, 10, None, None, None, None, None],            # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.050, 0.050, 2,   None, None, None, None, None],           # 8.残心
        [0.085, 2, 0.085, 2, -45.0, 45.0, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },          
    {'frame': '1.7-m',    # 約0.5秒
     'step': 2,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [0.080, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.035, 0.035, 3, None, None, None, None, None],             # 2.胴作り
        [0.025, 0.025, 3, None, None, None, None, None],             # 3.弓構え
        [0.015, 0.015, -45.0, 45.0, 2, None, None, None],            # 4.打起こし
        [0.006, 0.006, 0.006, 0.006, 5, 0.050, None, None],          # 5.引分け
        [0.050, 0.020, 10, None, None, None, None, None],            # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.050, 0.050, 2,   None, None, None, None, None],           # 8.残心
        [0.085, 2, 0.085, 2, -45.0, 45.0, None, None],               # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    },
    {'frame': '1.7-m',    # 約0.5秒
     'step': 9,
     'act': 1,
     'param': [
        [0.120, 0.140, None, None, None, None, None, None],          # 0.
        [0.080, 2, None, None, None, None, None, None],              # 1.足踏み
        [0.035, 0.035, 5, None, None, None, None, None],             # 2.胴作り
        [0.025, 0.025, 3, None, None, None, None, None],             # 3.弓構え
        [0.015, 0.015, -45.0, 45.0, 2, None, None, None],            # 4.打起こし
        [0.006, 0.006, 0.006, 0.006, 3, 0.050, None, None],          # 5.引分け
        [0.050, 0.020, 10, None, None, None, None, None],            # 6.会
        [0.085, None, None, None, None, None, None, None],           # 7.離れ
        [0.050, 0.050, 2,   None, None, None, None, None],           # 8.残心
        [0.085, 2, 0.085, 2, -45.0, 45.0, None, None],                # 9.弓倒し
        [0.900, None, None, None, None, None, None, None]            #10.共通
     ]
    }              
]
#
# 体、顔の向きをエンコードする際の閾値設定
#
Body_front_threshold:float = 0.180      # 体の向きの閾値(tag2=1:正面,0:横)
#Face_front_threshold:float = 0.055     # 顔の向きの閾値(tag1=1:正面,2:横)
Face_front_threshold:float = 0.060      # 顔の向きの閾値(tag1=0:不定,1:正面,2:横)
Eyes_ratio_threshold:float = 0.0        # 目幅比率の閾値（補正しない場合は0.0に設定）
Eyes_ratio_max:float = 0.1              # 目幅比率の最大値
Eyes_ratio_min:float = 0.01             # 目幅比率の最小値
#
#
# アラートID、メッセージの定義
#
Alart_Asibumi= 10     # 「正対不完全」のアラートID
Alart_Monomi = 30     # 「物見を定まらず」のアラートID
Alart_Daisan = 40     # 「大三移行不安定」のアラートID
Alart_KaiNasi = 50    # 「会なし離れ」のアラートID
Alart_KaiFusoku = 60  # 「会不十分な離れ」のアラートID
Alart_Hanare = 70     # 「離れタイミングずれ」のアラートID
#
Alart_msg = {
   0:'',
   10:'Warning:Detected illegal action in section-1.(SEITAI fukanzen)',
   100:'<警告>：「正対不明確」を検知しました。',
   30:'Warning:Detected illegal action in section-3.(MONOMI sadamarazu)',
   300:'<警告>：「物見定まらず」を検知しました。',
   40:'Warning:Detected illegal action in section-5.(DAISAN fumeikaku)',
   400:'<警告>：「大三移行不安定」を検知しました。',
   50:'Warning:Detected illegal action in section-5.(KAI nasi)',
   500:'<警告>：「会なし離れ」を検知しました。',
   60:'Warning:Detected illegal action in section-6.(KAI fusoku)',
   600:'<警告>：「会不十分な離れ」を検知しました。',
   70:'Warning:Detected illegal action in section-7.(Timing un-match)',
   700:'<警告>：「弓手押しタイミングの遅れ」を検知しました。'
}
#
# 評価の減点条件のパラメータ定義
#
Diduct_params = {
    #  key_name: ( (operator, value, deduction_score), 'message.unit')
    's4_rl_angle': (('>',10.0, 1),  '矢の傾きが大きい.度'),         # 矢が水平でない場合に減点する
    's4_rl_angle': (('<',-10.0, 1), '矢の傾きが大きい.度'),         # 矢が水平でない場合に減点する
    's5_pull_rate': (('>',0.65, 2),   '引き優位.%'),               # 引きの割合がこの値を超える場合に減点する
    's6_split_tm': (('<',2.0, 2),   '会の保持時間が短い.秒'),       # 会の時間がこの値未満の場合に減点する
    's6_split_tm': (('<',1.0, 3),   '会の保持時間が短い.秒'),       # 会の時間がこの値未満の場合に減点する
    's8_split_tm': (('<',1.5, 2),   '残身の保持時間が短い.秒'),     # 残身の時間がこの値未満の場合に減点する
    's8_split_tm': (('<',1.0, 3),   '残身の保持時間が短い.秒'),     # 残身の時間がこの値未満の場合に減点する
    's8_sl_angle': (('>',5.0, 1),   '弓手の下がりが大きい.度')      # 弓手の下がりがこの値を超える場合に減点する
}
#
# eof
