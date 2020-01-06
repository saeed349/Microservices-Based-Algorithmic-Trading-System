#####
# Ran, Broke and Mod from https://github.com/backtrader/backtrader/blob/master/backtrader/analyzers/transactions.py
#####

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import collections

import backtrader as bt
import psycopg2
import q_credentials.db_risk_cred as db_risk_cred
import q_tools.write_to_db as write_to_db
import datetime

class strat_performance_analyzer(bt.Analyzer):

    def __init__(self):
        self.performance = {}
        self.conn = psycopg2.connect(host=db_risk_cred.dbHost , database=db_risk_cred.dbName, user=db_risk_cred.dbUser, password=db_risk_cred.dbPWD)
        self.analyzer_sharpe = bt.analyzers.SharpeRatio()
        self.analyzer_returns = bt.analyzers.Returns()
        self.analyzer_sqn = bt.analyzers.SQN()
        self.analyzer_drawdown = bt.analyzers.DrawDown()
        self.analyzer_tradeanalyzer = bt.analyzers.TradeAnalyzer()

    def stop(self):
        self.performance['run_id']=self.strategy.db_run_id
        self.performance['total_open']=self.analyzer_tradeanalyzer.get_analysis().total.open
        self.performance['total_closed'] = self.analyzer_tradeanalyzer.get_analysis().total.closed
        self.performance['total_won'] = self.analyzer_tradeanalyzer.get_analysis().won.total
        self.performance['total_lost'] = self.analyzer_tradeanalyzer.get_analysis().lost.total
        self.performance['win_streak'] = self.analyzer_tradeanalyzer.get_analysis().streak.won.longest
        self.performance['lose_streak'] = self.analyzer_tradeanalyzer.get_analysis().streak.lost.longest
        self.performance['pnl_net'] = round(self.analyzer_tradeanalyzer.get_analysis().pnl.net.total,2)
        self.performance['strike_rate'] = (self.performance['total_won'] / self.performance['total_closed']) * 100
        self.performance['sqn']=self.analyzer_sqn.get_analysis()['sqn']
        self.performance['total_compound_return']=self.analyzer_returns.get_analysis()['rtot']
        self.performance['avg_return']=self.analyzer_returns.get_analysis()['ravg']
        self.performance['annual_norm_return']=self.analyzer_returns.get_analysis()['rnorm100']
        self.performance['max_draw_per']=self.analyzer_drawdown.get_analysis()['max']['drawdown']
        self.performance['max_draw_val']=self.analyzer_drawdown.get_analysis()['max']['moneydown']
        self.performance['max_draw_len']=self.analyzer_drawdown.get_analysis()['max']['len']

        write_to_db.write_to_db(conn=self.conn, data_dict=self.performance, table='strategy_performance')


    def get_analysis(self):
        return self.performance