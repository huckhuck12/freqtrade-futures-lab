from freqtrade.strategy import IStrategy
from pandas import DataFrame
from datetime import datetime
from typing import List
import talib.abstract as ta


class FutureHighFreqV1(IStrategy):
    """
    High Frequency Trend Following Strategy V1 (High Yield Edition)

    Simple and effective:
    - Buy when RSI is low and EMA crosses up
    - Sell when EMA crosses down or RSI is high
    - Aggressive profit targets
    - 5m timeframe, 10 pairs
    """

    timeframe = '5m'
    max_open_trades = 10
    stake_amount = 0.10
    startup_candle_count = 300

    minimal_roi = {
        "0": 0.015,
        "30": 0.008,
        "90": 0.004,
        "180": 0.002,
        "360": 0
    }

    stoploss = -0.015
    trailing_stop = True
    trailing_stop_positive = 0.006
    trailing_stop_positive_offset = 0.01
    trailing_only_offset_is_reached = True

    # ===== Core Strategy Parameters =====
    fast_ema = 9
    slow_ema = 21
    rsi_period = 7
    rsi_buy = 55
    rsi_sell = 70
    adx_period = 14
    adx_threshold = 25

    cooldown_period = 3

    def informative_pairs(self) -> List[tuple]:
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['fast_ema'] = ta.EMA(dataframe, timeperiod=self.fast_ema)
        dataframe['slow_ema'] = ta.EMA(dataframe, timeperiod=self.slow_ema)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=self.adx_period)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Golden cross
        golden_cross = (
            (dataframe['fast_ema'] > dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) <= dataframe['slow_ema'].shift(1))
        )
        # Buy when RSI is reasonable (not overbought)
        conditions = golden_cross & (dataframe['rsi'] < self.rsi_buy) & (dataframe['volume'] > 0)
        dataframe.loc[conditions, 'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Death cross
        death_cross = (
            (dataframe['fast_ema'] < dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) >= dataframe['slow_ema'].shift(1))
        )
        # Or RSI overbought
        overbought = dataframe['rsi'] > self.rsi_sell
        conditions = (death_cross | overbought) & (dataframe['volume'] > 0)
        dataframe.loc[conditions, 'exit'] = 1
        return dataframe
