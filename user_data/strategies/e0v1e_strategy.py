from datetime import datetime, timedelta
import talib.abstract as taa
import pandas_ta as pta
from freqtrade.persistence import Trade
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
from freqtrade.strategy import DecimalParameter, IntParameter
from functools import reduce
import warnings


# warnings.simplefilter

class E0V1E(IStrategy):

    # double 收益， 立刻退出
    minimal_roi = {
        "0" : 1
    }

    # 5m 
    timeframe = "5m"

    # candle到了，开始计算
    process_only_new_candles = True

    # 开始candle数量
    startup_candle_count = 20

    # market 交易，config 文件需要改成 other
    order_types = {
        "entry" : "market",
        "exit" : "market",
        "emergency_exit": "market",
        "force_entry": "market",
        "force_exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
        "stoploss_on_exchange_interval": 60,
        "stoploss_on_exchange_limit_ratio": 0.99,
    }

    # 止损这么高吗
    stoploss = -0.25

    # 这里的意思是，只有到了 0.03 的offset 之后，才会使用 0.002 的动态 trailing
    # 否则不trailing
    trailing_stop = True
    trailing_stop_positive = 0.002
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True

    # 不使用自定义 stoploss
    use_custom_stoploss = False

    use_exit_signal = True

    is_optimize_32 = True

    buy_rsi_fast_32 = IntParameter(20, 70, default=40, space='buy', optimize=is_optimize_32)
    buy_rsi_normal_32 = IntParameter(15, 50, default=42, space='buy', optimize=is_optimize_32)
    buy_sma15_32 = DecimalParameter(0.900, 1, default=0.973, decimals=3, space='buy', optimize=is_optimize_32)
    buy_cti_32 = DecimalParameter(-1, 1, default=0.69, decimals=2, space='buy', optimize=is_optimize_32)
    
    sell_fastx = IntParameter(50, 100, default=84, space='sell', optimize=True)

    # 卖出后96个candle之内不会重新买入
    @property
    def protections(self):
        return [
            {
                "method" : "CooldownPeriod",
                "stop_duration_conddles" : 96
            }
        ]
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict):
        """
        
        """
        dataframe['sma_15'] = taa.SMA(dataframe, timeperiod=15)         # 移动平均线 N=15
        
        dataframe['cti'] = pta.cti(dataframe['close'], len=20)          # 相关性指数 N=20

        dataframe['rsi_normal'] = taa.RSI(dataframe, timeperiod=14)     # 相对强弱指数 N=14
        
        dataframe['rsi_fast'] = taa.RSI(dataframe, timeperiod=4)        # 相对强弱指数 N=4
        
        dataframe['rsi_slow'] = taa.RSI(dataframe, timeperiod=20)       # 相对强弱指数 N=20
        
        stoch_fast = taa.STOCHF(dataframe, 5, 3, 0) # N=5, SMA_N=3      # STOCHF N=5, AVE=3
        dataframe['fastk'] = stoch_fast['fastk']

        dataframe['cci']= taa.CCI(dataframe, timeperiod=20)             # CCI Commodity Channel Index 

        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        """
        
        """
        conditions = []

        dataframe.loc[:, 'enter_tag'] = ''

        buy_1 = (
                
            (dataframe['rsi_slow'] < dataframe['rsi_slow'].shift(1)) &                  # rsi_slow 小于前一个， 长期正在下降
            (dataframe['rsi_fast'] < self.buy_rsi_fast_32.value) &                      # rsi_fast < 优化参数， 短期约束，不能超买
            (dataframe['rsi_normal'] > self.buy_rsi_normal_32.value) &                  # rsi_normal > 优化参数，中期约束，不能超卖
            (dataframe['close'] < dataframe['sma_15'] * self.buy_sma15_32.value) &      # close 小于 15-SMA * 缩小因子
            (dataframe['cti'] < self.buy_cti_32.value)                                  # 相关性指数 约束， 在相关性不高时买入
        )

        buy_new = (
            (dataframe['rsi_slow'] < dataframe['rsi_slow'].shift(1)) &                  # 重复?
            (dataframe['rsi_fast'] < 34) &                                              # 指定参数
            (dataframe['rsi_normal'] > 28) &                                                   # 指定参数
            (dataframe['close'] < dataframe['sma_15'] * 0.96) &                         # 15-SMA * 缩小因子
            (dataframe['cti'] < self.buy_cti_32.value)                                  # 重复?
        )

        conditions.append(buy_1)
        dataframe.loc[buy_1, 'enter_tag'] += 'buy_1'                                    # entry_tag += buy_1

        conditions.append(buy_new)
        dataframe.loc[buy_new, 'enter_tag'] += 'buy_new'                                # entry_tag +=buy_new

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),                                 # df.loc[buy_1 | buy_2, 'enter_long']效果是一样的，
                'enter_long'] = 1
            
    
        dataframe.loc[dataframe.index[-1], 'enter_long'] = 1

        return dataframe
    
    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        """
            检测频率更高
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)      # return latest dataframe，and time

        current_candle = dataframe.iloc[-1].squeeze()                                           # Series make sure.
        
        if current_profit > 0:
            if current_candle['fastk'] > self.sell_fastx.value:     # fastk 超买
                return "fastk_profit_sell"
            
        if current_profit > -0.03:
            if current_candle['cci'] > 80:                          # cci 超买
                return "cci_loss_sell"
        
        return None

    def populate_exit_trend(self, dataframe, metadata):
        """
            没有使用
        """
        dataframe.loc[:, ['exit_long', 'exit_tag']] = (0, 'long_out')
        return dataframe