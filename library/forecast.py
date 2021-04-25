from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from pmdarima.arima import auto_arima
from matplotlib import pyplot as plt 
import numpy as np
import pandas as pd
from fbprophet import Prophet
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout


def decompose(stock) :
     result = seasonal_decompose(stock.stockValue['Close'], model='multiplicative', period=30)
     return result


def AutoARIMA(stock) :
     # Seasonality check
     decomposed_df = decompose(stock)             # TODO create new tab to plot the backend analysis

     # The training will be carried out in logarithmic domain, to reduce data fluctuations and retrieve the best pqd triplet
     dfClean = np.log(stock.stockValue['Close'])
     
     # Split in train data and test data
     train_data, test_data = dfClean[10:int(len(dfClean)*0.98)], dfClean[int(len(dfClean)*0.98):]

     # AutoARIMA pdq identification
     model_autoARIMA = auto_arima(train_data, start_p=5, start_q=5,
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
     forecastedSteps = 15
     model_predictions = fitted.get_forecast(steps=forecastedSteps)  
     forecasted_value = model_predictions.predicted_mean
     forecasted_series = pd.Series(forecasted_value.values, index=test_data.index[:forecastedSteps])
     confidence = model_predictions.conf_int(alpha=0.25) # 75% confidence
     lower_series = pd.Series(confidence['lower Close'].values, index=test_data.index[:forecastedSteps])
     upper_series = pd.Series(confidence['upper Close'].values, index=test_data.index[:forecastedSteps])

     print('MAPE: {:.2%}'.format(np.mean(np.abs(forecasted_value.values - test_data[:forecastedSteps].values)/np.abs(test_data[:forecastedSteps].values))))
     return forecasted_series, lower_series, upper_series


def prophet(stock) :
     m = Prophet(daily_seasonality = False) # the Prophet class (model)
     m.fit(pd.DataFrame({'y': np.log(stock.stockValue['Close']), 'ds': stock.stockValue['Close'].index}))
     future = m.make_future_dataframe(periods=15) #we need to specify the number of days in future
     prediction = m.predict(future)

     # Prediction at t-30gg
     p = Prophet(daily_seasonality = False)
     p.fit(pd.DataFrame({'y': np.log(stock.stockValue['Close'][:-30]), 'ds': stock.stockValue['Close'][:-30].index}))
     future_m30 = p.make_future_dataframe(periods=45) #we need to specify the number of days in future
     prediction_m30 = p.predict(future_m30)

     return prediction, prediction_m30


def lstm_initialization(tensorShape, unitsPerLayer=[50, 50, 50, 50], dropoutPerLayer=[0.2, 0.2, 0.2, 0.2]) :

     if len(unitsPerLayer) == len(dropoutPerLayer) :
          # Initialising the RNN
          regressor = Sequential()

          # Adding the LSTM layer and Dropout regularisation
          # First Layer
          x=0
          regressor.add(LSTM(units = unitsPerLayer[x], return_sequences = True, input_shape = (tensorShape, 1)))
          regressor.add(Dropout(dropoutPerLayer[x]))
          # Intermediate Layers
          for x in range(1,len(unitsPerLayer)-1) : 
               regressor.add(LSTM(units = unitsPerLayer[x], return_sequences = True))
               regressor.add(Dropout(dropoutPerLayer[x]))
          # Last Layer
          x+=1
          regressor.add(LSTM(units = unitsPerLayer[x], return_sequences = True))
          regressor.add(Dropout(dropoutPerLayer[x]))
          regressor.add(Dense(units = 1))

          # Compiling the RNN
          regressor.compile(optimizer = 'adam', loss = 'mean_squared_error')
          return regressor

     else: 
          print('Error: Units per Layer and Dropouts mismatch!')

def lstm(stock, trainingSetDim=0.85, historicalWindowSize=60, epochs=100, batchSize=32) :
     
     trainSet = stock.stockValue.iloc[:, 3:4]
     # Scale the dset
     sc = MinMaxScaler(feature_range = (0, 1))
     scaledDF = sc.fit_transform(stock.stockValue)

     # Creating a data structure with a window of timesteps and 1 output
     X_train = []
     y_train = []
     for i in range(historicalWindowSize, int(len(scaledDF)*trainingSetDim)):
          X_train.append(scaledDF[i-historicalWindowSize:i, 0])   # <-- Si può pensare di espandere la matrice X con ulteriori dati come MACD, Volumes ed altro
          y_train.append(scaledDF[i, 0])
     X_train, y_train = np.array(X_train), np.array(y_train)
     # Reshaping
     X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

     # Train the Network
     regressor = lstm_initialization(X_train.shape[1])
     regressor.fit(X_train, y_train, epochs=epochs, batch_size=batchSize)

     # Prepare input for forecast
     X_test = []
     for i in range(historicalWindowSize + int(len(scaledDF)*trainingSetDim), len(scaledDF)):
          X_test.append(scaledDF[i-historicalWindowSize:i, 0])
     X_test = np.array(X_test)
     X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
     # Forecast
     Y_test = regressor.predict(X_test)
     predicted_stock_price = sc.inverse_transform(Y_test)
     return X_test, predicted_stock_price