#
#
# Class for sqlite3
#     
import sqlite3
import pandas
import time
from datetime import datetime
# local modules
from  kyudo.env import * 
#
# Private API Class for sqlite3from env import *
#
class MyDb:
    def __init__(self, dbpath='./yolo-kyudo.db'):
        self.dbpath = dbpath
        self.conn = sqlite3.connect(dbpath, check_same_thread=False)    # open database
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.mode = ''
        self.case_name = 'none'
        self.frame_no = 0
        self._section = 0
        self._step_counter = 0
        self._completed = 0
        self.section = 0
        self.step_counter = 0
        self.completed = 0
        self.csvpath1 = ''        # trcking_data用CSV出力ファイルパス
        self.csvfile1 = None
        self.csvpath2 = ''        # kyudo_data用CSV出力ファイルパス
        self.csvfile2 = None
        
    def open_csv(self):
        # CSV出力ファイルの作成
        timestamp = datetime.now().strftime('%Y%m%d')
        self.csvpath1 = self.dbpath[:self.dbpath.rfind('/')+1] + f"track{timestamp}_{self.case_name}.csv"
        self.csvfile1 = open( self.csvpath1, 'w')
        # カラム名を出力
        names ="case_name,frame_no,key_id,key_name,"\
            +  "box_id,box_w,box_h,"\
            +  "x,y,xy_conf,norm,ratio,angle,"\
            +  "inserted_at,time_epoch\n"
        self.csvfile1.write(names)
        self.csvfile1.flush()

        self.csvpath2 = self.dbpath[:self.dbpath.rfind('/')+1] + f"kyudo{timestamp}_{self.case_name}.csv"
        self.csvfile2 = open( self.csvpath2, 'w')
        # カラム名を出力
        names ="case_name,frame_no,"\
            +  "box_id,box_conf,box_w,box_h,"\
            +  "rw_norm,rw_angle,"\
            +  "lw_norm,lw_angle,"\
            +  "rl_norm,rl_angle,"\
            +  "hr_norm,hr_angle,"\
            +  "sr_norm,sr_angle,"\
            +  "sl_norm,sl_angle,"\
            +  "rew_angle,rse_angle,"\
            +  "lew_angle,lse_angle,"\
            +  "eyes_norm,hips_norm,"\
            +  "tag1,tag2,"\
            +  "section,completed,label,inserted_at,time_epoch\n"
        self.csvfile2.write(names)
        self.csvfile2.flush()
            

    def rollback(self):
        self.conn.rollback()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def execute(self, sql):
        return self.cur.execute(sql)
#
# insert frame_info table
#
    def insert_frame_info(self, data_list):
        
        # 重複キーの存在チェック
        sql = f"select * from frame_info where case_name='{self.case_name}'"
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            # 重複キーが存在する場合は削除
            sql = f"delete from frame_info where case_name ='{self.case_name}'"
            self.cur.execute(sql)

        d = datetime.now()
        timestamp = d.strftime('%Y-%m-%d %H:%M:%S')
        
        values = f"'{self.case_name}', '{data_list[0]}', {data_list[1]:.3f}, {data_list[2]}, {data_list[3]}, '{data_list[4]}',"\
               + f" '{timestamp}', '{timestamp}'"
            
        sql = "insert into frame_info"\
            + "(case_name, img_path, fps, height, width, csv_path, updated_at, inserted_at)"\
            + f" values({values})"

        self.cur.execute(sql)
        self.commit()
#
# update frame_info table
#
    def update_frame_info(self, col_name, value):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sql = f"update frame_info set"\
            + f" {col_name} = {value},"\
            + f" updated_at='{timestamp}'"\
            + f" where case_name='{self.case_name}'"
        self.cur.execute(sql)
        self.commit()
#
# delete frame_info table
#
    def delete_case(self, case_name):
        ret = False
        # キーの存在チェック
        sql = f"select * from frame_info where case_name='{case_name}'"
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            # キーが存在する場合は削除
            sql = f"delete from frame_info where case_name ='{case_name}'"
            self.cur.execute(sql)
            self.conn.commit()
            ret = True
        return ret
 
#
# delete records from any table by case_name without commit
#
    def delete_case_records(self, tbl, case_name):
        rcnt = None
        sql = f"delete from {tbl} where case_name = '{case_name}'"
        try:
            self.cur.execute(sql)
            rcnt = self.cur.rowcount
            self.conn.commit()
        except Exception as e:
            print(f"[delete_case_records]:error: {e}")
        return rcnt
