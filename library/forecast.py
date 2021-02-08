from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from pmdarima.arima import auto_arima
from matplotlib import pyplot as plt 
import numpy as np
import pandas as pd


def decompose(stock) :
     result = seasonal_decompose(stock.stockValue['Close'], model='multiplicative', period=30)
     return result


def AutoARIMA(stock) :
     # Seasonality check
     decomposed_df = decompose(stock)             # TODO create new tab to plot the backend analysis

     # The training will be carried out in logarithmic domain, to reduce data fluctuations and retrieve the best pqd triplet
     dfClean = np.log(stock.stockValue['Close'])
     # Split in train data and test data
     train_data, test_data = dfClean[3:int(len(dfClean)*0.9)], dfClean[int(len(dfClean)*0.9):]

     # AutoARIMA pdq identification
     model_autoARIMA = auto_arima(train_data, start_p=0, start_q=0,
                      test='adf',       # use adftest to find optimal 'd'
                      max_p=7, max_q=7, # maximum p and q
                      m=1,              # frequency of series
                      d=None,           # let model determine 'd'
                      seasonal=False,   # No Seasonality
                      start_P=0, 
                      D=0, 
                      trace=True,
                      error_action='ignore',  
                      suppress_warnings=True, 
                      stepwise=True)
     print(model_autoARIMA.summary())
     
     # Train ARIMA Model
     model = ARIMA(train_data, order=model_autoARIMA.order)  
     fitted = model.fit()  

     # Forecast
     forecastedSteps = 30
     model_predictions = fitted.get_forecast(steps=forecastedSteps)  # 95% confidence
     forecasted_value = model_predictions.predicted_mean
     forecasted_series = pd.Series(forecasted_value.values, index=test_data.index[:forecastedSteps])
     confidence = model_predictions.conf_int(alpha=0.05)
     lower_series = pd.Series(confidence['lower Close'].values, index=test_data.index[:forecastedSteps])
     upper_series = pd.Series(confidence['upper Close'].values, index=test_data.index[:forecastedSteps])

     return forecasted_series, lower_series, upper_series
