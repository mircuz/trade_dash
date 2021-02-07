from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error


def train_model(stock) :
    # Import the Stocks and evaluate the structure for the training and forecast

    # ARIMA implementation
    train_data, test_data = stock.stockValue[0:int(len(stock.stockValue)*0.7)],\
                            stock.stockValue[int(len(stock.stockValue)*0.7):]
    training_data = train_data['Close'].values
    test_data = test_data['Close'].values
    history = [x for x in training_data]
    model_predictions = []
    N_test_observations = len(test_data)
    for time_point in range(N_test_observations):
         model = ARIMA(history, order=(5,1,1))
         model_fit = model.fit()
         output = model_fit.forecast()
         model_predictions.append(output[0].item())
         true_test_value = test_data[time_point]
         history.append(true_test_value)
    MSE_error = mean_squared_error(test_data, model_predictions)
    print('Testing Mean Squared Error is {}'.format(MSE_error))
    test_set_range = stock.stockValue[int(len(stock.stockValue)*0.7):].index
    return test_set_range, model_predictions, MSE_error
