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

class transactions_analyzer(bt.Analyzer):
    '''This analyzer reports the transactions occurred with each an every data in
    the system

    It looks at the order execution bits to create a ``Position`` starting from
    0 during each ``next`` cycle.

    The result is used during next to record the transactions

    Params:

      - headers (default: ``True``)

        Add an initial key to the dictionary holding the results with the names
        of the datas

        This analyzer was modeled to facilitate the integration with
        ``pyfolio`` and the header names are taken from the samples used for
        it::

          'date', 'amount', 'price', 'sid', 'symbol', 'value'

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    params = (
        ('headers', False),
        ('_pfheaders', ('date', 'amount', 'price', 'sid', 'symbol', 'value')),
    )

    def __init__(self):
        self.trades = []
        self.conn = psycopg2.connect(host=db_risk_cred.dbHost , database=db_risk_cred.dbName, user=db_risk_cred.dbUser, password=db_risk_cred.dbPWD)

    def get_analysis(self):
        return self.trades

    def start(self):
        super(transactions_analyzer, self).start()
        if self.p.headers:
            self.rets[self.p._pfheaders[0]] = [list(self.p._pfheaders[1:])]

        self._positions = collections.defaultdict(Position)
        self._idnames = list(enumerate(self.strategy.getdatanames()))

    def notify_order(self, order):
        # An order could have several partial executions per cycle (unlikely
        # but possible) and therefore: collect each new execution notification
        # and let the work for next

        # We use a fresh Position object for each round to get summary of what
        # the execution bits have done in that round
        if order.status not in [Order.Partial, Order.Completed]:
            return  # It's not an execution

        pos = self._positions[order.data._name]
        for exbit in order.executed.iterpending():
            if exbit is None:
                break  # end of pending reached

            pos.update(exbit.size, exbit.price)

    def next(self):
        # super(Transactions, self).next()  # let dtkey update
        entries = []
        for i, dname in self._idnames:
            pos = self._positions.get(dname, None)
            if pos is not None:
                size, price = pos.size, pos.price
                if size:
                    # instead of datetime.now u can use self.strategy.current_time
                    analyzer_result={'run_id':self.strategy.db_run_id,'recorded_time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'strategy':self.strategy.alias,
                    'transaction_date':self.strategy.datetime.datetime(),'size':size, 'price':price, 'sid':i, 'ticker':dname, 'value':(-size * price)}
                    write_to_db.write_to_db(conn=self.conn, data_dict=analyzer_result, table='positions') 
                    self.trades.append(analyzer_result)
        # if entries:
        #     self.rets[self.strategy.datetime.datetime()] = entries

        self._positions.clear()