from binance.client import Client
from datetime import datetime
import pandas as pd
from .binanceToken import binance_api_secret, binance_api_key


def GetHistoricalData(symbol, interval, fromDate):
    client = Client(binance_api_key, binance_api_secret)
    klines = client.get_historical_klines(symbol, interval, fromDate)
    df = pd.DataFrame(klines, columns=['dateTime', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'])
    df.dateTime = pd.to_datetime(df.dateTime, unit='ms')
    #df['date'] = df.dateTime.dt.strftime("%d/%m/%Y")
    #df['time'] = df.dateTime.dt.strftime("%H:%M:%S")
    df = df.drop(['closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol','takerBuyQuoteVol', 'ignore'], axis=1)
    # column_names = ["dateTime", "open", "high", "low", "close", "volume"]
    # df = df.reindex(columns=column_names)
    df.rename({"dateTime": "Datetime", 
               "open":"Open", 
               "high":"High", 
               "low":"Low", 
               "close":"Close", 
               "volume":"Volume"}, 
               axis=1, 
               inplace=True)
    # Typecasting
    df[["Open", "High", "Low", "Close", "Volume"]] = df[["Open", "High", "Low", "Close", "Volume"]].apply(pd.to_numeric)
    return df