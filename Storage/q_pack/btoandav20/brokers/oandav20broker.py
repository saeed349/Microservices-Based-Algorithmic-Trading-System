#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import collections
from copy import copy
from datetime import date, datetime, timedelta
import threading

from backtrader.feed import DataBase
from backtrader import (TimeFrame, num2date, date2num, BrokerBase,
                        Order, BuyOrder, SellOrder, OrderBase, OrderData)
from backtrader.utils.py3 import bytes, with_metaclass, MAXFLOAT
from backtrader.metabase import MetaParams
from backtrader.comminfo import CommInfoBase
from backtrader.position import Position
from backtrader.utils import AutoDict, AutoOrderedDict
from backtrader.comminfo import CommInfoBase

from ..stores import oandav20store

class OandaV20CommInfo(CommInfoBase):
    def getvaluesize(self, size, price):
        # In real life the margin approaches the price
        return abs(size) * price

    def getoperationcost(self, size, price):
        '''Returns the needed amount of cash an operation would cost'''
        # Same reasoning as above
        return abs(size) * price


class MetaOandaV20Broker(BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        '''Class has already been created ... register'''
        # Initialize the class
        super(MetaOandaV20Broker, cls).__init__(name, bases, dct)
        oandav20store.OandaV20Store.BrokerCls = cls


class OandaV20Broker(with_metaclass(MetaOandaV20Broker, BrokerBase)):
    '''Broker implementation for Oanda v20.

    This class maps the orders/positions from Oanda to the
    internal API of ``backtrader``.

    Params:

      - ``use_positions`` (default:``True``): When connecting to the broker
        provider use the existing positions to kickstart the broker.

        Set to ``False`` during instantiation to disregard any existing
        position
    '''
    params = (
        ('use_positions', True),
    )

    def __init__(self, **kwargs):
        super(OandaV20Broker, self).__init__()
        self.o = oandav20store.OandaV20Store(**kwargs)

        self.orders = collections.OrderedDict()  # orders by order id
        self.notifs = collections.deque()  # holds orders which are notified

        self.opending = collections.defaultdict(list)  # pending transmission
        self.brackets = dict()  # confirmed brackets

        self.startingcash = self.cash = 0.0
        self.startingvalue = self.value = 0.0
        self.positions = collections.defaultdict(Position)
        self.addcommissioninfo(self, OandaV20CommInfo(mult=1.0, stocklike=False))

    def start(self):
        super(OandaV20Broker, self).start()
        self.addcommissioninfo(self, OandaV20CommInfo(mult=1.0, stocklike=False))
        self.o.start(broker=self)
        self.startingcash = self.cash = cash = self.o.get_cash()
        self.startingvalue = self.value = self.o.get_value()

        if self.p.use_positions:
            for p in self.o.get_positions():
                print('position for instrument:', p['instrument'])
                size = float(p['long']['units']) + float(p['short']['units'])
                price = float(p['long']['averagePrice']) if size > 0 else float(p['short']['averagePrice'])
                self.positions[p['instrument']] = Position(size, price)

    def data_started(self, data):
        pos = self.getposition(data)

        if pos.size == 0:
            return

        if pos.size < 0:
            order = SellOrder(data=data,
                              size=pos.size, price=pos.price,
                              exectype=Order.Market,
                              simulated=True)
        else:
            order = BuyOrder(data=data,
                             size=pos.size, price=pos.price,
                             exectype=Order.Market,
                             simulated=True)

        order.addcomminfo(self.getcommissioninfo(data))
        order.execute(0, pos.size, pos.price,
                      0, 0.0, 0.0,
                      pos.size, 0.0, 0.0,
                      0.0, 0.0,
                      pos.size, pos.price)

        order.completed()
        self.notify(order)

    def stop(self):
        super(OandaV20Broker, self).stop()
        self.o.stop()

    def getcash(self):
        # This call cannot block if no answer is available from oanda
        self.cash = cash = self.o.get_cash()
        return cash

    def getvalue(self, datas=None):
        self.value = self.o.get_value()
        return self.value

    def getposition(self, data, clone=True):
        # return self.o.getposition(data._dataname, clone=clone)
        pos = self.positions[data._dataname]
        if clone:
            pos = pos.clone()

        return pos

    def orderstatus(self, order):
        o = self.orders[order.ref]
        return o.status

    def _submit(self, oref):
        order = self.orders[oref]
        order.submit()
        self.notify(order)

    def _reject(self, oref):
        order = self.orders[oref]
        order.reject()
        self.notify(order)

    def _accept(self, oref):
        order = self.orders[oref]
        order.accept()
        self.notify(order)

    def _cancel(self, oref):
        order = self.orders[oref]
        order.cancel()
        self.notify(order)

    def _expire(self, oref):
        order = self.orders[oref]
        order.expire()
        self.notify(order)

    def _bracketize(self, order):
        pref = getattr(order.parent, 'ref', order.ref)  # parent ref or self
        br = self.brackets.pop(pref, None)  # to avoid recursion
        if br is None:
            return

        if len(br) == 3:  # all 3 orders in place, parent was filled
            br = br[1:]  # discard index 0, parent
            for o in br:
                o.activate()  # simulate activate for children
            self.brackets[pref] = br  # not done - reinsert children

        elif len(br) == 2:  # filling a children
            oidx = br.index(order)  # find index to filled (0 or 1)
            self._cancel(br[1 - oidx].ref)  # cancel remaining (1 - 0 -> 1)

    def _fill_external(self, data, size, price):
        if size == 0:
            return

        pos = self.getposition(data, clone=False)
        pos.update(size, price)

        if size < 0:
            order = SellOrder(data=data,
                              size=size, price=price,
                              exectype=Order.Market,
                              simulated=True)
        else:
            order = BuyOrder(data=data,
                             size=size, price=price,
                             exectype=Order.Market,
                             simulated=True)

        order.addcomminfo(self.getcommissioninfo(data))
        order.execute(0, size, price,
                      0, 0.0, 0.0,
                      size, 0.0, 0.0,
                      0.0, 0.0,
                      size, price)

        order.completed()
        self.notify(order)

    def _fill(self, oref, size, price, reason, **kwargs):
        order = self.orders[oref]
        if not order.alive():  # can be a bracket
            pref = getattr(order.parent, 'ref', order.ref)
            if pref not in self.brackets:
                msg = ('Order fill received for {}, with price {} and size {} '
                       'but order is no longer alive and is not a bracket. '
                       'Unknown situation {}')
                msg = msg.format(order.ref, price, size, reason)
                self.o.put_notification(msg)
                return

            # [main, stopside, takeside], neg idx to array are -3, -2, -1
            if reason == 'STOP_LOSS_ORDER':
                order = self.brackets[pref][-2]
            elif reason == 'TAKE_PROFIT_ORDER':
                order = self.brackets[pref][-1]
            else:
                msg = ('Order fill received for {}, with price {} and size {} '
                       'but order is no longer alive and is a bracket. '
                       'Unknown situation {}')
                msg = msg.format(order.ref, price, size, reason)
                self.o.put_notification(msg)
                return

        data = order.data
        pos = self.getposition(data, clone=False)
        psize, pprice, opened, closed = pos.update(size, price)
        comminfo = self.getcommissioninfo(data)

        closedvalue = closedcomm = 0.0
        openedvalue = openedcomm = 0.0
        margin = pnl = 0.0

        order.execute(data.datetime[0], size, price,
                      closed, closedvalue, closedcomm,
                      opened, openedvalue, openedcomm,
                      margin, pnl,
                      psize, pprice)

        if order.executed.remsize:
            order.partial()
            self.notify(order)
        else:
            order.completed()
            self.notify(order)
            self._bracketize(order)

    def _transmit(self, order):
        oref = order.ref
        pref = getattr(order.parent, 'ref', oref)  # parent ref or self

        if order.transmit:
            if oref != pref:  # children order
                # Put parent in orders dict, but add stopside and takeside
                # to order creation. Return the takeside order, to have 3s
                takeside = order  # alias for clarity
                parent, stopside = self.opending.pop(pref)
                for o in parent, stopside, takeside:
                    self.orders[o.ref] = o  # write them down

                self.brackets[pref] = [parent, stopside, takeside]
                self.o.order_create(parent, stopside, takeside)
                return takeside  # parent was already returned

            else:  # Parent order, which is being transmitted
                self.orders[order.ref] = order
                return self.o.order_create(order)

        # Not transmitting
        self.opending[pref].append(order)
        return order

    def buy(self, owner, data,
            size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            parent=None, transmit=True,
            **kwargs):

        order = BuyOrder(owner=owner, data=data,
                         size=size, price=price, pricelimit=plimit,
                         exectype=exectype, valid=valid, tradeid=tradeid,
                         trailamount=trailamount, trailpercent=trailpercent,
                         parent=parent, transmit=transmit)

        order.addinfo(**kwargs)
        order.addcomminfo(self.getcommissioninfo(data))
        return self._transmit(order)

    def sell(self, owner, data,
             size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, oco=None,
             trailamount=None, trailpercent=None,
             parent=None, transmit=True,
             **kwargs):

        order = SellOrder(owner=owner, data=data,
                          size=size, price=price, pricelimit=plimit,
                          exectype=exectype, valid=valid, tradeid=tradeid,
                          trailamount=trailamount, trailpercent=trailpercent,
                          parent=parent, transmit=transmit)

        order.addinfo(**kwargs)
        order.addcomminfo(self.getcommissioninfo(data))
        return self._transmit(order)

    def cancel(self, order):
        o = self.orders[order.ref]
        if order.status == Order.Cancelled:  # already cancelled
            return

        return self.o.order_cancel(order)

    def notify(self, order):
        self.notifs.append(order.clone())

    def get_notification(self):
        if not self.notifs:
            return None

        return self.notifs.popleft()

    def next(self):
        self.notifs.append(None)  # mark notification boundary
