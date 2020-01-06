import backtrader as bt
import backtrader.indicators as btind
import datetime
import psycopg2
import pandas as pd
import os

import mlflow.pyfunc

class St(bt.Strategy):
    alias = 'Simple Strategy'
    params = dict(
        period=10,
        limdays=200,
        backtest=True,
        ml_serving=False,
        model_uri="24cbdab283244fac8d54405d58b2bbf1"
    )


    def log(self, arg):
        if not self.p.backtest:
            print('{} {}'.format(self.datetime.datetime(), arg))
        

    def __init__(self): 
        self.db_run_id = None
        self.rsi = [bt.indicators.RSI(d, period=30) for d in self.datas]

        self.stoc = [bt.indicators.Stochastic(d, period=20) for d in self.datas]
        self.atr = [bt.indicators.ATR(d, period=5) for d in self.datas]
        for i in self.rsi:
            i.aliased='RSI'
        for i in self.stoc:
            i.aliased='STOCHASTIC'
        for i in self.atr:
            i.aliased='ATR'

        self.order = None
        self.buyprice = None
        self.buycomm = None
        # if arg:
        if self.p.backtest:
            self.datastatus = 1
        else:
            self.datastatus = 0

        if self.p.ml_serving:
            print("s3://mlflow-models/"+self.p.model_uri+"/artifacts/model")
            self.model_predict=mlflow.pyfunc.load_model(model_uri=("s3://mlflow-models/"+self.p.model_uri+"/artifacts/model"))


    def notify_data(self, data, status, *args, **kwargs):
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
        if status == data.LIVE:
            self.datastatus = 1

    
    def notify_order(self, order):        
        if (order.status>1): # 0 and 1 are created and submitted
            self.log('Order Status: {}: Ref: {}, Size: {}, Price: {}' \
                .format(order.Status[order.status], order.ref, order.size,
                        'NA' if not order.price else round(order.price,5)))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.5f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))



    def next(self): 
        for i, d in enumerate(self.datas):
            dt, dn = self.datetime.datetime(), d._name
            pos = self.getposition(d).size
            order_valid = datetime.timedelta(self.p.limdays)
            if self.datastatus and pos==0:
                if self.p.ml_serving:
                    pred=self.model_predict.predict([[self.rsi[i][0],self.stoc[i][0]]])[0]
                    if pred>0:
                        price_sl = d.close[0]-(self.atr[0] * 1)
                        price_tp = d.close[0]+(self.atr[0] * 2)
                        self.order=self.buy_bracket(data=d,exectype=bt.Order.Market , stopprice=price_sl, limitprice=price_tp, valid=order_valid) #, valid=order_valid,price=None
                        self.log('BUY CREATE {:.2f} at {}'.format(d.close[0],dn))
                    elif pred<=0:
                        price_sl = d.close[0]+(self.atr[0] * 1)
                        price_tp = d.close[0]-(self.atr[0] * 2)
                        self.order=self.sell_bracket(data=d,exectype=bt.Order.Market, stopprice=price_sl, limitprice=price_tp, valid=order_valid)
                        self.log('SELL CREATE {:.2f} at {}'.format(d.close[0],dn))

                elif self.rsi[i] < 40:
                    price_sl = d.close[0]-(self.atr[0] * 1)
                    price_tp = d.close[0]+(self.atr[0] * 2)
                    self.order=self.buy_bracket(data=d,exectype=bt.Order.Market , stopprice=price_sl, limitprice=price_tp, valid=order_valid) #, valid=order_valid,price=None
                    self.log('BUY CREATE {:.2f} at {}'.format(d.close[0],dn))

                elif self.rsi[i] > 60:
                    price_sl = d.close[0]+(self.atr[0] * 1)
                    price_tp = d.close[0]-(self.atr[0] * 2)
                    self.order=self.sell_bracket(data=d,exectype=bt.Order.Market, stopprice=price_sl, limitprice=price_tp, valid=order_valid)
                    self.log('SELL CREATE {:.2f} at {}'.format(d.close[0],dn))

    def stop(self):
        print("Strategy run finished with Run ID:",self.db_run_id)