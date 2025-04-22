"""
    dry run : 模拟运行
"""
import numpy as np
import pandas as pd
from pandas import DataFrame
import talib.abstract as ta
import talib
from freqtrade.vendor import qtpylib
from freqtrade.strategy import (IStrategy, Trade, BooleanParameter, CategoricalParameter, 
                                IntParameter, merge_informative_pair, DecimalParameter)

pd.set_option('display.max_rows', None)         # 显示所有行
pd.set_option('display.max_columns', None)      # 显示所有列
pd.set_option('display.width', 1000)            # 设置显示宽度，避免换行
pd.set_option('display.max_colwidth', None)     # 显示完整的列内容（如果列内容是字符串）


class SBN_MACD_Strategy(IStrategy):
    
    timeframe = "5m"           # 15min interval

    stoploss = -0.01            # ratio that should trigger a sale.

    stoploss_on_exchange = False

    trailing_stop = True        # Adjust with max asset value.

    trailing_stop_positive = 0.02  # 

    trailing_stop_positive_offset = 0.03 # stop_loss will changed to 0.02 when assets higher than 0.03

    trailing_only_offset_is_reached = False # 

    minimal_roi = {
        "0":  0.03,         # 有0.01的利润， 立刻撤退 
        "20": 0.02,        # 20min 后 如果利润大于 0.036， 撤退
        "30": 0.01,        # 30min 后 如果利润大于 0.035， 撤退
        "40": 0.0,          # 40min 后 如果利润大于 0， 撤退
    }

    startup_candle_count = 30 # 


    def populate_indicators(self, dataframe: DataFrame, metadata: dict):
        # 技术指标计算
        # talib.RSI()
        # print(dataframe.head(10))
        dataframe['macd'], dataframe['macd_signal'], dataframe['macdhist'] = talib.MACD(real=dataframe['close']) # 使用close 


        # print("len is ", len(dataframe))

        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict):
        # 入场信号
        # dataframe.loc[(dataframe['rsi'] < 30), 'enter_long'] = 1

        dataframe.loc[
            (
                (dataframe['macdhist'] > 0)
                &
                (dataframe['macdhist'].shift(1) < 0)
                &
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1

        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict):
        # 出场信号
        # dataframe.loc[(dataframe['rsi'] > 70), 'exit_long'] = 1


        dataframe.loc[
            (
                (dataframe['macdhist'] < 0)
                &
                (dataframe['macdhist'].shift(1) > 0)
                &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1
        
        return dataframe
    
    def adjust_trade_position(self, trade, current_time, current_rate, current_profit, min_stake, max_stake,\
                              current_entry_rate, current_exit_rate, current_entry_profit, current_exit_profit, **kwargs):
        # 是否进行调仓
        return super().adjust_trade_position(trade, current_time, current_rate, current_profit, min_stake, max_stake,\
                                              current_entry_rate, current_exit_rate, current_entry_profit, current_exit_profit, **kwargs)
    
    def custom_stake_amount(self, pair, current_time, current_rate, proposed_stake, min_stake, max_stake, leverage, entry_tag, side, **kwargs):
        # 是否自定义交易数量
        return super().custom_stake_amount(pair, current_time, current_rate, proposed_stake, min_stake, max_stake, leverage, entry_tag, side, **kwargs)