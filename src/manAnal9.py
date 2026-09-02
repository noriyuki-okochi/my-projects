
# local package
from kyudo.appUtil import * 
#
mylog = logging.getLogger('__main__')
#
################################################################################################
# 射法八節（側面カメラ）用の関数
# セクションが開始したかどうかを判定する関数
#
def section_started_L9(section_no, myResult:MyResult):
    
    keyPoints = myResult                            # キーポイントのデータ解析インスタンス
    ibox = myResult.boxid
    
    thsd = Threshold(keyPoints.block_height)        # バウンディングボックスの高さを基準に閾値設定インスタンス
    
    # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
    arrow = myResult.arrow_length_angles[Sample_lag]

    xy_wristR = keyPoints.xy('right_wrist')                             # 右手首の座標
    xy_elbow = keyPoints.xy('right_elbow')                  # 右肘の座標

    normR, anglR = arrow[Kn2idx['right_wrist']]                         # 右手首の移動ベクトルの長さと角度
    normK, _ = arrow[Kn2idx['right_knee']]                              # 右膝の移動ベクトルの長さと角度
    normR, anglR = arrow[Kn2idx['right_wrist']]                         # 右手首の移動ベクトルの長さと角度
    lenSW, anglSW = keyPoints.norm('right_shoulder', 'right_wrist')     # 右肩と右手首のベクトルの長さと角度を計算
    _, anglSE_ = keyPoints.norm('right_shoulder', 'right_elbow')        # 右肩と右肘のベクトルの長さと角度を計算
    _, anglEW_ = keyPoints.norm('right_elbow', 'right_wrist')           # 右肘と右手首のベクトルの長さと角度を計算

    started = False
    # 共通の開始条件を取得
    PRM = StartAction_param['param'][10]                                # 10は共通の開始条件     
    conf = keyPoints.conf('right_wrist')                                # 右手首の座標の信頼度
    confRY = keyPoints.conf('right_eye')                                # 右目の座標の信頼度
    
    if conf < PRM[0] and (section_no > 0 and section_no < 8):
        # 右手首の信頼度が低い
        mylog.log(INFO, f"started({section_no}): right-wrist-conf={conf:.2f}({PRM[0]:.2f}), "\
                      + f" skip....")
        return started

    mylog.log(INFO, f"started ({section_no}):フレーム={g.Frame_counter}:    counter={g.Step_counter}\n"\
            + f"    boxid={ibox}, H={int(thsd.block_height)}:  wristR=[{int(xy_wristR[0])}, {int(xy_wristR[1])}],"\
            + f"    normR={int(normR)}({thsd.ratio(normR):.3f}), anglR={int(anglR)}°,  conf={conf:.2f}")
    mylog.log(INFO, f"    lenSW={int(lenSW)}({thsd.ratio(lenSW):.3f}), anglSW={int(anglSW)}°,"\
                    f" anglSE={int(anglSE_)}°, anglEW={int(anglEW_)}°, xy_elbow=[{int(xy_elbow[0])}, {int(xy_elbow[1])}]")
    #
    # 次の節への移行条件を判定
    #
    # セクションごとの開始条件を取得
    PRM = StartAction_param['param'][section_no]  
    # 0-Start  ->  1-Asi-bumi
    if section_no == 0:    
        lenS, _ = keyPoints.norm('left_shoulder', 'right_shoulder')          # 右肩と左肩のベクトルの長さと角度を計算
        mylog.log(INFO, f">>>   lenS={int(lenS)}({thsd.ratio(lenS):.3f})")
        mylog.log(INFO, f">>>   [ lenS < {int(thsd(PRM[0]))} ]")

        Stkp.push([ (0,PRM[0]) ])  
        if lenS < thsd(PRM[0]) :
            # 右肩と左肩のベクトルの長さが80未満
            started = True
            
    # 1-Asi-bumi  ->  2-Dou-zukuri        
    elif section_no == 1:  
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} and anglR < {int(PRM[1])} and y_wristR < y_elbow ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,int(PRM[2]))] )  
        if normR > thsd(PRM[0]) and int(anglR) < int(PRM[1])  and  xy_wristR[1] < xy_elbow[1]:
            # 右手首の移動ベクトルの長さが50以上の場合（矢つがえ動作開始）
            g.Step_counter += 1
            if g.Step_counter == PRM[2]: started = True

    # 2-Dou-zukuri  ->  3-Yu-gamae        
    elif section_no == 2:  
        if g.Step_counter == 0:
            # 初期値設定（弦調べ）
            g.Step_counter = 30
        if g.Step_counter >= 30:
            #mylog.log(INFO, f">>>   [ confRY < {(PRM[0]):.2f} ]")
            #Stkp.push( [(3,PRM[3])] )  
            if confRY < PRM[3]:  
                # 箆調べ
                g.Step_counter = 40
            
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} and anglR < {int(PRM[1])} ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,int(PRM[2]))] )  
        if normR > thsd(PRM[0]) and int(anglR) < int(PRM[1]):
            # 右手首の移動ベクトルの長さが大きい場合（取りかけ動作開始）
            g.Step_counter += 1
            if (g.Step_counter%10) == PRM[2]: started = True

    # 3-Yu-gamae  ->  4-Uti-okosshi        
    elif section_no == 3:  
        if g.Step_counter == 0:
            # 初期値設定（物見）
            g.Step_counter = 11
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} and anglR < {int(PRM[1])} ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,int(PRM[2]))] )  
        if normR > thsd(PRM[0]) and int(anglR) < int(PRM[1]):
            # 右手首の移動ベクトルの長さが大きい場合（打ちお越し動作開始）
            g.Step_counter += 1
            if (g.Step_counter%10) == PRM[2] + 1: started = True

    # 4-Uti-okosshi  ->  5-Hiki-wake        
    elif section_no == 4:  
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} and (anglR > {int(PRM[1])} or anglR < {int(PRM[2])}) ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3])] )  
        if  normR > thsd(PRM[0]) and (int(anglR) > int(PRM[1]) or int(anglR) < int(PRM[2])):
            # 右手首の移動ベクトルの長さ大の場合（引分け大三への動作開始）
            g.Step_counter += 1
            if g.Step_counter == PRM[3]:   started = True
        
    # 5-Hiki-wake  ->  6-Kai        
    elif section_no == 5:  
        normE, _ = arrow[Kn2idx['right_elbow']]                    # 右肘の移動ベクトルの長さと角度

        mylog.log(INFO, f">>>   normE={int(normE)}({thsd.ratio(normE):.3f})")
        mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[0]))} and normE < {int(thsd(PRM[1]))} ]")
        
        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3]), (4,PRM[4])] )  
        if normR < thsd(PRM[0]) and normE < thsd(PRM[1])  :
            # 右手首の移動ベクトルの長さが10以下の場合（引分けの完了）
            g.Step_counter = g.Step_counter + 1
            if g.Step_counter == PRM[2]: 
                started = True    #  停止状態のN回保持で完了
            else:
                mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[3]))} and anglR < {int(PRM[4])} ]")
                if normR > thsd(PRM[3]) and anglR < int(PRM[4]):
                    # 右手首の移動ベクトルの長さが大きい（会なしで離れ）
                    g.Step_counter += 90              # 離れアラート設定（仮）

    # 6-Kai  ->  7-Hanare        
    elif section_no == 6:  
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} and (anglR > {int(PRM[1])} or anglR < {int(PRM[2])}]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2])] )  
        if normR > thsd(PRM[0]) and (anglR > int(PRM[1]) or anglR < int(PRM[2])): 
            # 右手首の移動ベクトルの長さが大きい
            started = True
    
    
    # 7-Hanare  ->  8-Zan-shin        
    elif section_no == 7:  
        g.Step_counter = g.Step_counter + 1
        mylog.log(INFO, f">>>   [ counter == {int(PRM[0])} ]")
        
        if g.Step_counter == PRM[0]: 
            #  N回の遅延後、次節に移行
            started = True             

    # 8-Zan-shin  ->  9-''(弓倒し)
    elif section_no == 8:  
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} and anglR > {int(PRM[1])} ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (1,PRM[2])] )  
        if normR > thsd(PRM[0]) and anglR > thsd(PRM[1]):
            # 右手首と左手首の移動ベクトルの長さが大きい場合（弓だおし開始）
            g.Step_counter += 1
            mylog.log(INFO, f">>>   [ counter == {int(PRM[2])} ]")

            if g.Step_counter == PRM[2]:
                started = True

    # 9-''(弓倒し)  ->  0-Start
    elif section_no == 9:  
        mylog.log(INFO, f">>>   normK={int(normK)}({thsd.ratio(normK):.3f})")
        mylog.log(INFO, f">>>   [ normK > {int(thsd(PRM[2]))} ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2])] )  
        if normK > thsd(PRM[2]):
            # 右膝の移動ベクトルの長さが大きい場合（退場開始）
            g.Step_counter = 22
            started = True
        else:
            mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} ]")
            if normR > thsd(PRM[0]):
                # 右手首の移動ベクトルの長さが大きい場合（矢つがえ開始）
                g.Step_counter += 1
                mylog.log(INFO, f">>>   [ counter == {int(PRM[1])} ]")

                if (g.Step_counter%10) == PRM[1]:
                    g.Step_counter = 30 
                    started = True

    #        
    # other section_no
    else:
        mylog.log(ERROR, f">>> section_no={section_no}は未定義のセクションです")
        started = False
    #
    mylog.log(INFO, f">>>   started({section_no}): started={started}")
    return started
