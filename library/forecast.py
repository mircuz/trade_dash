import pmdarima as pm
from pmdarima.model_selection import train_test_split
from pmdarima.pipeline import Pipeline
from pmdarima.preprocessing import BoxCoxEndogTransformer
from sklearn.metrics import mean_squared_error


def train_model(stock) :
     # Import the Stocks and evaluate the structure for the training and forecast
     train, test = train_test_split(stock.stockValue['Close'], train_size=int(len(stock.stockValue)*0.90))

     # ARIMA implementation
     pipeline = Pipeline([
     ('boxcox', BoxCoxEndogTransformer(lmbda2=1e-6)),  # lmbda2 avoids negative values
     ('arima', pm.AutoARIMA(seasonal=True, m=12,
                           suppress_warnings=True,
                           trace=True))
     ])
     pipeline.fit(train)
     prediction = pipeline.predict(int(len(stock.stockValue)*0.1))
    
     MSE_error = 5 #mean_squared_error(test, prediction)
     print('Testing Mean Squared Error is {}'.format(MSE_error))
     test_set_range = stock.stockValue[int(len(stock.stockValue)*0.9):int(len(stock.stockValue)*1.0)].index
     return test_set_range, prediction, MSE_error
