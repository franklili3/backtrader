# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 13:01:35 2019

@author: frankwin7
"""
def __init__(self):
    ...
 
    # Let's create the moving averages as before
    ma1 = bt.ind.SMA(self.data0, period=self.p.period)
    ma2 = bt.ind.SMA(self.data1, period=self.p.period)
 
    # Use line delay notation (-x) to get a ref to the -1 point
    ma1_pct = ma1 / ma1(-1) - 1.0  # The ma1 percentage part
    ma2_pct = ma2 / ma2(-1) - 1.0  # The ma2 percentage part
 
    self.buy_sig = ma1_pct > ma2_pct  # buy signal
    self.sell_sig = ma1_pct <= ma2_pct  # sell signal
def next(self):
    ...
    # Not yet ... we MIGHT BUY if ...
    if self.buy_sig:
    ...
 
    ...
    # Already in the market ... we might sell
    if self.sell_sig:
    ...

