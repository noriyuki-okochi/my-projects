#　
# アプリケーションのグローバル変数の定義（mainとサブモジュール間で共有する変数）
#
Hybrid_model:bool = False       # GRUモデルとロジック解析の併用フラグ
Frame_counter:int = 0           # フレームカウンター
CameraPos:str = ''              # カメラの位置名
#
Section_no:int = 0              # セクション番号
Completed:bool = False          # 完了フラグ
Step_counter:int = 0            # セクション内のステップカウンター
Nop_counter:int = 0             # スキップカウンター
Pull_counter:int = 0            # 引き分け時「引き」カウンター
Push_counter:int = 0            # 引き分け時、「押し」カウンター
#
Step_error:bool = False         # 不正な動作フラグ
Alart_section:int = 0           # アラート発生セクション番号
Alart_id:int = 0                # アラート番号
#
Split_sec:float = 0.0           # スプリット秒
Split_last:float = 0.0          # スプリット秒
Split_start:int = 0             # スプリットベースフレームカウント
Lap_sec:float = 0.0             # ラップ秒 
Lap_start:int = 0               # ラップベースフレームカウント
Action_start:float = 0.0        # アクションベース時間
#
RL_angle:float = 0.0            # 右手首ー＞左手首の角度
SR_angle:float = 0.0            # 右腕の角度(mainのみで使用)
SL_angle:float = 0.0            # 左腕の角度
ER_angle:float = 0.0            # 右肘ー＞右手首の角度
HR_angle:float = 0.0            # 右腰ー＞右手首の角度
RSE_angle:float = 0.0           # 右肩ー＞右肘の角度
EYE_ratio:float = 0.0           # 眼の間隔比率(mainのみで使用)
# eof