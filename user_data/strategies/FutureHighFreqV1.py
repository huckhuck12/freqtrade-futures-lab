from freqtrade.strategy import IStrategy
from pandas import DataFrame
from datetime import datetime
from typing import List
import talib.abstract as ta


class FutureHighFreqV1(IStrategy):
    """
    High Frequency Trend Following Strategy V1 (High Yield Edition)

    Strategy Logic:
    - Fast EMA crossover signals
    - Tight RSI thresholds for early entry
    - Enhanced profit taking with trailing
    - Multi-confirmation filters

    Timeframe: 1m
    Pairs: 10 high-volatility futures pairs
    """

    timeframe = '5m'
    max_open_trades = 10
    stake_amount = 0.10
    startup_candle_count = 300

    minimal_roi = {
        "0": 0.006,
        "20": 0.003,
        "60": 0.001,
        "120": 0
    }

    stoploss = -0.015
    trailing_stop = True
    trailing_stop_positive = 0.004
    trailing_stop_positive_offset = 0.006
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

    # ===== Core Strategy Parameters =====
    fast_ema = 9
    slow_ema = 21
    ema50_period = 50

    # RSI parameters - Balanced for quality + quantity
    rsi_period = 7
    rsi_buy_threshold = 65      # Relaxed for more entries
    rsi_sell_threshold = 70     # Later exit for more profit
    use_rsi_filter = True

    # ADX parameters
    adx_period = 14
    adx_threshold = 25          # Higher for quality
    use_adx_filter = True

    # ATR parameters
    atr_period = 14
    atr_max_pct = 0.04          # Moderate volatility filter
    use_atr_filter = True

    # Bollinger Bands for additional confirmation
    bb_period = 20
    bb_std = 2.0
    use_bb_filter = False
    bb_position_threshold = 0.1  # Price near lower band

    # Volume filter
    vol_ma_period = 20
    vol_multiplier = 0.8        # Very relaxed
    use_vol_filter = False

    # Time filter (UTC) - Full session
    use_time_filter = True
    session_start_hour = 0
    session_end_hour = 23

    # Dynamic stop loss
    use_dynamic_stoploss = True
    atr_sl_multiplier = 1.0

    cooldown_period = 3         # Reduced for more trades

    def informative_pairs(self) -> List[tuple]:
        """
        Define additional informative pairs.
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate all technical indicators for the strategy.
        """
        dataframe['fast_ema'] = ta.EMA(dataframe, timeperiod=self.fast_ema)
        dataframe['slow_ema'] = ta.EMA(dataframe, timeperiod=self.slow_ema)
        dataframe['ema20'] = ta.EMA(dataframe, timeperiod=self.ema50_period)

        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=self.adx_period)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=self.atr_period)

        dataframe['vol_ma'] = dataframe['volume'].rolling(window=self.vol_ma_period).mean()
        dataframe['vol_ratio'] = dataframe['volume'] / dataframe['vol_ma']

        dataframe['atr_pct'] = dataframe['atr'] / dataframe['close']

        bb = ta.BBANDS(dataframe, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)
        dataframe['bb_lower'] = bb['lowerband']
        dataframe['bb_middle'] = bb['middleband']
        dataframe['bb_upper'] = bb['upperband']
        dataframe['bb_position'] = (dataframe['close'] - dataframe['bb_lower']) / (dataframe['bb_upper'] - dataframe['bb_lower'])

        return dataframe

    def custom_stoploss(self, dataframe: DataFrame, pair: str, trade_id: int,
                        current_profit: float, min_rate: float, max_rate: float,
                        current_entry_rate: float, current_exit_rate: float,
                        current_time: datetime) -> float:
        """
        Dynamic stop loss based on ATR with profit protection.
        """
        if not self.use_dynamic_stoploss:
            return self.stoploss

        atr_pct = dataframe['atr_pct'].iloc[-1]
        dynamic_sl = -(atr_pct * self.atr_sl_multiplier)

        if current_profit > 0.015:
            return max(dynamic_sl, -0.003)
        elif current_profit > 0.008:
            return max(dynamic_sl, -0.006)
        else:
            return max(dynamic_sl, self.stoploss)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Entry signal logic - Fast EMA crossover with multi-confirmation.
        """
        ema_crossover = (
            (dataframe['fast_ema'] > dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) <= dataframe['slow_ema'].shift(1))
        )

        conditions = ema_crossover & (dataframe['volume'] > 0)

        if self.use_rsi_filter:
            conditions = conditions & (dataframe['rsi'] < self.rsi_buy_threshold)

        if self.use_adx_filter:
            conditions = conditions & (dataframe['adx'] > self.adx_threshold)

        if self.use_atr_filter:
            conditions = conditions & (dataframe['atr_pct'] < self.atr_max_pct)

        if self.use_bb_filter:
            conditions = conditions & (dataframe['bb_position'] < self.bb_position_threshold)

        if self.use_vol_filter:
            conditions = conditions & (dataframe['vol_ratio'] > self.vol_multiplier)

        if self.use_time_filter:
            hour = dataframe['date'].dt.hour
            time_condition = (hour >= self.session_start_hour) & (hour < self.session_end_hour)
            conditions = conditions & time_condition

        dataframe.loc[conditions, 'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit signal logic - Early exit on trend reversal.
        """
        ema_crossover = (
            (dataframe['fast_ema'] < dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) >= dataframe['slow_ema'].shift(1))
        )

        conditions = ema_crossover & (dataframe['volume'] > 0)

        if self.use_rsi_filter:
            conditions = conditions | (dataframe['rsi'] > self.rsi_sell_threshold)

        if self.use_adx_filter:
            conditions = conditions | (dataframe['adx'] < self.adx_threshold)

        if self.use_bb_filter:
            conditions = conditions | (dataframe['bb_position'] > 0.9)

        dataframe.loc[conditions, 'exit'] = 1

        return dataframe