#
# copy records from any table by case_name, and rename to to_name
#
    def copy_case(self, tbl, from_name, to_name):
        df = pandas.read_sql_query(f"SELECT * FROM {tbl} WHERE case_name='{from_name}'", self.conn)
        i = -1
        print(f"[copy_case]:info: {tbl} df:{df.shape}")
        rcnt = df.shape[0]
        if rcnt > 0:
            try:
                df['case_name'] = to_name
                i = df.to_sql(tbl, self.conn, if_exists='append', index=None, method='multi', chunksize=1024)
            except Exception as e:
                print(f"[copy_case]:error: {e}")
                i = -1
            else:
                print(f"[copy_case]:info: copied {i} records.")
                if i != rcnt:
                    print(f"[copy_case]:error: copy count mismatch. from='{from_name}' to='{to_name}'")
        else:
            print(f"[copy_case]:info: case_name='{from_name}' not found.")
        return None if i == -1 else i if i == rcnt else (-1)*i 
#
# insert tracking-data.(db)
#
    def insert_tracking_data(self, data_list):
        
        d = datetime.now()
        timestamp = d.strftime('%Y-%m-%d %H:%M:%S')
        time_epoc = int(time.mktime(d.timetuple()))
        
        values = f"'{self.case_name}',{self.frame_no},"     # case_name, frame_no
        
        for i, value in enumerate(data_list):
            if i == 0 or i == 2:                                # key_id or box_id
                values += f"{value},"
            elif i == 1:                                        # key_name
                values += f"'{value}'," 
            else:
                values += f"{value:.3f},"
            
        values += f"'{timestamp}',{time_epoc}"
            
        sql = "insert into tracking_data"\
            + "(case_name, frame_no, key_id,"\
            + " key_name, box_id, box_w, box_h, x, y, xy_conf, norm, ratio, angle,"\
            + " inserted_at, time_epoch)"\
            + f" values({values})"
        self.cur.execute(sql)
        self.conn.commit()
#
# write tracking-data to csv-file
#
    def outcsv_tracking_data(self, data_list):
        
        d = datetime.now()
        timestamp = d.strftime('%Y-%m-%d %H:%M:%S')
        time_epoc = int(time.mktime(d.timetuple()))
        
        values = f"{self.case_name},{self.frame_no},"
                    
        for i, value in enumerate(data_list):
            if i == 0 or i == 2:                                # key_id or box_id
                values += f"{value},"
            elif i == 1:                                        # key_name
                values += f"{value},"
            else:
                values += f"{value:.3f},"
            
        values += f"'{timestamp}',{time_epoc}"            
        self.csvfile1.write(f"{values}\n")
#
#
    def delete_tracking_data(self):
        sql = f"delete from tracking_data where case_name = '{self.case_name}'"
        try:
            self.cur.execute(sql)
        except:
            print("[delete_tracking_data]:no records.")
        else:
            self.conn.commit()
#
#
    def update_tracking_section(self):
        sql = "update kyudo_data set "\
            + f"section={self.section},"\
            + f"completed={self.completed}"\
            + f" where case_name='{self.case_name}' and frame_no={self.frame_no}"
        self.cur.execute(sql)
        self.conn.commit()
#
#
    def update_tracking_tag(self, tag_name, tag_value):
        sql = "update kyudo_data set "\
            + f"{tag_name}={tag_value}"\
            + f" where case_name='{self.case_name}' and frame_no={self.frame_no}"
        #print(f"update_tracking_tag: {sql}")
        self.cur.execute(sql)
        self.conn.commit()
#
    def clear_tracking_tag(self, tag_name):
        sql = "update kyudo_data set "\
            + f"{tag_name}=NULL"\
            + f" where case_name='{self.case_name}' and {tag_name} IS NOT NULL"
        #print(f"update_tracking_tag: {sql}")
        self.cur.execute(sql)
        self.conn.commit()                   
#
# delete kyudo_data table
    def delete_kyudo_data(self):
        sql = f"delete from kyudo_data where case_name = '{self.case_name}'"
        try:
            self.cur.execute(sql)
        except:
            print("[delete_kyudo_data]:no records.")
        else:
            self.conn.commit()
