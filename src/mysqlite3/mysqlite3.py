#
#
# Class for sqlite3
#     
import sqlite3
import pandas
import time
from datetime import datetime
#
# Private API Class for sqlite3from env import *
#
class MyDb:
    def __init__(self, dbpath='./yolo-tracking.db'):
        self.dbpath = dbpath
        self.conn = sqlite3.connect(dbpath, check_same_thread=False)    # open database
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.mode = ''
        self.case_name = 'none'
        self.frame_no = 0
        self.section = 0
        self.csvpath = ''
        self.csvfile = None
        
    def open_csv(self):
        # CSV出力ファイルの作成
        timestamp = datetime.now().strftime('%Y%m%d')
        self.csvpath = self.dbpath[:self.dbpath.rfind('/')+1] + f"tracking{timestamp}_{self.case_name}.csv"
        self.csvfile = open( self.csvpath, 'w')
        # カラム名を出力
        names ="case_name,frame_no,key_id,key_name,box_id,box_w,box_h,box_conf,x,y,xy_conf,norm,ratio,angle,eyes_span,shds_span,hips_span,"\
            + "inserted_at,time_epoch,section\n"
        self.csvfile.write(names)
        self.csvfile.flush()
            

    def rollback(self):
        self.conn.rollback()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def execute(self, sql):
        return self.cur.execute(sql)
#
#
#
    def insert_frame_info(self, data_list):
        
        # 重複キーの存在チェック
        sql = f"select * from frame_info where case_name='{self.case_name}'"
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
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
 
# insert samplling rates logs.
#
    def insert_tracking_data(self, data_list):
        
        d = datetime.now()
        timestamp = d.strftime('%Y-%m-%d %H:%M:%S')
        time_epoc = int(time.mktime(d.timetuple()))
        
        if self.mode == '':
            values = f"'{self.case_name}', {self.frame_no},"
        else:
            values = f"{self.case_name}, {self.frame_no},"
            
        
        for i, value in enumerate(data_list):
            if i == 0 or i == 2:                            # key_id or box_id
                values += f" {value}, "
            elif i == 1:                                    # key_name
                if self.mode == '':  values += f" '{value}', " 
                else:  values += f" {value}, "
            else:
                values += f" {value:.3f}, "
            
        values += f" '{timestamp}', {time_epoc}, {self.section}"
            
        if self.mode == 'csv':
            self.csvfile.write(f"{values}\n")
        else:
            sql = "insert into tracking_data"\
                + "(case_name, frame_no, key_id,"\
                + " key_name, box_id, box_w, box_h, box_conf, x, y, xy_conf, norm, ratio, angle,"\
                + " eyes_span, shds_span, hips_span, inserted_at, time_epoch, section)"\
                + f" values({values})"
            self.cur.execute(sql)
#
#
    def delete_tracking_data(self):
        sql = f"delete from tracking_data where case_name = '{self.case_name}'"
        try:
            self.cur.execute(sql)
        except:
            print("[delete_tracking_data]:no records.")
        
                   
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
        FPS = None
        import_count = 0
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
#
#       
    def pandas_read_tracking(self, key_id):
        
        sql = f"select * from tracking_data where key_id={key_id} and case_name='{self.case_name}'"
        return pandas.read_sql_query(sql, con=self.conn, index_col='frame_no')
        
    def pandas_read_frame(self, name=None):
        
        sql = 'select * from frame_info'
        if name is not None:
            sql += f" where case_name='{name}'"
        return pandas.read_sql_query(sql, con=self.conn)
#
#eof
