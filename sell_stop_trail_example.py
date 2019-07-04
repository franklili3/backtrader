# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 09:53:04 2019

@author: frankwin7
"""

class MyStrategy(bt.Strategy):
 
    def __init__(self):
        self.up_down = three_bars(self.data0)
        self.buy_signal = bt.indicators.CrossOver(self.data.close, self.up_down.up)
        self.sell_signal = bt.indicators.CrossDown(self.data.close, self.up_down.down)
 
 
    def next(self):
        if not self.position and self.buy_signal[0] == 1:
            self.order = self.buy(size=1)
            self.order = self.sell(size=1, exectype=bt.Order.StopTrail, trailamount=25)
