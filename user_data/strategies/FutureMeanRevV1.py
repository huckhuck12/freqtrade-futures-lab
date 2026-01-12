from freqtrade.strategy import IStrategy
from pandas import DataFrame
from typing import Dict, List
import talib.abstract as ta
from ._base import BaseFuturesStrategy


class FutureMeanRevV1(BaseFuturesStrategy):
    """
    Futures Mean Reversion Strategy V1

    Strategy logic:
    - Uses Bollinger Bands and RSI for mean reversion trading
    - Buy when price touches lower Bollinger Band and RSI < 35
    - Sell when price touches upper Bollinger Band or RSI > 75
    """

    # Bollinger Bands parameters
    bb_period = 20
    bb_std = 2
    # RSI period
    rsi_period = 14
    # RSI oversold threshold
    rsi_oversold = 35
    # RSI overbought threshold
    rsi_overbought = 75

    def informative_pairs(self) -> List[tuple]:
        """
        Define informative pairs.
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate indicators for the strategy.
        """
        # Calculate Bollinger Bands
        bb = ta.BBANDS(dataframe, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)
        dataframe['bb_lower'] = bb['lowerband']
        dataframe['bb_middle'] = bb['middleband']
        dataframe['bb_upper'] = bb['upperband']

        # Calculate RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period)

        # Calculate percentage position between bands
        dataframe['bb_position'] = (dataframe['close'] - dataframe['bb_lower']) / (dataframe['bb_upper'] - dataframe['bb_lower'])

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Buy signal logic.
        """
        # Buy when price touches lower Bollinger Band and RSI is oversold
        buy_conditions = (
            (dataframe['bb_position'] < 0.05) &  # Price near lower band
            (dataframe['rsi'] < self.rsi_oversold) &
            (dataframe['volume'] > 0)
        )

        dataframe.loc[buy_conditions, 'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Sell signal logic.
        """
        # Sell when price touches upper Bollinger Band or RSI is overbought
        sell_conditions = (
            (
                (dataframe['bb_position'] > 0.95) |  # Price near upper band
                (dataframe['rsi'] > self.rsi_overbought)
            ) &
            (dataframe['volume'] > 0)
        )

        dataframe.loc[sell_conditions, 'sell'] = 1

        return dataframe