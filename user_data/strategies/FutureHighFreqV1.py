from freqtrade.strategy import IStrategy
from pandas import DataFrame
from datetime import datetime
from typing import List
import talib.abstract as ta


class FutureHighFreqV1(IStrategy):
    """
    High Frequency Trend Following Strategy V1 (Ultra Optimized)

    Strategy Logic:
    - Multi-indicator confluence: EMA + MACD + RSI + ADX
    - Dynamic ATR-based stop loss
    - Volume confirmation
    - VWAP price validation

    Timeframe: 1m
    Pairs: 10 high-volatility futures pairs
    """

    timeframe = '1m'
    max_open_trades = 10
    stake_amount = 0.10
    startup_candle_count = 200

    minimal_roi = {
        "0": 0.006,
        "30": 0.003,
        "120": 0.001,
        "240": 0
    }

    stoploss = -0.012
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

    # ===== Core Strategy Parameters =====
    fast_ema = 9
    slow_ema = 21
    ema50_period = 20

    # MACD parameters
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    use_macd_filter = False

    # RSI parameters
    rsi_period = 7
    rsi_buy_threshold = 55
    rsi_sell_threshold = 60
    use_rsi_filter = True

    # ADX parameters
    adx_period = 14
    adx_threshold = 25
    use_adx_filter = True

    # ATR parameters
    atr_period = 14
    atr_max_pct = 0.05
    use_atr_filter = True

    # Volume parameters
    vol_ma_period = 20
    vol_multiplier = 1.0
    use_vol_filter = False

    # VWAP parameters
    use_vwap_filter = False
    vwap_deviation = 0.02

    # Time filter (UTC)
    use_time_filter = True
    session_start_hour = 0
    session_end_hour = 23

    # Dynamic stop loss
    use_dynamic_stoploss = True
    atr_sl_multiplier = 1.2

    cooldown_period = 5

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

        ema12 = ta.EMA(dataframe, timeperiod=self.macd_fast)
        ema26 = ta.EMA(dataframe, timeperiod=self.macd_slow)
        dataframe['macd'] = ema12 - ema26
        dataframe['macd_signal'] = ta.EMA(dataframe, timeperiod=self.macd_signal)
        dataframe['macd_hist'] = dataframe['macd'] - dataframe['macd_signal']

        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=self.adx_period)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=self.atr_period)

        dataframe['vol_ma'] = dataframe['volume'].rolling(window=self.vol_ma_period).mean()
        dataframe['vol_ratio'] = dataframe['volume'] / dataframe['vol_ma']

        dataframe['atr_pct'] = dataframe['atr'] / dataframe['close']

        dataframe['vwap'] = (dataframe['volume'] * (dataframe['high'] + dataframe['low'] + dataframe['close']) / 3).cumsum() / dataframe['volume'].cumsum()
        dataframe['vwap_deviation'] = (dataframe['close'] - dataframe['vwap']) / dataframe['vwap']

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

        if current_profit > 0.02:
            return max(dynamic_sl, -0.005)
        elif current_profit > 0.01:
            return max(dynamic_sl, -0.008)
        else:
            return max(dynamic_sl, self.stoploss)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Entry signal logic - Multi-indicator confluence for long entries.
        """
        ema_crossover = (
            (dataframe['fast_ema'] > dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) <= dataframe['slow_ema'].shift(1))
        )

        conditions = ema_crossover & (dataframe['volume'] > 0)

        if self.use_macd_filter:
            macd_bullish = dataframe['macd'] > dataframe['macd_signal']
            conditions = conditions & macd_bullish

        if self.use_rsi_filter:
            conditions = conditions & (dataframe['rsi'] < self.rsi_buy_threshold)

        if self.use_adx_filter:
            conditions = conditions & (dataframe['adx'] > self.adx_threshold)

        if self.use_atr_filter:
            conditions = conditions & (dataframe['atr_pct'] < self.atr_max_pct)

        if self.use_vol_filter:
            conditions = conditions & (dataframe['vol_ratio'] > 0.8)

        if self.use_vwap_filter:
            conditions = conditions & (dataframe['close'] > dataframe['vwap'])

        if self.use_time_filter:
            hour = dataframe['date'].dt.hour
            time_condition = (hour >= self.session_start_hour) & (hour < self.session_end_hour)
            conditions = conditions & time_condition

        dataframe.loc[conditions, 'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit signal logic - Multi-indicator confluence for long exits.
        """
        ema_crossover = (
            (dataframe['fast_ema'] < dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) >= dataframe['slow_ema'].shift(1))
        )

        conditions = ema_crossover & (dataframe['volume'] > 0)

        if self.use_macd_filter:
            macd_bearish = dataframe['macd'] < dataframe['macd_signal']
            conditions = conditions & macd_bearish

        if self.use_rsi_filter:
            conditions = conditions | (dataframe['rsi'] > self.rsi_sell_threshold)

        if self.use_adx_filter:
            conditions = conditions | (dataframe['adx'] < self.adx_threshold)

        if self.use_vwap_filter:
            conditions = conditions | (dataframe['close'] < dataframe['vwap'])

        dataframe.loc[conditions, 'exit'] = 1

        return dataframe
