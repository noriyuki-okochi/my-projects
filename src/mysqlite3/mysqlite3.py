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
    def __init__(self, dbpath='../yolo-data.db'):
        self.dbpath = dbpath
        self.conn = sqlite3.connect(dbpath, check_same_thread=False)    # open database
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.case_name = 'none'
        self.frame_no = 0
        self.section = 0
        
        timestamp = datetime.now().strftime('%Y%m%d')
        self.logfile = open(dbpath[:dbpath.rfind('/')+1] + f"log{timestamp}.txt", 'a') 
        self.logfile.write(f"DB opened: {dbpath}\n")
        self.logfile.flush()

    def rollback(self):
        self.conn.rollback()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def execute(self, sql):
        return self.cur.execute(sql)
#
# insert samplling rates logs.
#
    def insert_keypoints(self, data_list):
        
        d = datetime.now()
        timestamp = d.strftime('%Y-%m-%d %H:%M:%S')
        time_epoc = int(time.mktime(d.timetuple()))
        
        values = f"'{self.case_name}', {self.frame_no},"
        
        for i, value in enumerate(data_list):
            if i == 0 or i == 2:                # key_id or box_id
                values += f" {value}, "
            elif i == 1:                        # key_name
                values += f" '{value}', "
            else:
                values += f" {value:.3f}, "
            
        values += f" '{timestamp}', {time_epoc}, {self.section}"
            
        sql = "insert into keypoints_data"\
            + "(case_name, frame_no, key_id,"\
            + " key_name, box_id, box_w, box_h, box_conf, x, y, xy_conf, norm, ratio, angle, inserted_at, time_epoch, section)"\
            + f" values({values})"

        self.cur.execute(sql)
        
    def pandas_read_ratelogs(self, params):
        if params['sym'] == '*':
            sql ="select * from ratelogs where length(symbol) < 6"
        else:
            sql ="select * from ratelogs where symbol = :sym"
        if params['limit'] > 0:
            sql += " LIMIT :limit"
        # return pandas.read_sql_query(sql, con=self.conn, params=params)
        return pandas.read_sql_query(sql, con=self.conn, index_col='inserted_at',\
                                     parse_dates=('inserted_at'), params=params)
        
#
# logout
#
    def logwrite(self, msg):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.logfile.write(f"{timestamp}{msg}\n")
        self.logfile.flush()


''' 
#
# insert auto-orders log
#
    def insert_orders(self, id, exchange, pair, trade, extype, rate, amount):
        # insert new datas
        sql = "insert into orders(id, exchange, pair, order_side, order_type, rate, amount)"
        sql += f" values({id},'{exchange}','{pair}','{trade}','{extype}',{rate},{amount})"
        #print(sql)
        self.cur.execute(sql)
        #
        self.conn.commit()
#
#
# insert or update balance-table
#
    def update_balance(self, exchange, symbol, amount, rate, jpy):
        pre = jpy
        symbol = symbol.lower()
        sql = "select * from balance where "\
            + f"exchange='{exchange}' and symbol='{symbol}'"
        rs = self.cur.execute(sql).fetchone()
        if rs == None:
            sql = "insert into balance(exchange,symbol,amount,rate,jpy) values("\
                + f"'{exchange}',"\
                + f"'{symbol}',"\
                + f"{amount},"\
                + f"{rate},"\
                + f"{jpy})"
            self.cur.execute(sql)
        else:
            pre = rs['jpy']
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = "update balance set "\
                + f"amount={amount},rate={rate},"\
                + f"updated_at='{timestamp}'"\
                + f" where exchange='{exchange}' and symbol='{symbol}'"
            self.cur.execute(sql)
        self.conn.commit()
        return int(pre)
#
# select amount from balance-table
#
    def get_balanceAmount(self, exchange, symbol):
        amount = None
        symbol = symbol.lower()
        sql = "select * from balance where "\
            + f"exchange='{exchange}' and symbol='{symbol}'"

        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            amount = rs['amount']

        print(f">get_balanceAmount=>amount={amount}:sql={sql}")
        return amount
#
# adjust amount 
#  
    def adjust_balance(self, exchange, symbol, trade, amount):
        symbol = symbol.lower()        
        c_amount = self.get_balanceAmount(exchange, symbol)
        if c_amount != None:
            if trade == 'SELL':
                c_amount -= amount
            else:     # 'BUY'
                c_amount += amount
            sql = f"update balance set amount = {c_amount} where "\
                + f"exchange='{exchange}' and symbol='{symbol}'"

            print(f">adjust_balance:sql={sql}")
            self.cur.execute(sql)
            self.conn.commit()            
        return c_amount
'''

#eof