#
# write kyudo-data to csv-file
#
    def outcsv_kyudo_data(self, data_list, num_classes = 3):
        
        d = datetime.now()
        timestamp = d.strftime('%Y-%m-%d %H:%M:%S')
        time_epoc = int(time.mktime(d.timetuple()))
        
        values = f"{self.case_name},{self.frame_no},"                   # case_name, frame_no
                   
        for i, value in enumerate(data_list): 
            if i == 0 or i >= len(data_list) - 2:                       # 0:box_id, -2:tag1
                values += f"{value},"
            else:
                values += f"{value:.6f},"
        
        label = 0
        if self.section != self._section:
            label = 2 if num_classes == 3 else (self.section * 2 - 1)
            self._section = self.section
            self._completed = 0
        elif self.completed != self._completed:
            label = 1 if num_classes == 3 else (self.section * 2)
            self._completed = self.completed
        elif self.step_counter != self._step_counter:
            if self.section == 1 and self.step_counter == 10:
                if num_classes == 3 : label = 1
            #print(f"[csv_kyudo_data]: section={self.section} step_counter={self._step_counter} -> {self.step_counter}, label={label}")
            self._step_counter = self.step_counter
          
        values += f"{self.section},{self.completed},{label},'{timestamp}',{time_epoc}"            
        self.csvfile2.write(f"{values}\n")
#
# delete eval_data table
    def delete_eval_data(self):
        sql = f"delete from eval_data where case_name = '{self.case_name}'"
        try:
            self.cur.execute(sql)
        except:
            print("[delete_eval_data]:no records.")
        else:
            self.conn.commit()
#
# select FPS from balance-table
#
    def get_fps(self, case_name=None):
        FPS = None
        import_count = 0
        if case_name is None:
            case_name = self.case_name

        sql = f"select fps, import from frame_info where case_name='{case_name}'"

        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            FPS = rs['fps']
            import_count = rs['import']
        return FPS, import_count

    def get_file_path(self, case_name=None):
        img_path = None
        csv_path = None
        if case_name is None:
            case_name = self.case_name

        sql = f"select img_path, csv_path from frame_info where case_name='{case_name}'"

        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            img_path = rs['img_path']
            csv_path = rs['csv_path']
        return img_path, csv_path
    
    def update_import(self, import_count):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = "update frame_info set "\
            + f"import={import_count},"\
            + f"updated_at='{timestamp}'"\
            + f" where case_name='{self.case_name}'"
        self.cur.execute(sql)
        self.conn.commit()
        
#
#   read tracking_data(return pandas-DataFrame)
#       
    def pandas_read_tracking(self, key_id):
        
        sql = f"select * from tracking_data where key_id={key_id} and case_name='{self.case_name}'"
        return pandas.read_sql_query(sql, con=self.conn, index_col='frame_no')
#
#   read kyudo_data of each case_name(return pandas-DataFrame)
#       
    def pandas_read_kyudo(self, cols=None, cases=None):
        if cases is None:
            cond_case = f"case_name='{self.case_name}'"
        else:
            cond_case = "case_name in (" + ','.join([f"'{c}'" for c in cases]) + ")"
            
        #print(f"pandas_read_kyudo: {cases}")
        if cols is None: 
            sql = f"select * from kyudo_data where {cond_case} order by case_name,frame_no asc"
        else: 
            sql = 'select frame_no,' +  ','.join(cols)                                    
            sql += f" from kyudo_data where {cond_case} order by case_name,frame_no asc"
        
        return pandas.read_sql_query(sql, con=self.conn, index_col='frame_no')
#
#   read kyudo_data on each section(return pandas-DataFrame)
#       
    def pandas_read_kyudo_section(self, cols=None, section=0):
        section2 = section + 1 if section < 9 else 2
        if cols is None: 
            sql = f"select * from kyudo_data where "\
                  f" section == {section} or section == {section2}"\
                   " order by case_name, frame_no asc" 
        else: 
            sql =  "select frame_no," +  ','.join(cols) + " from kyudo_data"\
                  f" where section == {section} or section == {section2}"\
                   " order by case_name, frame_no asc" 
                   
        return pandas.read_sql_query(sql, con=self.conn, index_col='frame_no')
#
#   read frame_info(return pandas-DataFrame)
#       
    def pandas_read_frame(self, name=None):
        
        sql = 'select * from frame_info'
        if name is not None:
            sql += f" where case_name='{name}'"
        return pandas.read_sql_query(sql, con=self.conn)
#
# insert act_param table
#
    def insert_act_param(self, act_param_tbl):
        frame_model = act_param_tbl['frame'].split('-')
        if len(frame_model) < 2: return False
        frame_lag = frame_model[0].split('.')
        if not frame_lag[0].isnumeric(): return False
        frame = int(frame_lag[0])
        lag = 0
        if len(frame_lag) > 1:
            if frame_lag[1].isnumeric(): lag = int(frame_lag[1])
        model = frame_model[1]
        
        step = act_param_tbl['step']
        act = act_param_tbl['act']
        act_param = act_param_tbl['param']
        
        # 登録済データを削除
        sql = f"delete from act_param where frame={frame} and lag={lag} and model='{model}' and step={step} and act={act}"
        rs = self.cur.execute(sql)

        for sect, row_list in enumerate(act_param):
            for idx, val in enumerate(row_list):
                if val is None: break
                values = f"{frame}, {lag}, '{model}', {step}, {act}, {sect}, {idx}, {val}"
                sql = "insert into act_param"\
                    + "(frame, lag, model, step, act, sect, idx, val)"\
                    + f" values({values})"
                self.cur.execute(sql)
        self.commit()
        return True
