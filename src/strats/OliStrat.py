from pyalgotrade import strategy
from pyalgotrade import technical


class OliStrat(strategy.BacktestingStrategy):
    pass


def testFunction(stockHandle):
    sma = technical.ma.SMA()
    #stockHandle.data.
    stockHandle.data.getPriceDataSeries()