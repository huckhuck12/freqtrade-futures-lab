from freqtrade.strategy import IStrategy
from pandas import DataFrame
from typing import Dict, List
import talib.abstract as ta


class FutureTrendV1(IStrategy):
    """
    Futures Trend Following Strategy V1

    Strategy logic:
    - Uses EMA crossover and RSI for trend identification
    - Buy when fast EMA crosses above slow EMA and RSI < 70
    - Sell when fast EMA crosses below slow EMA or RSI > 80
    """

    # Define minimal ROI
    minimal_roi = {
        "0": 0.05
    }

    # Define stoploss
    stoploss = -0.03

    # Use trailing stop
    trailing_stop = False
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = False

    # Order types
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Timeframe for strategy
    timeframe = '5m'

    # Stake amount in USDT
    stake_amount = 0.01

    # Number of startup candles
    startup_candle_count = 300

    # Unfilled timeout
    unfilledtimeout = {
        'entry': 10,
        'exit': 10,
        'exit_timeout_count': 0,
        'unit': 'seconds'
    }

    # Fast EMA period
    fast_ema = 12
    # Slow EMA period
    slow_ema = 26
    # RSI period
    rsi_period = 14

    def informative_pairs(self) -> List[tuple]:
        """
        Define informative pairs.
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate indicators for strategy.
        """
        # Calculate EMAs
        dataframe['fast_ema'] = ta.EMA(dataframe, timeperiod=self.fast_ema)
        dataframe['slow_ema'] = ta.EMA(dataframe, timeperiod=self.slow_ema)

        # Calculate RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Entry signal logic.
        """
        # Entry when fast EMA crosses above slow EMA and RSI < 70
        entry_conditions = (
            (dataframe['fast_ema'] > dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) <= dataframe['slow_ema'].shift(1)) &
            (dataframe['rsi'] < 70) &
            (dataframe['volume'] > 0)
        )

        dataframe.loc[entry_conditions, 'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit signal logic.
        """
        # Exit when fast EMA crosses below slow EMA or RSI > 80
        exit_conditions = (
            (
                (dataframe['fast_ema'] < dataframe['slow_ema']) &
                (dataframe['fast_ema'].shift(1) >= dataframe['slow_ema'].shift(1))
            ) |
            (dataframe['rsi'] > 80)
        ) & (dataframe['volume'] > 0)

        dataframe.loc[exit_conditions, 'exit'] = 1

        return dataframe
