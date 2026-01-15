from freqtrade.strategy import IStrategy
from pandas import DataFrame
from datetime import datetime
from typing import List, Optional
import talib.abstract as ta


class FutureHighFreqV1(IStrategy):
    """
    High Frequency Trend Following Strategy V1 (Fully Optimized)

    Strategy Logic:
    - EMA crossover with multi-filter confirmation
    - Dynamic ATR-based stop loss
    - Time-based session filter
    - Partial profit taking

    Timeframe: 1m
    Pairs: 10 high-volatility futures pairs
    """

    timeframe = '1m'
    max_open_trades = 10
    stake_amount = 0.10
    startup_candle_count = 200

    minimal_roi = {
        "0": 0.008,
        "15": 0.005,
        "60": 0.002,
        "180": 0
    }

    stoploss = -0.015
    trailing_stop = True
    trailing_stop_positive = 0.006
    trailing_stop_positive_offset = 0.01
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
    ema50_period = 20
    rsi_period = 7
    atr_period = 14
    vol_ma_period = 20

    rsi_overbought = 70
    rsi_buy_threshold = 55
    rsi_sell_threshold = 60

    trend_filter = True
    rsi_filter = True
    atr_filter = True
    atr_max_pct = 0.05
    adx_period = 14
    adx_threshold = 25
    adx_filter = True

    # Time filter parameters (UTC)
    use_time_filter = True
    session_start_hour = 0
    session_end_hour = 23

    # Dynamic stop loss
    use_dynamic_stoploss = True
    atr_sl_multiplier = 1.5

    # Partial profit taking
    use_partial_profit = True
    partial_profit_threshold = 0.005
    partial_profit_amount = 0.5

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
        dataframe['ema20'] = ta.EMA(dataframe, timeperiod=self.ema50_period)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=self.atr_period)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=self.adx_period)
        dataframe['vol_ma'] = dataframe['volume'].rolling(window=self.vol_ma_period).mean()
        dataframe['atr_pct'] = dataframe['atr'] / dataframe['close']

        return dataframe

    def custom_stoploss(self, dataframe: DataFrame, pair: str, trade_id: int,
                        current_profit: float, min_rate: float, max_rate: float,
                        current_entry_rate: float, current_exit_rate: float,
                        current_time: datetime) -> float:
        """
        Dynamic stop loss based on ATR.
        """
        if not self.use_dynamic_stoploss:
            return self.stoploss

        atr_pct = dataframe['atr_pct'].iloc[-1]
        dynamic_sl = -(atr_pct * self.atr_sl_multiplier)

        return max(dynamic_sl, self.stoploss)

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
            conditions = conditions & (dataframe['close'] > dataframe['ema20'])

        if self.atr_filter:
            conditions = conditions & (dataframe['atr_pct'] < self.atr_max_pct)

        if self.adx_filter:
            conditions = conditions & (dataframe['adx'] > self.adx_threshold)

        if self.use_time_filter:
            hour = dataframe['date'].dt.hour
            time_condition = (hour >= self.session_start_hour) & (hour < self.session_end_hour)
            conditions = conditions & time_condition

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
            conditions = conditions & (dataframe['close'] < dataframe['ema20'])

        if self.adx_filter:
            conditions = conditions | (dataframe['adx'] < self.adx_threshold)

        dataframe.loc[conditions, 'exit'] = 1

        return dataframe
