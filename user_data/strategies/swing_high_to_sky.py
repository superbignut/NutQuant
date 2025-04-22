from freqtrade.strategy import (IStrategy, IntParameter)
from functools import reduce
from pandas import DataFrame
import talib
import talib.abstract as taa
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy as np


cciBuyTP = 72
cciBuyVal = -175
cciSellTP = 66
cciSellVal = -106

rsiBuyTP = 36
rsiBuyVal = 90
rsiSellTP = 45
rsiSellVal = 88

class SwingHighToSky(IStrategy):
    
    INTERFACE_VERSION = 3

    timeframe = '15m'

    minimal_roi = {
        "0" : 0.27,
        "33" : 0.08,
        "64" : 0.04,
        "244" : 0
    }

    # 这里是第一个要优化的参数，也就是买入的CCI，一般都是 100
    buy_cci = IntParameter(low=-200, high=200, default=100, space="buy", optimize= True) 
    # 这里是第二个要优化的参数，是CCI的取多少天平均值的那个n
    buy_cciTime = IntParameter(low=10, high=80, default=20, space="buy", optimize= True)

    # 
    buy_rsi = IntParameter(low=10, high=90, default=30, space="buy", optimize= True)
    buy_rsiTime = IntParameter(low=10, high=80, default=26, space="buy", optimize= True)

    # CCI的sell参数均同上
    sell_cci = IntParameter(low=-200, high=200, default=100, space="sell", optimize= True)
    sell_cciTime = IntParameter(low=10, high=80, default=20, space="sell", optimize= True)

    # 
    sell_rsi = IntParameter(low=10, high=90, default=30, space="sell", optimize= True)
    sell_rsiTime = IntParameter(low=10, high=80, default=26, space="sell", optimize= True)

    buy_params = {
        "buy_cci":-175,
        "buy_cciTime":72,
        "sell_rsi":90,
        "sell_rsiTime":36
    }

    sell_params = {
        "buy_cci":-106,
        "buy_cciTime":66,
        "sell_rsi":88,
        "sell_rsiTime":45
    }

    def informative_pairs(self):
        # 提供额外的数据信息
        return []
    
    def populate_indicators(self, dataframe:DataFrame, metadata:dict):
        
        for val in self.buy_cciTime.range:
            dataframe[f'cci-buy-{val}'] = taa.CCI(dataframe, timeperiod=val)

        for val in self.sell_cciTime.range:
            dataframe[f'cci-sell-{val}'] = taa.CCI(dataframe, timeperiod=val)

        