# 
# 射法八節解析（側面カメラ）用の関数
#セクションが完了したかどうかを判定する関数
# 
def section_completed_L9(section_no, myResult:MyResult):
     
    keyPoints = myResult                            # キーポイントのデータ解析インスタンス
    ibox = myResult.boxid
    
    thsd = Threshold(keyPoints.block_height)        # バウンディングボックスの高さを基準に閾値設定インスタンス

    # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
    arrow = myResult.arrow_length_angles[Sample_lag]  
    
    xy_wristR = keyPoints.xy('right_wrist')                             # 右手首の座標
    xy_elbow = keyPoints.xy('right_elbow')                              # 右肘の座標
    xy_nose = keyPoints.xy('nose')                                      # 鼻の座標

    normR, anglR = arrow[Kn2idx['right_wrist']]                         # 右手首の移動ベクトルの長さと角度
    normE, _ = arrow[Kn2idx['right_elbow']]                             # 右肘の移動ベクトルの長さと角度
    normS, _ = arrow[Kn2idx['right_shoulder']]                          # 右肩の移動ベクトルの長さと角度
    lenSW, anglSW = keyPoints.norm('right_shoulder', 'right_wrist')     # 右肩と右手首のベクトルの長さと角度を計算
    _, anglSE = keyPoints.norm('right_shoulder', 'right_elbow')        # 右肩と右肘のベクトルの長さと角度を計算
    _, anglEW = keyPoints.norm('right_elbow', 'right_wrist')           # 右肘と右手首のベクトルの長さと角度を計算

    completed = False
    # 共通の開始条件を取得
    PRM = CompleteAction_param['param'][10]    # 10は共通の開始条件 
    conf = keyPoints.conf('right_wrist')                                # 右手首の座標の信頼度
    confRY = keyPoints.conf('right_eye')                                # 右目の座標の信頼度

    if conf < PRM[0]  and (section_no > 1 and section_no < 9):
        # 右手首の信頼度が低い
        mylog.log(INFO, f"completed({section_no}): right-wrist-conf={conf:.2f}({PRM[0]:.2f}), "\
                      + f" skip....")
        return completed

    mylog.log(INFO, f"completed({section_no}):フレーム={g.Frame_counter}:   counter={g.Step_counter}\n"\
            + f"    boxid={ibox}, H={int(thsd.block_height)}, wristR=[{int(xy_wristR[0])}, {int(xy_wristR[1])}],"\
            + f"    normR={int(normR)}({thsd.ratio(normR):.3f}), anglR={int(anglR)}°, conf={conf:.2f}")
    mylog.log(INFO, f"    lenSW={int(lenSW)}({thsd.ratio(lenSW):.3f}), anglSW={int(anglSW)}°,"\
                  + f" anglSE={int(anglSE)}°, anglEW={int(anglEW)}°,"\
                  + f" anglSE={int(anglSE)}°, anglEW={int(anglEW)}°\n"\
                  + f"    xy_elbow=[{int(xy_elbow[0])}, {int(xy_elbow[1])}], confRY={confRY:.2f}")
    
    #
    # 節の動作完了（次節への移行体制）条件を判定
    #    
    # セクションごとの開始条件を取得
    PRM = CompleteAction_param['param'][section_no]  
    # 1-Asi-bumi
    if section_no == 1:  
        normS, _ = arrow[Kn2idx['right_shoulder']]              # 右肩の移動ベクトルの長さと角度
        normE, _ = arrow[Kn2idx['right_elbow']]                 # 右肘の移動ベクトルの長さと角度
        mylog.log(INFO, f">>>   "\
                        + f" normS={int(normS)}({thsd.ratio(normS):.3f}), normE={int(normE)}({thsd.ratio(normE):.3f})") 

        mylog.log(INFO, f">>>   [ (normR <= {int(thsd(PRM[0]))} and normS <= {int(thsd(PRM[1]))} and normE <= {int(thsd(PRM[2]))}) and"\
                    + f"  (anglSW >= {int(PRM[3])} and anglSW <= {int(PRM[4])}) and confRY > {PRM[5]:.2f} ]")
        
        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3]), (4,PRM[4]), (5,PRM[5]), (6,PRM[6])] )  
        if (normR <= thsd(PRM[0]) and normS <= thsd(PRM[1]) and normE <= thsd(PRM[2])) and\
           (anglSW >= PRM[3] and anglSW <= PRM[4]) and confRY > PRM[5]:
            # 右手首、右肩、右腰の移動が小さく、右肩から右手首のベクトルの角度が下向き垂直に近く、
            # 右目検出信頼度が高い場合（足踏み動作完了）
            g.Step_counter += 1
            if (g.Step_counter%10) == PRM[6]: completed = True
    # 2-Dou-zukuri            
    elif section_no == 2:  
        if g.Step_counter == 0: g.Step_counter = 1  # 初期化（矢番え動作開始）

        if g.Step_counter >= 10 and g.Step_counter < 20:
            mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[5]))} and anglR < {int(PRM[6])}]")
            
            Stkp.push( [(5,PRM[5]), (6,PRM[6]), (7,PRM[7])] )  
            if normR > thsd(PRM[5]) and int(anglR) < int(PRM[6]): 
                # 右手首の移動ベクトルの長さが大きい場合（取り矢動作開始）
                g.Step_counter += 1
                if (g.Step_counter%10) == PRM[7]: g.Step_counter = 20 
            else:
                g.Step_counter = int(g.Step_counter/10)*10  # 連続回数をリセット    
        else:
            mylog.log(INFO, f">>>   [ (normR <= {int(thsd(PRM[0]))} and (anglSW >= {int(PRM[1])} and anglSW <= {int(PRM[2])}) ]")
            
            Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3]), (4,PRM[4])] )  
            if ( normR <= thsd(PRM[0])  and (anglSW >= PRM[1] and anglSW <= PRM[2]) ):
                # 右手首の移動が小さく、右肩から右手首のベクトルの角度が下向き垂直に近い場合（馬手を腰に置く動作完了）
                g.Step_counter += 1
                if g.Step_counter < 10:
                    # 右手首と左手首の移動ベクトルの長さが10未満の場合（矢つがえ動作完了）
                    mylog.log(INFO, f">>>   [ counter == {int(PRM[3])} ]")
                    
                    if g.Step_counter == PRM[3]: g.Step_counter = 10            #(N-1)回保持（初期値=1に注意）
                elif g.Step_counter >= 20:
                    # 右手首と左手首の移動ベクトルの長さが10未満の場合（胴作り完了）
                    mylog.log(INFO, f">>>   [ counter == {int(PRM[4])} ]")
                    
                    if (g.Step_counter%10) == PRM[4]: completed = True          #N回保持
            else:
                g.Step_counter = int(g.Step_counter/10)*10 + 1 # 連続回数をリセット
        #
                        
    # 3-Yu-gamae            
    elif section_no == 3:  
        if g.Step_counter == 0:
            # 初期値設定（取掛け・手の内）
            g.Step_counter = 10
            
        mylog.log(INFO, f">>>   [ confRY < {(PRM[0]):.2f} ]")
        
        Stkp.push( [(0,PRM[0]), (0,PRM[1]), (2,PRM[2])] )  
        if confRY < PRM[0]:  
            # 物見を定める
            g.Step_counter = g.Step_counter + 1
            mylog.log(INFO, f">>>   [ counter == {int(PRM[1])} ]")
            if g.Step_counter%10 >= PRM[1]: 
                completed = True   # 
            else:
                mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[2]))} ]")
                if normR > thsd(PRM[2]):
                    # 右手首の移動ベクトルの長さが大きい（物見なしで打ちおこし）
                    g.Alart_id = Alart_Monomi
                    g.Step_error = True
                
    # 4-Uti-okosshi        
    elif section_no == 4:
        if g.Step_counter < 10:  
            mylog.log(INFO, f">>>   y_wristR={int(xy_wristR[1])}, y_nose={int(xy_nose[1])}")
            mylog.log(INFO, f">>>   [ y_wristR < y_nose ]")
            if xy_wristR[1] < xy_nose[1] :
                # （右手首と左手首が鼻より高い位置（Y軸は下方が正）
                g.Step_counter = 10
        else:
            mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[0]))} and anglSW < {int(PRM[1])} ]")

            Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2])] )  
            if normR < thsd(PRM[0]) and anglSW < int(PRM[1]):
                # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満
                g.Step_counter = g.Step_counter + 1
                if (g.Step_counter%10) == PRM[2]: completed = True   # N回保持で完了                
    
    # 5-Hiki-wake        
    elif section_no == 5:  
        xy_shouder = keyPoints.xy('right_shoulder')                # 右腰の座標
        mylog.log(INFO, f">>>   y_nose={int(xy_nose[1])}, y_wristR={int(xy_wristR[1])}, y_shouler={int(xy_shouder[1])}")

        mylog.log(INFO, f">>>   [ y_wristR > y_nose and y_wristR < y_shouler]")
        if  xy_wristR[1] > xy_nose[1] and xy_wristR[1] < xy_shouder[1] :
            # 右手首が鼻より低く、右肩より高い位置（Y軸は下方が正）
            if g.Step_counter < 20: g.Step_counter = 20

            mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[0]))} ]")

            Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2])] )  
            if normR < thsd(PRM[0])  :
                # 右手首の移動ベクトルが小（姿勢の保持で完了）
                g.Step_counter = g.Step_counter + 1
                if (g.Step_counter%10) == PRM[1]:  completed = True
            else:
                pass
                '''
                
                # 右手首の移動ベクトルの長さが大きい（会なしで離れ）
                mylog.log(INFO, f">>>   [ (g.Step_counter%10) > {PRM[8]} and (normR > {int(thsd(PRM[9]))}) ]")
                Stkp.push( [(8,PRM[8]), (9,PRM[9])] )  
                if (g.Step_counter%10) > PRM[8] and normR > thsd(PRM[9]):
                    g.Step_counter = 90 + g.Step_counter%10         # 離れアラート設定（仮）
                '''
    # 6-Kai            
    elif section_no == 6:  
        normE, _ = arrow[Kn2idx['right_elbow']]                    # 右肘の移動ベクトルの長さと角度

        mylog.log(INFO, f">>>   normE={int(normE)}({thsd.ratio(normE):.3f})")
        mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[0]))} and normE < {int(thsd(PRM[1]))} ]")
        
        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3]), (4,PRM[4])] )  
        if normR < thsd(PRM[0]) and normE < thsd(PRM[1])  :
            # 右手首、右肘の移動ベクトルの長さが小場合（会の完了）
            g.Step_counter = g.Step_counter + 1
            mylog.log(INFO, f">>>   [ counter == {int(PRM[2])} ]")

            if g.Step_counter == PRM[2]: completed = True    #  停止状態のN回保持で完了
            else:
                mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[3]))} and anglR < {int(PRM[4])} ]")
                if normR > thsd(PRM[3]) and anglR < int(PRM[4]):
                    # 右手首の移動ベクトルの長さが大きい（会なしで離れ）
                    g.Step_counter += 90              # 離れアラート設定（仮）

    # 7-Hanare        
    elif section_no == 7:          
        g.Step_counter = g.Step_counter + 1
        mylog.log(INFO, f">>>   [ counter > {int(PRM[0])} ]")

        Stkp.push( [(0,PRM[0])] )  
        if g.Step_counter > PRM[0]: 
            completed = True

    # 8-Zan-shin    
    elif section_no == 8:  
        mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[0]))} ]")
        Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
        if normR < thsd(PRM[0]) :
            # 右手首と左手首の移動ベクトルの長さが50以下の場合（姿勢の保持で完了）
            g.Step_counter = g.Step_counter + 1
            mylog.log(INFO, f">>>   [ counter == {int(PRM[1])} ]")

            if g.Step_counter == PRM[1]:  
                completed = True

    elif section_no == 9:  
        if g.Step_counter == 0:
            # 初期値に１を設定 
            g.Step_counter = 1
        if g.Step_counter != 22:    # 22：「退場」
            # 「弓倒し」の完了判定 
            mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[0]))} and anglEW > {int(PRM[1])} ]")

            Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2])] )  
            if normR < thsd(PRM[0]) and int(anglEW) > int(PRM[1]):
                g.Step_counter += 1
                mylog.log(INFO, f">>>   [ counter == {int(PRM[2])} ]")

                if (g.Step_counter%10) == PRM[2] + 1:
                    g.Step_counter = 20
                    completed = True
    #
    # other section_no            
    else:
        mylog.log(ERROR, f">>>  section_no={section_no}は未定義のセクションです")
        completed = False
    
    mylog.log(INFO, f">>>   completed({section_no}): completed={completed}")      
    return completed

