#####
# Ran, Broke and Mod from https://github.com/backtrader/backtrader/blob/master/backtrader/analyzers/transactions.py
#####

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import collections

import backtrader as bt
from backtrader import Order, Position
import psycopg2
import q_credentials.db_risk_cred as db_risk_cred
import datetime
import q_tools.write_to_db as write_to_db

class strategy_id_analyzer(bt.Analyzer):

    def __init__(self):
        self.strat_info = {}
        self.conn = psycopg2.connect(host=db_risk_cred.dbHost , database=db_risk_cred.dbName, user=db_risk_cred.dbUser, password=db_risk_cred.dbPWD)
        self.current_time=datetime.datetime.now()

    def get_analysis(self):
        return self.strat_info

    def start(self):
        info_run_type = 'Backtest' if self.strategy.p.backtest else 'Live'
        info_tickers=','.join([d for d in (self.strategy.getdatanames())])
        info_indicators = ','.join([i.aliased for i in (self.strategy.getindicators())])
        info_timeframe = self.strategy.data0._timeframe # This is currently a number, have to change it later
        if self.strategy.p.backtest:
            info_start_date =  bt.num2date(self.strategy.data0.fromdate) # would have to change for live due to the backfill.
            info_end_date =  bt.num2date(self.strategy.data0.todate)
        else:
            info_start_date =  self.current_time # would have to change for live due to the backfill.
            info_end_date =  None

            info_end_date =None
        info_account = ""
        info_log_file = ""
        self.strat_info={'run_type':info_run_type,'recorded_time':self.current_time,'start_time':info_start_date,'end_time':info_end_date,
                    'strategy':self.strategy.alias,'tickers':info_tickers,'indicators':info_indicators,'frequency':info_timeframe,'account':info_account,'log_file':info_log_file}

        self.strategy.db_run_id=write_to_db.write_to_db(conn=self.conn, data_dict=self.strat_info, table='run_information',return_col='run_id')

 