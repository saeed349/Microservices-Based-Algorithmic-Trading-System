####
# 1) Has the logging functionality embeded into the BT strategy file
####



import backtrader as bt
import backtrader.indicators as btind
import datetime
import psycopg2
import pandas as pd
import os



class St(bt.Strategy):
    alias = 'Simple Strategy'
    params = dict(
            period=10,
            limdays=200,
            backtest=True,
            ml_serving=False,
        )


    def log(self, arg):
        if not self.p.backtest:
            print('{} {}'.format(self.datetime.datetime(), arg))
        

    def __init__(self):
        self.ml_log = []
        self.db_run_id = None
        self.sma = [bt.indicators.SimpleMovingAverage(d, period=10) for d in self.datas]
        self.sma2 = [bt.indicators.SimpleMovingAverage(d, period=20) for d in self.datas]
        self.sma3 = [bt.indicators.SimpleMovingAverage(d, period=50) for d in self.datas]
        for i in self.sma:
            i.aliased='MovingAverageSimple_0'
        for i in self.sma2:
            i.aliased='MovingAverageSimple_1'
        for i in self.sma3:
            i.aliased='MovingAverageSimple_2'

        self.order = None
        self.buyprice = None
        self.buycomm = None
        # if arg:
        if self.p.backtest:
            self.datastatus = 1
        else:
            self.datastatus = 0


    def notify_data(self, data, status, *args, **kwargs):
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
        if status == data.LIVE:
            # self.counttostop = self.p.stopafter
            self.datastatus = 1

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.5f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.5f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.5f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))



    def next(self):
        for i, d in enumerate(self.datas):
            dt, dn = self.datetime.datetime(), d._name
            pos = self.getposition(d).size
            if self.datastatus:
                if d.close[0] > self.sma[i] and pos<=0:
                    self.order=self.close(data=d)
                    self.order=self.buy(data=d)
                    self.log('BUY CREATE {:.2f} at {}'.format(d.close[0],dn))

                elif d.close[0] < self.sma[i] and pos>=0:
                    self.order=self.close(data=d)
                    self.order=self.sell(data=d)
                    self.log('SELL CREATE {:.2f} at {}'.format(d.close[0],dn))

    def stop(self):
        print("Strategy run finished with Run ID:",self.db_run_id)