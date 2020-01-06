#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
from btoandav20.stores import oandav20store

class OandaV20Sizer(bt.Sizer):

    params = (
        ('percents', 0),   # percents of cash
        ('amount', 0),     # fixed amount
    )

    def __init__(self, **kwargs):
        self.o = oandav20store.OandaV20Store(**kwargs)

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if position:
            return position.size

        avail = 0
        name = data.contractdetails['name']
        price = self.o.get_pricing(name)
        if price is not None:
            if isbuy:
                avail = float(price['unitsAvailable']['default']['long'])
            else:
                avail = float(price['unitsAvailable']['default']['short'])
        if self.p.percents is not 0:
            size = avail * (self.p.percents / 100)
        elif self.p.amount is not 0:
            size = (avail / cash) * self.p.amount
        else:
            size = 0
        return int(size)

class OandaV20Percent(OandaV20Sizer):

    params = (
        ('percents', 5),
    )

class OandaV20Cash(OandaV20Sizer):

    params = (
        ('amount', 50),
    )

class OandaV20Risk(OandaV20Sizer):

    params = (
        ('risk_amount', 0),        # risk amount
        ('risk_percents', 0),       # risk percents
        ('stoploss', 10),           # stop loss in pips
    )

    def _getsizing(self, comminfo, cash, data, isbuy):

        position = self.broker.getposition(data)
        if position:
            return position.size

        name = data.contractdetails['name']

        sym_from = name[:3]
        sym_to = name[4:]
        sym_src = self.o.get_currency()

        cash_to_use = 0
        if self.p.risk_percents is not 0:
            cash_to_use = cash * (self.p.risk_percents / 100)
        elif self.p.risk_amount is not 0:
            cash_to_use = self.p.risk_amount

        if sym_src != sym_to:
            # convert cash to target currency
            price = self.o.get_pricing(sym_src + '_' + sym_to)
            if price is not None:
                cash_to_use = cash_to_use / (1 / float(price['closeoutAsk']))

        size = 0
        price_per_pip = cash_to_use / self.p.stoploss
        price = self.o.get_pricing(name)
        if price is not None:
            size = price_per_pip * (1 / 10 ** data.contractdetails['pipLocation'])
            if isbuy:
                size = min(size, float(price['unitsAvailable']['default']['long']))
            else:
                size = min(size, float(price['unitsAvailable']['default']['short']))

        return int(size)

class OandaV20RiskPercent(OandaV20Sizer):

    params = (
        ('risk_percents', 5),
    )

class OandaV20RiskCash(OandaV20Sizer):

    params = (
        ('risk_amount', 50),
    )
