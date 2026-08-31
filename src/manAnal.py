
# local package
from kyudo.appUtil import * 

mylog = logging.getLogger('__main__')
##########################################################################################
# 射法八節解析（正面カメラ）用の関数
# 次のセクションが開始したかどうかを判定する関数
#
def section_started(section_no, myResult:MyResult):
    global Stkp
        
    keyPoints = myResult                            # キーポイントのデータ解析インスタンス
    ibox = myResult.boxid
    
    thsd = Threshold(keyPoints.block_height)        # バウンディングボックスの高さを基準に閾値設定インスタンス
    
    # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
    arrow = myResult.arrow_length_angles[Sample_lag]

    normR, anglR = arrow[Kn2idx['right_wrist']]                     # 右手首の移動ベクトルの長さと角度
    normL, anglL = arrow[Kn2idx['left_wrist']]                      # 左手首の移動ベクトルの長さと角度
    normS, _ = arrow[Kn2idx['right_shoulder']]                      # 右肩の移動ベクトルの長さと角度
    xy_wristR = keyPoints.xy('right_wrist')                         # 右手首の座標

    started = False
    # 共通の開始条件を取得
    PRM = StartAction_param['param'][10]        # 10は共通の開始条件     
    conf = keyPoints.conf('right_wrist')                            # 右手首の座標の信頼度
    
    if conf < PRM[0] and (section_no > 0 and section_no < 8):
        # 右手首の信頼度が低い
        mylog.log(INFO, f"started({section_no}): right-wrist-conf={conf:.2f}({PRM[0]:.2f}), "\
                      + f" skip....")
        return started

    mylog.log(INFO, f"started ({section_no}):フレーム={g.Frame_counter}\n"\
            + f"    boxid={ibox}, H={int(thsd.block_height)}:  wristR=[{int(xy_wristR[0])}, {int(xy_wristR[1])}],"\
            + f"    normR={int(normR)}({thsd.ratio(normR):.3f}), anglR={int(anglR)}°, anglRL={int(g.RL_angle)}°, conf={conf:.2f}, counter={g.Step_counter}")
    #
    # 次の節への移行条件を判定
    #
    # セクションごとの開始条件を取得
    PRM = StartAction_param['param'][section_no]  
    # 0-Start  ->  1-Asi-bumi
    if section_no == 0:    
        lenS, _ = keyPoints.norm('left_shoulder', 'right_shoulder')          # 右肩と左肩のベクトルの長さと角度を計算
        mylog.log(INFO, f">>>   lenS={int(lenS)}({thsd.ratio(lenS):.3f}), normS={(int(normS))}({thsd.ratio(normS):.3f})")
        mylog.log(INFO, f">>>   [ lenS < {int(thsd(PRM[0]))} and normS > {int(thsd(PRM[1]))} ]")

        Stkp.push([ (0,PRM[0]), (1,PRM[1]) ])  
        if lenS < thsd(PRM[0]) and  normS > thsd(PRM[1]):
            # 右肩と左肩のベクトルの長さが80未満、右肩の移動ベクトルの長さが50以上の場合（射位へ移動）
            started = True
    
    # 1-Asi-bumi  ->  2-Dou-zukuri        
    elif section_no == 1:  
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
        if normR > thsd(PRM[0]):
            # 右手首の移動ベクトルの長さが50以上の場合（矢つがえ動作開始）
            g.Step_counter += 1
            if g.Step_counter == PRM[1]: started = True
    
    # 2-Dou-zukuri  ->  3-Yu-gamae        
    elif section_no == 2:  
        if g.Step_counter == 0: g.Step_counter = 30 # 初期化（弦調べ）

        lenY, _ = keyPoints.norm('right_eye', 'left_eye')         # 右目と左目のベクトルの長さと角度を計算       
        mylog.log(INFO, f">>>   lenY={int(lenY)}({thsd.ratio(lenY):.3f})")
        if thsd.ratio(lenY) > 1.0:
            mylog.log(INFO, f"started({section_no}): lenY.ratio={thsd.ratio(lenY):.3f}, "\
                      + f" skip....")
            return started   # 目の間隔が異常に広い場合、開始判定しない

        if g.Step_counter == 30:
            mylog.log(INFO, f">>>   lenY < {int(thsd(PRM[0]))})")
            if lenY < thsd(PRM[0]) :
                # 目の間隔が狭くなる（箆調べ）
                g.Step_counter = 40        
        if g.Step_counter == 40:
            mylog.log(INFO, f">>>   lenY > {int(thsd(PRM[0]))})")
            if lenY > thsd(PRM[0]):
                # 箆調べからの戻り
                g.Step_counter = 50
        '''            
        mylog.log(INFO, f">>>   [ lenY > {int(thsd(PRM[0]))} and normR > {int(thsd(PRM[1]))} ]")
        Stkp.push( [(0,PRM[0]),(1,PRM[1]), (2,PRM[2])] )  
        if lenY > thsd(PRM[0]) and normR > thsd(PRM[1]):
        '''
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[1]))} ]")
        Stkp.push( [(1,PRM[1]), (2,PRM[2])] )  
        if normR > thsd(PRM[1]):
            # 右手首の移動ベクトルの長さが10以上の場合（取りかけ動作開始）
            g.Step_counter += 1
            if (g.Step_counter%10) == PRM[2]: started = True
        else: g.Step_counter = int(g.Step_counter/10)*10
    
    # 3-Yu-gamae  ->  4-Uti-okosshi        
    elif section_no == 3:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} and normL > {int(thsd(PRM[1]))} ]")

        if g.Step_counter == 0: g.Step_counter = 11 # 初期化（物見が定まる）
        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2])] )  
        if normR > thsd(PRM[0]) and normL > thsd(PRM[1]):
            # 右手首と左手首の移動ベクトルの長さが10以上の場合（打起し動作開始）
            g.Step_counter += 1
            if (g.Step_counter%10) == PRM[2]:   started = True
    
    # 4-Uti-okosshi  ->  5-Hiki-wake        
    elif section_no == 4:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), anglL={int(anglL)}°, anglR={int(anglR)}°")
        mylog.log(INFO, f">>>   [ (normR > {int(thsd(PRM[0]))} and anglR > {PRM[2]:.2f} and anglR < {PRM[3]:.2f})"\
                      + f" or (normL > {int(thsd(PRM[1]))} and anglL > {PRM[2]:.2f} and anglL < {PRM[3]:.2f}) ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3]), (4,PRM[4])] )  
        if  (normR > thsd(PRM[0]) and anglR > PRM[2] and anglR < PRM[3]) or \
            (normL > thsd(PRM[1]) and anglL > PRM[2] and anglL < PRM[3]):
            # 右手首の移動ベクトルの長さが15以上の場合（引分け大三への動作開始）
            g.Step_counter += 1
            if g.Step_counter == PRM[4]:   started = True
    
    # 5-Hiki-wake  ->  6-Kai        
    elif section_no == 5:  
        _, angER = keyPoints.norm('right_elbow', 'right_wrist')     # 右肘から右手首へのベクトルの角度を計算
        if g.Step_counter > 90 :  # 離れアラート設定（仮）
            mylog.log(INFO, f">>>   angER={angER:.1f}°")
            if angER > 145 or angER < -145:                 # Yolo8の誤検出防止
                # 右肘の角度が伸展している場合（会なしで離れ）
                g.Alart_id = Alart_KaiNasi
                g.Step_error = True
            else: g.Step_counter = g.Step_counter%10
        else:    
            normER, _ = arrow[Kn2idx['right_elbow']]                    # 右肘の移動ベクトルの長さと角度
            normEL, _ = arrow[Kn2idx['left_elbow']]                     # 左肘の移動ベクトルの長さと角度
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                            + f" normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normL)}({thsd.ratio(normL):.3f})")
            mylog.log(INFO, f">>>   [ (normR < {int(thsd(PRM[0]))} and normL < {int(thsd(PRM[1]))}) and (normER < {int(thsd(PRM[2]))} and normEL < {int(thsd(PRM[3]))}) ]")
            
            Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3]), (4,PRM[4])] )  
            if (normR < thsd(PRM[0]) and normL < thsd(PRM[1])) and (normER < thsd(PRM[2]) and normEL < thsd(PRM[3])) :
                # 右手首の移動ベクトルの長さが10以下の場合（引分けの完了）
                g.Step_counter = g.Step_counter + 1
                if g.Step_counter == PRM[4]: started = True    #  停止状態の５回保持で完了
            else:
                mylog.log(INFO, f">>>   angER={angER:.1f}°")
                mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[5]))} and angER < -90.0 ]")
                Stkp.push( [(5,PRM[5])] )  
                if normR > thsd(PRM[5]) and angER < -90.0:
                    # 右手首の移動ベクトルの長さが大きい（会なしで離れ）
                    g.Step_counter += 90              # 離れアラート設定（仮）
    
    # 6-Kai  ->  7-Hanare        
    elif section_no == 6:  
        mylog.log(INFO, f">>>   angR-EW={g.ER_angle:.1f}°")
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} and normL > {int(thsd(PRM[1]))} ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2])] )  
        if normR > thsd(PRM[0]) and normL > thsd(PRM[1]):
            # 右手首、左手首の移動ベクトルの長さが大きい場合（離れ）
            started = True
        elif normR > thsd(PRM[0]) and g.ER_angle < -90.0:
            # 右手首の動き検知のみあり
            g.Step_counter += 1
            if g.Step_counter > PRM[2]:
                # 左手首（弓手）の押しタイミングズレ
                g.Alart_id = Alart_Hanare
                g.Step_error = True
                started = True
        elif g.Step_counter > 0: 
            # 左手首（弓手）の動き検知なし
            started = True
    
    # 7-Hanare  ->  8-Zan-shin        
    elif section_no == 7:  
        mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[0]))} ]")

        Stkp.push( [(0,PRM[0])] )  
        if normR < thsd(PRM[0]) :
            started = True

    # 8-Zan-shin  ->  9-''(弓倒し)
    elif section_no == 8:  
        mylog.log(INFO, f">>>   normR={int(normR)}({thsd.ratio(normR):.3f}), normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[0]))} and normL > {int(thsd(PRM[1]))} ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (1,PRM[2])] )  
        if normR > thsd(PRM[0]) and normL > thsd(PRM[1]):
            # 右手首と左手首の移動ベクトルの長さが大きい場合（弓だおし開始）
            g.Step_counter += 1
            if g.Step_counter == PRM[2]:
                started = True
    
    # 9-''(弓倒し)  ->  0-Start
    elif section_no == 9:  
        if g.Step_counter == 0: g.Step_counter = 10
        mylog.log(INFO, f">>>   normS={int(normS)}({thsd.ratio(normS):.3f})")
        mylog.log(INFO, f">>>   [ normS > {int(thsd(PRM[0]))} ]")

        Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
        if normS > thsd(PRM[0]):
            # 右肩の移動ベクトルの長さが大きい場合（退場）
            if int(g.Step_counter/10) == 1: g.Step_counter = 20
            g.Step_counter += 1
            if g.Step_counter%10 == PRM[1]: started = True
        else:
            mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[2]))} ]")
            Stkp.push( [(2,PRM[2]), (3,PRM[3])] )  
            if normR > thsd(PRM[2]):
                mylog.log(INFO, f">>>   [ counter < 30 and (anglR > {PRM[4]:.1f} and anglR < {PRM[5]:.1f}) ]")
                Stkp.push( [(4,PRM[4]), (5,PRM[5])] )  
                if g.Step_counter < 30 and (anglR > PRM[4] and anglR < PRM[5]):
                    g.Step_counter = 30
                    started = True
                else:
                    # 右手首の移動ベクトルの長さが大きい場合（矢つがえ開始）
                    if int(g.Step_counter/10) == 2: g.Step_counter = 10
                    g.Step_counter += 1
                    if g.Step_counter%10 == PRM[3]:
                        g.Step_counter = 10 + (g.Step_counter%10) 
                        started = True
    else:
        mylog.log(ERROR, f">>> section_no={section_no}は未定義のセクションです")
        started = False
    #
    mylog.log(INFO, f">>>   started  ({section_no}): started={started}")
    return started
