from freqtrade.strategy import IStrategy
from pandas import DataFrame
from typing import Dict, List
import talib.abstract as ta
from ._base import BaseFuturesStrategy


class FutureTrendV1(BaseFuturesStrategy):
    """
    Futures Trend Following Strategy V1

    Strategy logic:
    - Uses EMA crossover and RSI for trend identification
    - Buy when fast EMA crosses above slow EMA and RSI < 70
    - Sell when fast EMA crosses below slow EMA or RSI > 80
    """

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
        Calculate indicators for the strategy.
        """
        # Calculate EMAs
        dataframe['fast_ema'] = ta.EMA(dataframe, timeperiod=self.fast_ema)
        dataframe['slow_ema'] = ta.EMA(dataframe, timeperiod=self.slow_ema)

        # Calculate RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Buy signal logic.
        """
        # Buy when fast EMA crosses above slow EMA and RSI < 70
        buy_conditions = (
            (dataframe['fast_ema'] > dataframe['slow_ema']) &
            (dataframe['fast_ema'].shift(1) <= dataframe['slow_ema'].shift(1)) &
            (dataframe['rsi'] < 70) &
            (dataframe['volume'] > 0)
        )

        dataframe.loc[buy_conditions, 'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Sell signal logic.
        """
        # Sell when fast EMA crosses below slow EMA or RSI > 80
        sell_conditions = (
            (
                (dataframe['fast_ema'] < dataframe['slow_ema']) &
                (dataframe['fast_ema'].shift(1) >= dataframe['slow_ema'].shift(1))
            ) |
            (dataframe['rsi'] > 80)
        ) & (dataframe['volume'] > 0)

        dataframe.loc[sell_conditions, 'sell'] = 1

        return dataframe