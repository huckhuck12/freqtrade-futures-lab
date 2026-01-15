from freqtrade.strategy import IStrategy
from pandas import DataFrame
from typing import List
import talib.abstract as ta


class FutureHighFreqV1(IStrategy):
    """
    High Frequency Trend Following Strategy V1 (Optimized)

    Strategy Logic:
    - EMA crossover with RSI and trend filters
    - Trailing stop for profit protection
    - Dynamic stop-loss based on ATR

    Timeframe: 1m
    Pairs: 10 high-volatility futures pairs
    """

    timeframe = '1m'
    max_open_trades = 10
    stake_amount = 0.10
    startup_candle_count = 200

    minimal_roi = {
        "0": 0.01,
        "30": 0.005,
        "120": 0.002,
        "240": 0
    }

    stoploss = -0.015
    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.012
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
    ema50_period = 50
    rsi_period = 7
    atr_period = 14
    vol_ma_period = 20

    rsi_overbought = 70
    rsi_buy_threshold = 70
    rsi_sell_threshold = 50

    trend_filter = False
    rsi_filter = True
    atr_filter = False
    atr_max_pct = 0.05

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
        dataframe['ema50'] = ta.EMA(dataframe, timeperiod=self.ema50_period)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=self.atr_period)

        dataframe['vol_ma'] = dataframe['volume'].rolling(window=self.vol_ma_period).mean()

        dataframe['atr_pct'] = dataframe['atr'] / dataframe['close']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Entry signal logic - Buy when trend is bullish.
        """
        ema_crossover = (
            (dataframe['fast_ema'] > dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) <= dataframe['slow_ema'].shift(1))
        )

        conditions = ema_crossover & (dataframe['volume'] > 0)

        if self.rsi_filter:
            conditions = conditions & (dataframe['rsi'] < self.rsi_buy_threshold)

        if self.trend_filter:
            conditions = conditions & (dataframe['close'] > dataframe['ema50'])

        if self.atr_filter:
            conditions = conditions & (dataframe['atr_pct'] < self.atr_max_pct)

        dataframe.loc[conditions, 'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit signal logic - Sell when trend is bearish or conditions met.
        """
        ema_crossover = (
            (dataframe['fast_ema'] < dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) >= dataframe['slow_ema'].shift(1))
        )

        conditions = ema_crossover & (dataframe['volume'] > 0)

        if self.rsi_filter:
            conditions = conditions | (dataframe['rsi'] > self.rsi_sell_threshold)

        if self.trend_filter:
            conditions = conditions & (dataframe['close'] < dataframe['ema50'])

        dataframe.loc[conditions, 'exit'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit signal logic - Sell when trend is bearish or conditions met.
        """
        ema_crossover = (
            (dataframe['fast_ema'] < dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) >= dataframe['slow_ema'].shift(1))
        )

        conditions = [ema_crossover, dataframe['volume'] > 0]

        if self.rsi_filter:
            conditions.append(dataframe['rsi'] > self.rsi_sell_threshold)

        if self.trend_filter:
            conditions.append(dataframe['close'] < dataframe['ema50'])

        dataframe.loc[
            sum(conditions),
            'exit'
        ] = 1

        return dataframe
