from freqtrade.strategy import IStrategy
from pandas import DataFrame
from typing import List
import talib.abstract as ta


class FutureHighFreqV1(IStrategy):
    """
    High Frequency Trend Following Strategy V1

    Strategy Logic:
    - Uses EMA crossover and price breakouts for trend identification
    - Dynamic pair selection based on volatility and volume
    - Fast entry/exit with trailing stop for profit protection

    Timeframe: 1m
    Pairs: 10 high-volatility futures pairs
    """

    timeframe = '1m'
    max_open_trades = 10
    stake_amount = 0.10
    startup_candle_count = 200

    minimal_roi = {
        "0": 0.01,
        "10": 0.005,
        "30": 0.002,
        "60": 0
    }

    stoploss = -0.02
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.008
    trailing_only_offset_is_reached = True

    order_types = {
        'entry': 'market',
        'exit': 'market',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    unfilledtimeout = {
        'entry': 5,
        'exit': 5,
        'unit': 'seconds'
    }

    # ===== Strategy Parameters =====
    fast_ema = 9
    slow_ema = 21
    rsi_period = 7
    atr_period = 7
    vol_ma_period = 20

    rsi_overbought = 70
    rsi_oversold = 30
    vol_multiplier = 1.2
    atr_multiplier = 0.002
    breakout_lookback = 20
    cooldown_period = 5

    def informative_pairs(self) -> List[tuple]:
        """
        Define additional informative pairs.
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate technical indicators for the strategy.
        """
        dataframe['fast_ema'] = ta.EMA(dataframe, timeperiod=self.fast_ema)
        dataframe['slow_ema'] = ta.EMA(dataframe, timeperiod=self.slow_ema)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=self.atr_period)

        dataframe['vol_ma'] = dataframe['volume'].rolling(window=self.vol_ma_period).mean()

        dataframe['highest'] = dataframe['high'].rolling(window=self.breakout_lookback).max()
        dataframe['lowest'] = dataframe['low'].rolling(window=self.breakout_lookback).min()

        dataframe['atr_pct'] = dataframe['atr'] / dataframe['close']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Entry signal logic - Buy when trend is bullish.
        """
        dataframe.loc[
            (dataframe['fast_ema'] > dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) <= dataframe['slow_ema'].shift(1)) &
            (dataframe['rsi'] < 70) &
            (dataframe['volume'] > 0),
            'enter_long'
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit signal logic - Sell when trend is bearish or conditions met.
        """
        dataframe.loc[
            (dataframe['fast_ema'] < dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) >= dataframe['slow_ema'].shift(1)) &
            (dataframe['volume'] > 0),
            'exit'
        ] = 1

        return dataframe
