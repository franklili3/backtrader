# -*- coding: utf-8 -*-
"""
Created on Wed Jul  3 09:05:20 2019

@author: frankwin7
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import pandas as pd
import statistics

# Import the backtrader platform
import backtrader as bt

class diff_pct_close_ema_ind(bt.Indicator):
    lines = ('dpce',)

    def __init__(self, emaperiod = self.params.emaperiod):
        self.params.emaperiod = emaperiod
        
        # Add a MovingAverageSimple indicator
        self.ema = bt.indicators.ExplonentialMovingAverage(
                self.datas[0], period=self.params.emaperiod)
        
    def next(self):
        self.dataclose = self.datas[0].close
        self.lines.dpce[0] = self.dataclose / self.ema[0] - 1
 
# Create a Stratey
class EmaMeanReversionStrategy(bt.Strategy):
    params = (
        ('emaperiod', 1000),
        ('meanperiod', 201600),
        ('printlog', False),
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.PositiveAbnormalIsOverDiff_pct_close_ema = False
        self.Diff_pct_close_emaIsOverNegativeAbnormal = False 
        self.MeanIsOverDiff_pct_close_ema = False
        self.Diff_pct_close_emaIsOverMean = False 
        self.diff_pct_close_ema = 0
        self.diff_pct_close_ema_sum = 0
        self.diff_pct_close_ema_list = []
        self.diff_pct_close_ema_mean = None
        self.diff_pct_close_ema_std = None
        self.negative_abnormal = None
        self.positive_abnormal = None
        self.dpce = diff_pct_close_ema_ind(emaperiod = self.params.emaperiod, subplot=False)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            if self.ema[0] == 0: return
            self.diff_pct_close_ema_list.append(self.dpce[0])
       
            if len(self.diff_pct_close_ema_list) % self.longPeriod == 0:
                self.diff_pct_close_ema_mean = statistics.mean(self.diff_pct_close_ema_list)
                self.diff_pct_close_ema_std = statistics.stdev(self.diff_pct_close_ema_list)
                self.negative_abnormal = self.diff_pct_close_ema_mean - self.diff_pct_close_ema_std
                self.positive_abnormal = self.diff_pct_close_ema_mean + self.diff_pct_close_ema_std
                self.diff_pct_close_ema_list = []
            if self.negative_abnormal is not None:
                if not self.Portfolio.Invested and self.Diff_pct_close_emaIsOverNegativeAbnormal and self.dpce[0] < self.negative_abnormal:
                    # BUY, BUY, BUY!!! (with all possible default parameters)
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()
                elif not self.Portfolio.Invested and self.PositiveAbnormalIsOverDiff_pct_close_ema and self.dpce[0] > self.positive_abnormal:
                    # SELL, SELL, SELL!!! (with all possible default parameters)
                    self.log('SELL CREATE, %.2f' % self.dataclose[0])
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.sell()
                elif self.Portfolio[self.symbol].IsLong and self.MeanIsOverDiff_pct_close_ema and self.dpce[0] > self.diff_pct_close_ema_mean:
                    # CLOSE (with all possible default parameters)
                    self.log('CLOSE CREATE, %.2f' % self.dataclose[0])
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.close()
                elif self.Portfolio[self.symbol].IsShort and self.Diff_pct_close_emaIsOverMean and self.dpce[0] < self.diff_pct_close_ema_mean:
                    # CLOSE (with all possible default parameters)
                    self.log('CLOSE CREATE, %.2f' % self.dataclose[0])
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.close()
                self.PositiveAbnormalIsOverDiff_pct_close_ema = self.positive_abnormal > self.dpce[0]
                self.Diff_pct_close_emaIsOverNegativeAbnormal = self.dpce[0] > self.negative_abnormal
                self.MeanIsOverDiff_pct_close_ema = self.dpce[0] < self.diff_pct_close_ema_mean
                self.Diff_pct_close_emaIsOverMean = not self.MeanIsOverDiff_pct_close_ema
 
    def stop(self):
        self.log('(MA Period %2d) Ending Value %.2f' %
                 (self.params.maperiod, self.broker.getvalue()), doprint=True)

class Rerverser(bt.Size):
    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if isbuy:
            if position == 0: 
                size = cash / (data * (1 + comminfo))
            else:
                size = position.size
        else:
            if position == 0: 
                size = cash / (data * (1 + comminfo))
            else:
                 size = position.size
        return size

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    # Add a strategy
    cerebro.addstrategy(EmaMeanReversionStrategy)
    cerebro.addsizer(Rerverser)
'''    # optimize strategy
    strats = cerebro.optstrategy(
        TestStrategy,
        maperiod=range(10, 31))
'''
    # Create a Data Feed
    # 本地数据
    # parase_dates = True是为了读取csv为dataframe的时候能够自动识别datetime格式的字符串，big作为index
    # 注意，这里最后的pandas要符合backtrader的要求的格式
    dataframe = pd.read_csv('bitfinex_BTCUSD_min_20180601_20190531.csv', index_col=0, parse_dates=True)
    dataframe['openinterest'] = 0
    data = bt.feeds.PandasData(dataname=dataframe,
        fromdate = datetime.datetime(2018, 6, 1, 0, 1),
        todate = datetime.datetime(2019, 5, 31, 23, 59)
    )
    
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)


    # Set the commission
    cerebro.broker.setcommission(commission=0.0035)

    # Run over everything
    cerebro.run()

