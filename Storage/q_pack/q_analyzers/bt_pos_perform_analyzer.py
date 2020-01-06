####
# Important Note: If there's already an open position in the account during live trading, this will error out because we are recording round trip trades 
####
import backtrader as bt
import datetime

import psycopg2
import q_credentials.db_risk_cred as db_risk_cred
import q_tools.write_to_db as write_to_db

class pos_performance_analyzer(bt.Analyzer):

    def get_analysis(self):

        return self.trades


    def __init__(self):

        self.trades = []
        self.cumprofit = 0.0
        self.conn = psycopg2.connect(host=db_risk_cred.dbHost , database=db_risk_cred.dbName, user=db_risk_cred.dbUser, password=db_risk_cred.dbPWD)

    def notify_trade(self, trade):

        if trade.isclosed:

            brokervalue = self.strategy.broker.getvalue()

            dir = 'short'
            if trade.history[0].event.size > 0: dir = 'long'

            pricein = trade.history[len(trade.history)-1].status.price
            priceout = trade.history[len(trade.history)-1].event.price
            datein = bt.num2date(trade.history[0].status.dt)
            dateout = bt.num2date(trade.history[len(trade.history)-1].status.dt)
            if trade.data._timeframe >= bt.TimeFrame.Days:
                datein = datein.date()
                dateout = dateout.date()

            pcntchange = 100 * priceout / pricein - 100
            pnl = trade.history[len(trade.history)-1].status.pnlcomm
            pnlpcnt = 100 * pnl / brokervalue
            barlen = trade.history[len(trade.history)-1].status.barlen
            pbar = (pnl / barlen) if barlen else pnl # to avoid divide by 0 error
            self.cumprofit += pnl

            size = value = 0.0
            for record in trade.history:
                if abs(size) < abs(record.status.size):
                    size = record.status.size
                    value = record.status.value

            highest_in_trade = max(trade.data.high.get(ago=0, size=barlen+1))
            lowest_in_trade = min(trade.data.low.get(ago=0, size=barlen+1))
            hp = 100 * (highest_in_trade - pricein) / pricein
            lp = 100 * (lowest_in_trade - pricein) / pricein
            if dir == 'long':
                mfe = hp
                mae = lp
            if dir == 'short':
                mfe = -lp
                mae = -hp

            analyzer_result={'run_id':self.strategy.db_run_id,'strategy':self.strategy.alias,'recorded_time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'ref': trade.ref, 'ticker': trade.data._name, 'direction': dir,
                 'datein': datein, 'pricein': pricein, 'dateout': dateout, 'priceout': priceout,
                 'change_percentage': round(pcntchange, 2), 'pnl': pnl, 'pnl_percentage': round(pnlpcnt, 2),
                 'size': size, 'value': value, 'cumpnl': self.cumprofit,
                 'nbars': barlen, 'pnl_per_bar': round(pbar, 2),
                 'mfe_percentage': round(mfe, 2), 'mae_percentage': round(mae, 2)}

            write_to_db.write_to_db(conn=self.conn, data_dict=analyzer_result, table='position_performance')  
            self.trades.append(analyzer_result)