#
# load act_param table
#
    def load_act_param(self, act_param_tbl):
        rec_count = 0
        frame_model = act_param_tbl['frame'].split('-')
        if len(frame_model) < 2: return False
        frame_lag = frame_model[0].split('.')
        if not frame_lag[0].isnumeric(): return False
        frame = int(frame_lag[0])
        lag = 0
        if len(frame_lag) > 1:
            if frame_lag[1].isnumeric(): lag = int(frame_lag[1])
        model = frame_model[1]        
        step = act_param_tbl['step']
        act = act_param_tbl['act']

        for sect in range(11):
            raw_vals = [None]*Param_max
            sql = f"select * from act_param where "\
                + f"frame={frame} and lag={lag} and model='{model}' and step={step} and act={act} and sect={sect}"\
                + f" order by idx asc"
            rs = self.cur.execute(sql).fetchone()
            while rs != None:
                idx = rs['idx']
                if idx < 0 or idx > 9: continue
                raw_vals[idx]= rs['val']
                rs = self.cur.fetchone()
                rec_count += 1
            #
            act_param_tbl['param'].append(raw_vals)
        return rec_count
#
# get print eval_data of each case_name(return print-data-list) 
#
    def get_print_eval_data(self, case_name, section, step, items):
        print_list = []
        for i in range(2):
            #print(f"get_print_eval_data({i}): section={section} step={step}")
            order = f"order by section desc,frame_no desc" if i == 0 else f"order by section,frame_no desc"
            # SQL文を作成
            if step == 0:                       # 完了移行直前のデータを取得
                sql = f"select {items} from eval_data where case_name='{case_name}'"\
                      f" and  (section%10)={section} and completed=0 {order} limit 1"
                      
            # 以下は、完了移行前のステップのデータを取得するための措置
            elif section == 5 and step == 10:   # 大三移行時のデータを取得
                sql = f"select {items} from eval_data where case_name='{case_name}'"\
                      f" and  (section%10)={section} and step={step} and completed=0 {order}"                        
            # SQL文を実行
            df = pandas.read_sql_query(sql, con=self.conn)
            if df.shape[0] == 0:
                break                # no data for this section
            
            # 検索データを整形してリストに追加
            print_text = ""
            for c, val in df.iloc[0].to_dict().items():
                if c == 'section': 
                    v = f"{val:2.0f}.{step}"
                    val = float(v)
                print_text += f"{val:12.2f}" if isinstance(val, float) \
                                else f"{val:12} " if isinstance(val, int) else f"{val:>12}"
                # 以下は、完了移行前のステップのデータを表示するための措置
                if section == 5 and step == 10 and c == 'frame_no':
                    # 大三移行時の角度データを表示するため、空白を追加
                    print_text += " "*12    
                    
            # テキストを出力行リストに追加  
            print_list.append(print_text)
            if df.iloc[0]['section'] < 10:
                break               # 甲矢のみなので、ループを抜ける

        # 乙矢のデータがある場合は、順番を入れ替える
        if len(print_list) == 2:
            print_list[0], print_list[1] = print_list[1], print_list[0]

        return print_list
#
# 登録ケース名の評価データからsection,stepに該当するフレーム番号を取得する
#
    def get_frame_no_at(self, case_name:str, sect:int, step:int):
        #print(f"[get_frame_no_at]: case={case_name},section={sect}, step={step}")
        # SQL文を作成
        if step == 0:   
            # 完了移行直前のデータを取得
            sql = f"select frame_no from eval_data where case_name='{case_name}'"\
                    f" and  section={sect} and completed=0 order by frame_no desc limit 1"
        else:           
            # 完了移行前のステップのデータを取得するための措置
            sql = f"select frame_no from eval_data where case_name='{case_name}'"\
                    f" and  section={sect} and step={step} and completed=0 limit 1"                        
        # SQL文を実行
        df = pandas.read_sql_query(sql, con=self.conn)
        return df.iloc[0]['frame_no'] if len(df) > 0 else None

#eof
