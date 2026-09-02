import numpy as np
import pandas as pd
from kyudo.kyudoUtils import *

mylog = logging.getLogger('__main__')
#
# ハイブリッドモデルの場合、動作予測結果を補正（正面カメラ対応）
#
def correct_action_by_rules(action, section, completed):
    
    r_action = action
    if completed == True and action == 1:
        # 「動作完了」で「動作完了」が認識された場合、
        r_action = 0
    elif completed == False and action == 2:
        # 「動作未完了」で「動作開始」が認識された場合、
        r_action = 0
    elif g.Hybrid_model == True:
        # 動作解析ステップに応じた補正ルール
        if section == 1:        # 「足踏み」
            if action == 1 and g.Step_counter < 13:   # 動作完了が早すぎる
                r_action = 0
        if section == 2:        # 「胴づくり」
            if action == 1 and g.Step_counter < 21:   # 動作完了が早すぎる（一回目の腰）
                r_action = 0
            if action == 1 and g.RSE_angle < 120.0:   # 動作完了が早すぎる（肩肘の角度が不十分）
                r_action = 0
            if action == 1 and g.ER_angle < 0.0:      # 動作完了が早すぎる（肘手首の角度が不十分）
                r_action = 0
            if action == 1 and g.SL_angle > 70.0:     # 動作完了が早すぎる（左腕の角度が不十分）
                r_action = 0
            if action == 2 and g.Step_counter < 50:   # 動作開始が早すぎる
                r_action = 0
        elif section == 3:      # 「弓構え」
            if action == 2 and g.Step_counter < 12:   # 動作開始が早すぎる
                r_action = 0
        elif section == 4:      # 「打起し」
            if action == 1 and g.Step_counter < 11:   # 動作完了が早すぎる
                r_action = 0
            if action == 2 and g.Step_counter < 1:    # 動作開始が早すぎる
                r_action = 0
        elif section == 5:      # 「引き分け」
            if action == 2 and g.Step_counter < 2:    # 動作開始が早すぎる
                r_action = 0
        elif section == 6:      # 「会」
            if action == 2 and g.ER_angle > -90.0:    # 動作開始が早すぎる
                r_action = 0
        elif section == 8:      # 「残心」
            if action == 2 and g.Step_counter < 1:    # 動作開始が早すぎる
                r_action = 0
        elif section == 9:      # 「弓倒し」
            #if action == 1 and g.Step_counter < 2:    # 動作完了が早すぎる
            #    r_action = 0
            if action == 2 and g.Step_counter < 11:   # 動作開始が早すぎる
                r_action = 0
            if action == 2 and g.HR_angle > -90.0:    # 動作開始が早すぎる
                r_action = 0
    #
    if r_action != action:
        mylog.log(INFO, f"[correct_by_rules]: action {action} corrected to {r_action}")
        print(f"[correct_by_rules]: action {action} corrected to {r_action}")
    return r_action
#
#
# ハイブリッドモデルの場合、動作予測結果を補正（側面カメラ対応）
#
def correct_action_by_rules9(action, section, completed):
    r_action = action
    if completed == True and action == 1:
        # 「動作完了」で「動作完了」が認識された場合、
        r_action = 0
    elif completed == False and action == 2:
        # 「動作未完了」で「動作開始」が認識された場合、
        r_action = 0
    elif g.Hybrid_model == True:
        # 動作解析ステップに応じた補正ルール
        if section == 1:        # 「足踏み」
            if action == 2 and g.ER_angle > 10:             # 動作開始が早すぎる
                r_action = 0
        if section == 2:        # 「胴づくり」
            if action == 1 and g.Step_counter < 23:         # 動作完了が早すぎる（一回目の腰）
                r_action = 0
            if action == 1 and g.Step_counter == 31:        # 動作完了が早すぎる（乙矢の腰）
                r_action = 0
        elif section == 3:      # 「弓構え」
            if action == 2 and g.Step_counter < 12:         # 動作開始が早すぎる
                r_action = 0
        elif section == 4:      # 「打起し」
            if action == 1 and g.Step_counter < 11:         # 動作完了が早すぎる
                r_action = 0
            if action == 2 and g.Step_counter < 1:          # 動作開始が早すぎる
                r_action = 0
        elif section == 5:      # 「引き分け」
            if action == 1 and g.Step_counter < 20:         # 動作完了が早すぎる
                r_action = 0
        elif section == 6:      # 「会」
            if action == 2 and g.ER_angle < -40.0:          # 動作開始が早すぎる
                r_action = 0
        elif section == 8:      # 「残心」
            if action == 1 and g.Step_counter < 2:         # 動作完了が早すぎる
                r_action = 0
        elif section == 9:      # 「弓倒し」
            if action == 1 and g.Step_counter < 2:          # 動作完了が早すぎる
                r_action = 0
    #
    if r_action != action:
        mylog.log(INFO, f"[correct_by_rules9]: action {action} corrected to {r_action}")
        print(f"[correct_by_rules9]: action {action} corrected to {r_action}")
    return  r_action           
#
# GRUモデルによる動作予測関数
#
def gru_analize(section, completed, model, input_pdf:pd.DataFrame, level:int=0):
    
    mylog.log(DEBUG, f"[gru_analize]: input_pdf.shape={input_pdf.shape}")
    mylog.log(DEBUG, f"[gru_analize]: {input_pdf.tail()}")
   
    x = input_pdf.to_numpy(dtype=np.float32)
    s_frames = len(input_pdf)
    
    # GRUモデルによる動作解析
    y = predict_Kyudo( model, x, s_frames, log_print=False )
    mylog.log(DEBUG, f"[gru_analize]: y.shape={y.shape}")
    action = y[0]
    if action != 0:
        if g.Hybrid_model == True:
            mylog.log(INFO, f"[gru_analize]: not zero action={action} ( section={section}, completed={completed}, counter={g.Step_counter} )")
        # ハイブリッドモデルの場合、動作認識結果を補正
        action = correct_action_by_rules(action, section, completed) if level != 9 \
                else correct_action_by_rules9(action, section, completed)
                
    # タイマー情報の更新
    if action == 2:
        g.Action_start = g.Lap_sec
        g.Split_start = g.Frame_counter                         # スプリット開始時間を記録
        if section == 6: g.Split_last = g.Split_sec             # 「会」スプリット秒を記録
        g.Split_sec = 0.0
    elif action == 1:
        g.Action_start = g.Lap_sec
        #if section != 6 and section != 8:                   # 「会」、「残身」はスプリットを計測
        #    g.Split_start = 0                                 # スプリット開始時間をリセット
        g.Split_start = g.Frame_counter                         # スプリット開始時間を記録
        if section == 9 and g.Step_counter == 0:              # 退場動作の場合、解析終了 
            g.Lap_start = 0
    #
    ival = 1 if completed == True else 0
    rslt = update_section_completed(action, section, ival, output_size=model.output_size)
    if action != 0:
        mylog.log(INFO, f"[gru_analize]: フレーム={g.Frame_counter}")
        if action == 1:
            mylog.log(INFO, f"[gru_analize]: section({section}), completed=True")
            print(f"[gru_analize]: section({section}), completed=True")
        else:
            mylog.log(INFO, f"[gru_analize]: section({section}), strated=True")
            print(f"[gru_analize]: section({section}), strated=True")
        mylog.log(INFO, f"[gru_analize]: section={rslt[0]}, completed={rslt[1]}")
        #
        if section == 9 and action == 2: g.Step_counter = 30
        else: g.Step_counter = 0
    #
    return rslt[0], (True if rslt[1] == 1 else False), action
#
# eof