#
# 射法八節解析（正面カメラ）用の関数
#セクションが完了したかどうかを判定する関数
#
def section_completed(section_no, myResult:MyResult):
    global Stkp
    
    keyPoints = myResult                            # キーポイントのデータ解析インスタンス
    ibox = myResult.boxid
    
    thsd = Threshold(keyPoints.block_height)        # バウンディングボックスの高さを基準に閾値設定インスタンス

    # 各キーポイントの移動ベクトルの長さと角度を格納するリスト
    arrow = myResult.arrow_length_angles[Sample_lag]  
    
    normR, anglR = arrow[Kn2idx['right_wrist']]                     # 右手首の移動ベクトルの長さと角度
    normL, _ = arrow[Kn2idx['left_wrist']]                          # 左手首の移動ベクトルの長さと角度
    normER, _ = arrow[Kn2idx['right_elbow']]                        # 右肘の移動ベクトルの長さと角度
    normEL, _ = arrow[Kn2idx['left_elbow']]                         # 左肘の移動ベクトルの長さと角度
    
    xy_wristR = keyPoints.xy('right_wrist')                         # 右手首の座標
    xy_wristL = keyPoints.xy('left_wrist')                          # 左手首の座標
    xy_nose = keyPoints.xy('nose')                                  # 鼻の座標

    lenY, _ = keyPoints.norm('right_eye', 'left_eye')               # 右目と左目のベクトルの長さと角度を計算

    completed = False
    # 共通の開始条件を取得
    PRM = CompleteAction_param['param'][10]    # 10は共通の開始条件 
    conf = keyPoints.conf('right_wrist')                                # 右手首の座標の信頼度
    
    if conf < PRM[0]  and (section_no > 1 and section_no < 9):
        # 右手首の信頼度が低い
        mylog.log(INFO, f"completed({section_no}): right-wrist-conf={conf:.2f}({PRM[0]:.2f}), "\
                      + f" skip....")
        return completed

    mylog.log(INFO, f"completed({section_no}):フレーム={g.Frame_counter}\n"\
            + f"    boxid={ibox}, H={int(thsd.block_height)}, wristR=[{int(xy_wristR[0])}, {int(xy_wristR[1])}],"\
            + f"    normR={int(normR)}({thsd.ratio(normR):.3f}), anglR={int(anglR)}°, anglRL={int(g.RL_angle)}°, conf={conf:.2f}, counter={g.Step_counter}")
    
    #
    # 節の動作完了（次節への移行体制）条件を判定
    #    
    # セクションごとの開始条件を取得
    PRM = CompleteAction_param['param'][section_no]  
    # 1-Asi-bumi
    if section_no == 1:  
        if g.Step_counter == 0:
            #conf= keyPoints.conf('left_eye')       
            #mylog.log(INFO, f">>>   lenY={int(lenY)}({thsd.ratio(lenY):.3f}), conf={conf:.2f}")
            #mylog.log(INFO, f">>>   [  lenY > {int(thsd(PRM[0]))} and conf > {PRM[1]:.2f} ]")
            lenS, _ = keyPoints.norm('right_shoulder', 'left_shoulder')    # 右肩と左肩のベクトルの長さと角度を計算
            conf= keyPoints.conf('left_shoulder')       
            mylog.log(INFO, f">>>   lenS={int(lenS)}({thsd.ratio(lenS):.3f}), conf={conf:.2f}")
            mylog.log(INFO, f">>>   [  lenS > {int(thsd(PRM[0]))} and conf > {PRM[1]:.2f} ]")
            
            Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
            #if lenY > thsd(PRM[0]) and conf > PRM[1]:
            if lenS > thsd(PRM[0]) and conf > PRM[1]:
                # 右目と左目のベクトルの長さが10以上、左目の信頼度が0.5以上の場合（正面を向く）
                g.Step_counter = 10
        else:
            normN, _ = arrow[Kn2idx['nose']]                        # 鼻の移動ベクトルの長さと角度
            normHR, _ = arrow[Kn2idx['right_hip']]                  # 左腰の移動ベクトルの長さと角度
            normHL, _ = arrow[Kn2idx['left_hip']]                   # 左腰の移動ベクトルの長さと角度
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), normN={int(normN)}({thsd.ratio(normN):.3f}), "\
                            + f" normHR={int(normHR)}({thsd.ratio(normHR):.3f}), normHL={int(normHL)}({thsd.ratio(normHL):.3f})") 

            mylog.log(INFO, f">>>   [ (normR <= {int(thsd(PRM[2]))} and normL <= {int(thsd(PRM[3]))}) and"\
                        + f" (normHR <= {int(thsd(PRM[4]))}) and (normHL <= {int(thsd(PRM[5]))}) and (normN <= {int(thsd(PRM[6]))}) ]")
            
            Stkp.push( [(2,PRM[2]), (3,PRM[3]), (4,PRM[4]), (5,PRM[5]), (6,PRM[6])] )  
            if (normR <= thsd(PRM[2]) and normL <= thsd(PRM[3])) and (normHR <= thsd(PRM[4]) and normHL <= thsd(PRM[5])) and (normN <= thsd(PRM[6])):
                # 右手首と左手首、右腰骨と左腰骨の移動ベクトルの長さが10未満、鼻の移動ベクトルの長さが10未満、
                g.Step_counter += 1
                if (g.Step_counter%10) == PRM[7]: completed = True
                
        if not completed and g.CameraPos == 'Front-side':
            xy_hipL = keyPoints.xy('left_hip')                         # 右腰の座標
            mylog.log(INFO, f">>>   x_wristR={int(xy_wristR[0])}, x_hipL={int(xy_hipL[0])}")
            mylog.log(INFO, f">>>   int(x_wristR) > int(x_hipL")
            if int(xy_wristR[0]) > int(xy_hipL[0]):
                # 右手首が左腰の右にある（足踏み完了なしで矢番え動作（胴作り）へ）
                g.Alart_id = Alart_Asibumi
                g.Step_error = True
           
    # 2-Dou-zukuri            
    elif section_no == 2:  
        if g.Step_counter == 0: g.Step_counter = 1  # 初期化（矢番え動作開始）
        
        _, angER = keyPoints.norm('right_elbow', 'right_wrist')     # 右肘から右手首へのベクトルの角度を計算
        _, angSE = keyPoints.norm('right_shoulder', 'right_elbow')  # 右肩から右肘へのベクトルの角度を計算
        if g.Step_counter >= 10 and g.Step_counter < 20:
            mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[5]))} ]")
            
            Stkp.push( [(5,PRM[5]), (6,PRM[6])] )  
            if normR > thsd(PRM[5]): 
                # 右手首の移動ベクトルの長さが大きい場合（取り矢動作開始）
                g.Step_counter += 1
                if (g.Step_counter%10) == PRM[6]: g.Step_counter = 20 
            else:
                g.Step_counter = int(g.Step_counter/10)*10  # 連続回数をリセット    
        else:
            mylog.log(INFO, f">>>   angER= {angER:.1f}°, angSE= {angSE:.1f}°, SL_angl= {g.SL_angle:.1f}")
            mylog.log(INFO, f">>>   [ (angER > {PRM[0]:.1f} and angER < {PRM[1]:.1f}) and angSE > {PRM[2]:.1f} ]")
            
            Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2])] )  
            if ( (angER > PRM[0] and angER < PRM[1]) and (angSE > PRM[2]) ):
                # 右手首と右肘を結ぶベクトルの角度が65度から95度の範囲内の場合
                mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[3]))} ]")
            
                Stkp.push( [(3,PRM[3]), (4,PRM[4]), (7,PRM[7])] )  
                if ( normR <= thsd(PRM[3]) ) : 
                    if g.Step_counter < 10:
                        # 右手首と左手首の移動ベクトルの長さが10未満の場合（矢つがえ動作完了）
                        g.Step_counter += 1
                        if (g.Step_counter%10) == PRM[4]: g.Step_counter = 10        #２回保持
                    elif g.Step_counter >= 20:
                        # 右手首と左手首の移動ベクトルの長さが10未満の場合（胴作り完了）
                        g.Step_counter += 1
                        if (g.Step_counter%10) == PRM[7]: completed = True         #５回保持
            else:
                g.Step_counter = int(g.Step_counter/10)*10 + 1 # 連続回数をリセット
        #
        if not completed and g.Step_counter >= 10:
            mylog.log(INFO, f">>>   [ lenY < {int(thsd(PRM[8]))} and angER > {PRM[0]:.1f} ]")            
            Stkp.push( [(7,PRM[8])] )  
            if lenY < thsd(PRM[8]) and  angER >PRM[0]:
                # 目の間隔が狭くなる（箆調べ）
                completed = True
                        
    # 3-Yu-gamae            
    elif section_no == 3:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), normER={int(normER)}({thsd.ratio(normR):.3f}),"\
                      + f" normEL={int(normEL)}({thsd.ratio(normEL):.3f}), lenY={int(lenY)}({thsd.ratio(lenY):.3f})")
        if g.Step_counter < 10:
            mylog.log(INFO, f">>>   [ (normR < {int(thsd(PRM[0]))} and normL < {int(thsd(PRM[1]))})"\
                            + f" and (normER < {int(thsd(PRM[2]))} and normEL < {int(thsd(PRM[3]))}) ]")

            Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3]), (4,PRM[4])] )  
            if (normR < thsd(PRM[0]) and normL < thsd(PRM[1])) and (normER < thsd(PRM[2]) and normEL < thsd(PRM[3])) :
                # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満の場合
                g.Step_counter = g.Step_counter + 1
                if g.Step_counter >= PRM[4]: g.Step_counter = 10
            else: g.Step_counter = 0
        else:            
            mylog.log(INFO, f">>>   [ lenY < {int(thsd(PRM[5]))} ]")
            
            Stkp.push( [(5,PRM[5])] )  
            if lenY < thsd(PRM[5]):  
                # 物見を定める
                g.Step_counter = g.Step_counter + 1
            Stkp.push( [(6,PRM[6])] )  
            if g.Step_counter%10 >= PRM[6]: completed = True   # 
            else:
                mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[7]))} and normL > {int(thsd(PRM[7]))} ]")
                Stkp.push( [(7,PRM[7])] )  
                if normR > thsd(PRM[7]) and normL > thsd(PRM[7]):
                    # 右手首と左手首の移動ベクトルの長さが大きい（物見なしで打ちおこし）
                    g.Alart_id = Alart_Monomi
                    g.Step_error = True                
                
    # 4-Uti-okosshi        
    elif section_no == 4:
        if g.Step_counter < 10:  
            mylog.log(INFO, f">>>   xy_nose={int(xy_nose[1])}, xy_wristR={int(xy_wristR[1])}, xy_wristL={int(xy_wristL[1])}")
            mylog.log(INFO, f">>>   [ (xy_wristR[1] < xy_nose[1] and xy_wristL[1] < xy_nose[1] ]")
            if (xy_wristR[1] < xy_nose[1] and xy_wristL[1] < xy_nose[1]):
                # （右手首と左手首が鼻より高い位置（Y軸は下方が正）
                g.Step_counter = 10
        else:
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                          + f"normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normEL)}({thsd.ratio(normEL):.3f})")
            mylog.log(INFO, f">>>   [ (normR < {int(thsd(PRM[0]))} and normL < {int(thsd(PRM[1]))}) and (normER < {int(thsd(PRM[2]))} and normEL < {int(thsd(PRM[3]))}) ]")

            Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3]), (4,PRM[4])] )  
            if (normR < thsd(PRM[0]) and normL < thsd(PRM[1])) and (normER < thsd(PRM[2]) and normEL < thsd(PRM[3])):
                # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満
                g.Step_counter = g.Step_counter + 1
                if (g.Step_counter%10) == PRM[4]: completed = True   # ３回保持で完了                
    
    # 5-Hiki-wake        
    elif section_no == 5:  
        xy_shouderR = keyPoints.xy('right_shoulder')                # 右腰の座標
        mylog.log(INFO, f">>>   y_nose={int(xy_nose[1])}, y_wristR={int(xy_wristR[1])}, y_shoulR={int(xy_shouderR[1])}")

        mylog.log(INFO, f">>>   [ y_wristR < y_nose ]")
        if  xy_wristR[1] < xy_nose[1]  :
            # 右手首が鼻より高い位置（Y軸は下方が正）
            _, anglEL = keyPoints.norm('left_elbow', 'left_wrist')       # 左肘から左手首へのベクトルの角度を計算
            mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}), anglR={int(anglR)}°, anglEL={int(anglEL)}°")
            if g.Step_counter < 10:   # 「打越し」から「大三」への移行
                mylog.log(INFO, f">>>   [ normL < {int(thsd(PRM[0]))} and anglEL > -80° ]")
                Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
                if normL < thsd(PRM[0]) and anglEL > -80.0:  g.Step_counter += 1      # 弓手の静止
                else: g.Step_counter = 0
                              
                if g.Step_counter == PRM[1]: g.Step_counter = 10                        # 6回保持で「大三」へ移行
                else:
                    mylog.log(INFO, f">>>   [ normR > {int(thsd(0.025))} and (anglR < -130 or anglR > 130) ]")
                    if normR > thsd(0.025) and (anglR < -130 or anglR > 130):       # 馬手の引きが大きい場合    
                        # 「大三」不安定
                        g.Step_counter = 31
            elif g.Step_counter > 30:
                    mylog.log(INFO, f">>>   [ normR > {int(thsd(0.025))} and (anglR < -130 or anglR > 130) ]")
                    if normR > thsd(0.030) and (anglR < -130 or anglR > 130):       # 馬手の引きが大きい場合    
                        # 「大三」不安定
                        g.Step_counter += 1
                        if (g.Step_counter%10) == 3:
                            g.Step_counter = 10
                            g.Alart_id = Alart_Daisan
                            g.Step_error = True
                    else: g.Step_counter = 0
                
            elif PRM[2] > 0.0:  # 「大三」から「引き分け」完了への移行
                mylog.log(INFO, f">>>   [ normL > {int(thsd(PRM[2]))} ]")
                Stkp.push( [(2,PRM[2])] )  
                if normL > thsd(PRM[2]): 
                    # 「押し」を優先的に判定する
                    g.Step_counter = 11         # 「押し」
                    g.Push_counter += 1
                else:
                    mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[2]))} ]")
                    if normR > thsd(PRM[2]):  
                        g.Step_counter = 12     # 「引き」
                        g.Pull_counter += 1
            
            else: g.Step_counter = 13

        elif  xy_wristR[1] < xy_shouderR[1] :
            # （右手首が右肩より高い位置で停止）
            if g.Step_counter < 20: g.Step_counter = 20

            if g.Step_counter > 90 :  # 離れアラート設定（仮）
                _, angER = keyPoints.norm('right_elbow', 'right_wrist')     # 右肘から右手首へのベクトルの長さと角度を計算
                mylog.log(INFO, f">>>   angER={angER:.1f}°")
                if angER > 145 or angER < -145:             # Yolo8の誤検出防止 
                    g.Alart_id = Alart_KaiNasi
                    g.Step_error = True
                else:
                    g.Step_counter = 20 + g.Step_counter%10
            else:    
                mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                            + f" normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normL)}({thsd.ratio(normEL):.3f})")
                mylog.log(INFO, f">>>   [ (normR < {int(thsd(PRM[3]))} and normL < {int(thsd(PRM[4]))}) and (normER < {int(thsd(PRM[5]))} and normEL < {int(thsd(PRM[6]))}) ]")

                Stkp.push( [(3,PRM[3]), (4,PRM[4]), (5,PRM[5]), (6,PRM[6]), (7,PRM[7])] )  
                if (normR < thsd(PRM[3]) and normL < thsd(PRM[4])) and (normER < thsd(PRM[5]) and normEL < thsd(PRM[6])) :
                    # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満（姿勢の保持で完了）
                    g.Step_counter = g.Step_counter + 1
                    if (g.Step_counter%10) == PRM[7]:  completed = True
                else:
                    # 右手首の移動ベクトルの長さが大きい（会なしで離れ）
                    mylog.log(INFO, f">>>   [ (g.Step_counter%10) > {PRM[8]} and (normR > {int(thsd(PRM[9]))}) ]")
                    Stkp.push( [(8,PRM[8]), (9,PRM[9])] )  
                    if (g.Step_counter%10) > PRM[8] and normR > thsd(PRM[9]):
                        g.Step_counter = 90 + g.Step_counter%10         # 離れアラート設定（仮）
    # 6-Kai            
    elif section_no == 6:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f}),"\
                      + f" normER={int(normER)}({thsd.ratio(normER):.3f}), normEL={int(normEL)}({thsd.ratio(normEL):.3f}) ")
        mylog.log(INFO, f">>>   [ (normR < {int(thsd(PRM[0]))} and normL < {int(thsd(PRM[1]))}) and (normER < {int(thsd(PRM[2]))} and normEL < {int(thsd(PRM[3]))}) ]")

        if g.Step_counter == 0: g.Step_counter = 1  # 初期化（口割）
        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2]), (3,PRM[3]), (4,PRM[4])] )  
        if (normR < thsd(PRM[0]) and normL < thsd(PRM[1])) and (normER < thsd(PRM[2]) and normEL < thsd(PRM[3])) :
            # 右手首と左手首の移動ベクトルの長さが10未満、右肘と左肘の移動ベクトルの長さが10未満（姿勢の保持で完了）
            g.Step_counter = g.Step_counter + 1
            if g.Step_counter == PRM[4]:  completed = True
        else:
            mylog.log(INFO, f">>>   [ normR > {int(thsd(PRM[5]))} and normL > {int(thsd(PRM[6]))} ]")

            Stkp.push( [(5,PRM[5]), (6,PRM[6])] )  
            if normR > thsd(PRM[5]) and normL > thsd(PRM[6]):
                # 右手首の移動ベクトルの長さが大きい（会不十分で離れ）
                g.Alart_id = Alart_KaiFusoku
                g.Step_error = True
            #else:
            #    g.Step_counter = 1  # 連続回数をリセット
    
    # 7-Hanare        
    elif section_no == 7:          
        g.Step_counter = g.Step_counter + 1
        Stkp.push( [(0,PRM[0])] )  
        if g.Step_counter > PRM[0]: completed = True
    
    # 8-Zan-shin    
    elif section_no == 8:  
        mylog.log(INFO, f">>>   normL={int(normL)}({thsd.ratio(normL):.3f})")
        mylog.log(INFO, f">>>   [ normR < {int(thsd(PRM[0]))} and normL < {int(thsd(PRM[1]))} ]")
        Stkp.push( [(0,PRM[0]), (1,PRM[1]), (2,PRM[2])] )  
        if normR < thsd(PRM[0]) and normL < thsd(PRM[1]):
            # 右手首と左手首の移動ベクトルの長さが50以下の場合（姿勢の保持で完了）
            g.Step_counter = g.Step_counter + 1
            if g.Step_counter == PRM[2]:  completed = True
    
    # 8-Zan-shin(弓倒し)        
    elif section_no == 9:  
        xy_hipR = keyPoints.xy('right_hip')                                 # 右腰の座標
        xy_hipL = keyPoints.xy('left_hip')                                  # 左腰の座標
        _, angER = keyPoints.norm('right_elbow', 'right_wrist')             # 右肘から右手首へのベクトルの長さと角度を計算
        normS, _ = arrow[Kn2idx['right_shoulder']]                          # 右肩の移動ベクトルの長さと角度
        mylog.log(INFO, f">>>   angER= {angER:.1f}°, normS={int(normS)}({thsd.ratio(normS):.3f})")
        mylog.log(INFO, f">>>   x_wristR= {int(xy_wristR[0])}, x_hipR= {int(xy_hipR[0])}")
        
        if g.Step_counter == 30:
            mylog.log(INFO, f">>>   [ x_wristR < x_hipR ]")
            if ( int(xy_wristR[0]) < int(xy_hipR[0]) ):  g.Step_counter += 1
        else:
            if g.Step_counter == 0: g.Step_counter = 1
            mylog.log(INFO, f">>>   [ (angER > {PRM[0]:.1f} and angER < {PRM[1]:.1f}) and x_wristR < x_hipR ]")
            
            Stkp.push( [(0,PRM[0]), (1,PRM[1])] )  
            if ( (angER > PRM[0] and angER < PRM[1]) and int(xy_wristR[0]) < int(xy_hipR[0]) ):
                # 右手首と右肘を結ぶベクトルの角度が65度から95度の範囲内の場合
                mylog.log(INFO, f">>>   [ normR <= {int(thsd(PRM[2]))} ]")

                Stkp.push( [(2,PRM[2]), (3,PRM[3])] )  
                if normR <= thsd(PRM[2]) : 
                    g.Step_counter += 1
                    if (g.Step_counter%10) == PRM[3]:
                        g.Step_counter = 0 
                        completed = True
            if not completed : 
                mylog.log(INFO, f">>>  [ x_wristR > x_hipR ]")
                if int(xy_wristR[0]) > int(xy_hipR[0]):
                    if g.Step_counter > 30: 
                        # 右手首が右腰の右に戻る（取り消した完了を復帰）
                        completed = True
                    else:
                        # （完了なしで矢番え動作（胴作り）へ）
                        g.Alart_id = Alart_Asibumi
                        g.Step_error = True
        if not completed:    
            mylog.log(INFO, f">>>   [ normS > {int(thsd(PRM[4]))} ]")
            Stkp.push( [(4,PRM[4])] )  
            if normS > thsd(PRM[4]):
                # 右肩の移動ベクトルの長さが大きい場合（退場）
                g.Step_counter = -1
                completed = True            
    else:
        mylog.log(ERROR, f">>>  section_no={section_no}は未定義のセクションです")
        completed = False
    #
    mylog.log(INFO, f">>>   completed({section_no}): completed={completed}")
    return completed
