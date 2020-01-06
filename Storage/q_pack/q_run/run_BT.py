import argparse
import datetime
import glob
import os.path
import backtrader as bt


import btoandav20
import pytz

import q_datafeeds.bt_datafeed_postgres as bt_datafeed_postgres
from q_strategies import *
import q_credentials.oanda_cred as oanda_cred
import q_credentials.db_secmaster_cred as db_cred
import q_analyzers.bt_strat_perform_analyzer as bt_strat_performance_analyzer
import q_analyzers.bt_pos_perform_analyzer as bt_pos_performance_analyzer
import q_analyzers.bt_transaction_analyzer as bt_trans_analyzer
import q_analyzers.bt_strategy_id_analyzer as bt_strategy_id_analyzer
import q_analyzers.bt_logger_analyzer as bt_logger_analyzer
import q_tools.args_parse_other as args_parse_other

def run(args=None): 
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed kwargs
    dkwargs = dict(**eval('dict(' + args.dargs + ')'))

    ticker_list=args.tickers[0].split(',')

    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    if args.fromdate:
        fmt = dtfmt + tmfmt * ('T' in args.fromdate)
        dkwargs['fromdate'] = datetime.datetime.strptime(args.fromdate, fmt)    

    if args.todate:
        fmt = dtfmt + tmfmt * ('T' in args.todate)
        dkwargs['todate'] = datetime.datetime.strptime(args.todate, fmt)

    cerebro.addanalyzer(bt_trans_analyzer.transactions_analyzer,_name='position_list')
    cerebro.addanalyzer(bt_strategy_id_analyzer.strategy_id_analyzer,_name='strategy_id')
    cerebro.addanalyzer(bt_strat_performance_analyzer.strat_performance_analyzer,_name='strat_perf')
    cerebro.addanalyzer(bt_pos_performance_analyzer.pos_performance_analyzer,_name='pos_perf')
    
    if args.ml_log:
        cerebro.addanalyzer(bt_logger_analyzer.logger_analyzer,_name='ml_logger')

    if args.mode=='live':
        oandastore = btoandav20.stores.OandaV20Store(token=args.broker_token, account=args.broker_account, practice=True)
        for ticker in ticker_list:
            data = oandastore.getdata(dataname = ticker,timeframe = bt.TimeFrame.Minutes,compression=1,tz=pytz.timezone('US/Eastern'))
            cerebro.adddata(data)
        cerebro.broker = oandastore.getbroker()
        cerebro.addstrategy(globals()[args.strat_name].St, backtest=False)

    elif args.mode=='backtest':

        for ticker in ticker_list:
            data = bt_datafeed_postgres.PostgreSQL_Daily(dbHost=db_cred.dbHost,dbUser=db_cred.dbUser,dbPWD=db_cred.dbPWD,dbName=db_cred.dbName,ticker=ticker, name=ticker,**dkwargs)
            cerebro.adddata(data)
        cerebro.broker.setcash(args.cash)
        cerebro.addstrategy(globals()[args.strat_name].St, **args.strat_param)
 
    

    cerebro.addsizer(bt.sizers.FixedSize, stake=1000)


    results = cerebro.run(tradehistory=True)  

    pnl = cerebro.broker.get_value() - args.cash
    print('Profit ... or Loss: {:.2f}'.format(pnl))

    strats = results
    if args.plot:
        cerebro.plot(style='candlestick',iplot=False,volume=False)
   


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=('Rebalancing with the Conservative Formula'),
    )

    parser.add_argument('--tickers', nargs='*' ,required=False,default=['EUR_USD,GBP_USD'], type=str,
                        help='Pass the tickers with space')

    parser.add_argument('--dargs', default='',
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--fromdate', required=False, default='2010-1-1',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='2019-7-30',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--cash', default=10000, type=float,
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--strat_name', required=False, default='simple_strategy_2', 
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--strat_param', required=False, default=dict(ml_serving=False),
                        action=args_parse_other.StoreDictKeyPair, metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--ml_log', required=False, default=False, type=args_parse_other.str2bool, const=True, nargs='?',
                        help='To save ML log or not')
    
    parser.add_argument('--mode', required=False, default='backtest',   
                        help='Live or Backtest')

    parser.add_argument('--broker_token', required=False, default=oanda_cred.token_practice,
                        help='Oanda Broker Token id')

    parser.add_argument('--broker_account', required=False, default=oanda_cred.acc_id_practice,
                        help='Oanda Broker Account id')

    parser.add_argument('--plot', required=False, default=False, type=args_parse_other.str2bool, const=True, nargs='?',
                    help='Plot the results')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    run()

