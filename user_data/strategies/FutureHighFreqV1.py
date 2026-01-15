from freqtrade.strategy import IStrategy
from pandas import DataFrame
from datetime import datetime
from typing import List
import talib.abstract as ta


class FutureHighFreqV1(IStrategy):
    """
    High Frequency Trend Following Strategy V1 (Leveraged Edition)

    Optimized for 3-5x leverage:
    - Tighter stop loss (leverage amplifies losses)
    - Higher profit targets (maximize leverage benefit)
    - Strong trend confirmation
    - 5m timeframe, 10 pairs
    """

    timeframe = '5m'
    max_open_trades = 5
    stake_amount = 0.10
    startup_candle_count = 300

    # Higher profit targets for leveraged trading
    minimal_roi = {
        "0": 0.02,      # 2% quick profit
        "30": 0.015,    # 1.5% in 30min
        "60": 0.01,     # 1% in 1h
        "120": 0.005,   # 0.5% in 2h
        "240": 0        # Hold longer
    }

    # Tighter stop loss for leverage (5x leverage = 5x losses)
    stoploss = -0.01
    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.012
    trailing_only_offset_is_reached = True

    # ===== Core Strategy Parameters =====
    fast_ema = 9
    slow_ema = 21
    rsi_period = 7
    rsi_buy = 60        # More entries
    rsi_sell = 70
    adx_period = 14
    adx_threshold = 20  # Lower threshold

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
        # Buy when RSI is reasonable
        rsi_ok = dataframe['rsi'] < self.rsi_buy

        conditions = golden_cross & rsi_ok & (dataframe['volume'] > 0)
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