#
# 射法八節解析（正面カメラ）用の関数
# 動作の開始を判定する関数
#  
def manual_analize_start(section_no, myResult:MyResult):
    
    # 動作の開始を判定
    if section_started(section_no, myResult):
        print(f"[man_analize]: section({section_no}), strated=True")
        g.Action_start = g.Lap_sec
        g.Split_start = g.Frame_counter                         # スプリット開始時間を記録
        if g.Section_no == 6: g.Split_last = g.Split_sec          # 「会」スプリット秒を記録
        g.Split_sec = 0.0
        g.Completed = False                                   # セクションが開始されたら完了フラグをリセット    
        g.Nop_counter = 0                                     # セクション内の動作が完了しない場合のカウンター
        if g.Section_no < 5: g.Pull_counter,g.Push_counter = 0,0  # 「引き分け」引き・押しのカウンターリセット
        if g.Section_no != 9: 
            g.Section_no = g.Section_no + 1                     # セクション番号をインクリメント
            g.Step_counter = 0                                # セクション内の動作カウンター
        else:
            #早矢弓倒し完了からの動作開始
            counter = int(g.Step_counter/10)      
            mylog.log(INFO, f"[man_analize]: g.Step_counter={g.Step_counter}") 
            if counter == 2: 
                g.Lap_start = 0                               # 退場動作開始の場合、解析終了
                g.Split_sec = 0.0
                g.Split_start = 0
            elif counter == 3:                              # 乙矢の持ち直し動作開始
                g.Completed = False                           # 完了フラグをリセット
                print(f"[man_analize]: section({section_no}), Reset completed=False")
                #g.Step_counter = 0
            else:                                           # 乙矢の矢つがえ動作開始
                # セクション番号を2にリセット、動作カウンターを30に設定
                g.Section_no = 2
                g.Step_counter = 30
                mylog.log(INFO, f"[man_analize]: Next {Section_names[g.Section_no]} Sction_no={g.Section_no}, g.Step_counter={g.Step_counter}") 
        #
    else:
        g.Nop_counter += 1
        if g.Step_error:
            # セクション内の動作が不正な場合
            g.Alart_section = g.Section_no
            mylog.log(INFO, f"[man_analizestart]: g.Step_error={g.Step_error}, g.Alart_id={g.Alart_id}")
            if g.Alart_id == Alart_Hanare:   # 弓手押しタイミングの遅れ
                g.Section_no += 1                             # セクション番号をインクリメント
            if g.Alart_id == Alart_KaiNasi: g.Section_no += 1   # 会なしで離れた場合
            g.Step_counter = 0
            g.Nop_counter = 0                                 # セクション内の動作が完了しない場合のカウンター
        #
    return g.Section_no, g.Completed  
#
# 射法八節解析（正面カメラ）用の関数
# 動作の完了を判定する関数
#
def manual_analize_completed(section_no, myResult:MyResult):
    
    # 動作の完了を判定
    if section_completed(section_no, myResult):
        print(f"[man_analize]: section({section_no}), completed=True")
        g.Action_start = g.Lap_sec
        g.Completed = True 
        g.Split_start = g.Frame_counter                         # スプリット開始時間を記録
        if g.Section_no == 9 and g.Step_counter == -1:
            # 退場動作の場合、解析終了 
            g.Lap_start = 0
        if not (g.Section_no == 9 and g.Step_counter > 30):
            g.Step_counter = 0
        g.Nop_counter = 0
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
        #
    return g.Section_no, g.Completed  
#
# eof