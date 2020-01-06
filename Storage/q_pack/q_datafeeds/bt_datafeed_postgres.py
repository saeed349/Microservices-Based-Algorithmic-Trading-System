# from __future__ import (absolute_import, division, print_function,
#                         unicode_literals)

import datetime
from backtrader.feed import DataBase
from backtrader import date2num
from sqlalchemy import create_engine


class PostgreSQL_Daily(DataBase):
    params = (
        ('dbHost', None),
        ('dbUser', None),
        ('dbPWD', None),
        ('dbName', None),
        ('ticker', 'EUR_USD'),
        ('fromdate', datetime.datetime.min),
        ('todate', datetime.datetime.max),
        ('name', ''),
        )

    def __init__(self):
        self.engine = create_engine('postgresql+psycopg2://'+self.p.dbUser+':'+ self.p.dbPWD +'@'+ self.p.dbHost +'/'+ self.p.dbName)
#         self.engine = psycopg2.connect(host=self.p.dbHost, database=self.p.dbName, user=self.p.dbUser, password=self.p.dbPWD)

    def start(self):
        self.conn = self.engine.connect()
        sql = "select a.date_price date, a.close_price as close, a.high_price high, a.open_price open, a.low_price low from daily_data a inner join symbol b on a.stock_id = b.id where b.ticker='"+ self.p.ticker + "' and a.date_price between '"+self.p.fromdate.strftime("%Y-%m-%d")+"' and '"+self.p.todate.strftime("%Y-%m-%d")+"' order by date ASC"
        self.result = self.conn.execute(sql)
        

    def stop(self):
        #self.conn.close()
        self.engine.dispose()

    def _load(self):
        one_row = self.result.fetchone()
        if one_row is None:
            return False
        self.lines.datetime[0] = date2num(one_row[0])
        self.lines.open[0] = float(one_row[1])
        self.lines.high[0] = float(one_row[2])
        self.lines.low[0] = float(one_row[3])
        self.lines.close[0] = float(one_row[4])
#         self.lines.volume[0] = int(one_row[5])
        self.lines.openinterest[0] = -1
        return True
    
class PostgreSQL_Minute(DataBase):
    params = (
        ('dbHost', None),
        ('dbUser', None),
        ('dbPWD', None),
        ('dbName', None),
        ('ticker', 'EUR_USD'),
        ('fromdate', datetime.datetime.min),
        ('todate', datetime.datetime.max),
        ('name', ''),
        )

    def __init__(self):
        self.engine = create_engine('postgresql+psycopg2://'+self.p.dbUser+':'+ self.p.dbPWD +'@'+ self.p.dbHost +'/'+ self.p.dbName)
        print(self.engine)
#         self.engine = psycopg2.connect(host=self.p.dbHost, database=self.p.dbName, user=self.p.dbUser, password=self.p.dbPWD)

    def start(self):
        self.conn = self.engine.connect()
        sql = "select a.date_price date, a.close_price as close, a.high_price high, a.open_price open, a.low_price low from minute_data a inner join symbol b on a.stock_id = b.id where b.ticker='"+ self.p.ticker + "' and a.date_price between '"+self.p.fromdate.strftime("%Y-%m-%d")+"' and '"+self.p.todate.strftime("%Y-%m-%d")+"' order by date ASC"
        self.result = self.conn.execute(sql)
        

    def stop(self):
        #self.conn.close()
        self.engine.dispose()

    def _load(self):
        one_row = self.result.fetchone()
        if one_row is None:
            return False
        self.lines.datetime[0] = date2num(one_row[0])
        self.lines.open[0] = float(one_row[1])
        self.lines.high[0] = float(one_row[2])
        self.lines.low[0] = float(one_row[3])
        self.lines.close[0] = float(one_row[4])
#         self.lines.volume[0] = int(one_row[5])
        self.lines.openinterest[0] = -1
        return True