# 射法八節解析（側面カメラ）用の関数
# 動作の開始を判定する関数
#
def manual_analize_start_L9(section_no, myResult:MyResult):    
    if section_started_L9(section_no, myResult):
        print(f"[man_analize]: section({section_no}), strated=True")
        g.Action_start = g.Lap_sec
        g.Split_start = g.Frame_counter                     # スプリット開始時間を記録
        if g.Section_no == 6: g.Split_last = g.Split_sec    # 「会」スプリット秒を記録
        g.Split_sec = 0.0

        g.Nop_counter = 0                                   # セクション内の動作が完了しない場合のカウンター
        g.Completed = False                                 # セクションが開始されたら完了フラグをリセット    
        if g.Section_no == 9:
            g.Section_no = 2 if g.Step_counter == 30 else 9
        else:
            g.Step_counter = 0                              # セクション内の動作カウンター
            g.Section_no += 1                               # セクション番号をインクリメント

    return g.Section_no, g.Completed  
#    
# 射法八節解析（側面カメラ）用の関数
# 動作の完了を判定する関数
#
def manual_analize_completed_L9(section_no, myResult:MyResult):    
    if section_completed_L9(section_no, myResult):
        print(f"[man_analize]: section({section_no}), completed=True")
        g.Action_start = g.Lap_sec
        g.Split_start = g.Frame_counter                      # スプリット開始時間を記録
        g.Completed = True 
        g.Step_counter = 0                                   # セクション内の動作カウンター
    else:
        g.Nop_counter += 1
        if g.Step_error:
            # セクション内の動作が不正な場合
            g.Alart_section = g.Section_no
            mylog.log(INFO, f"[man_analize_completed]: g.Step_error={g.Step_error}, g.Alart_id={g.Alart_id}")
            if g.Alart_id == Alart_Asibumi: g.Section_no = 2        # 足踏み不完全で矢番えの場合
            if g.Alart_id == Alart_Monomi: g.Section_no = 4         # 物見なしで打ちおこしの場合
            if g.Alart_id == Alart_KaiNasi: g.Section_no = 7        # 会なしで離れた場合
            if g.Alart_id == Alart_KaiFusoku: g.Section_no = 7      # 会不十分で離れた場合
            if g.Alart_id != Alart_Daisan:                        # 大三不安定の場合、リセットしない
                g.Step_counter = 0
                g.Nop_counter = 0
         
    return g.Section_no, g.Completed  

# eof