import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import yfinance as yf


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H2("PyTrade"),
    html.Div(className='row', children=[
            html.P(className='two columns', children="Enter the name of the Stock "),
            dcc.Input(className='one columns', id='stockName', value='AAPL', type='text'),
    ]),
    dcc.Graph(id='stockGraph'),
])




@app.callback(
    Output('stockGraph','figure'),
    [Input('stockName','value')]
)
def loadStockData(stockName) :
    if len(stockName) == 4 : 
        stockTicker = yf.Ticker(stockName.upper())
        stockValue = stockTicker.history(period='2y',interval='1d',group_by='ticker')

        fig = go.Figure(data=go.Ohlc(x=stockValue['Close'].index,
                        open=stockValue['Open'].array,
                        high=stockValue['High'].array,
                        low=stockValue['Low'].array,
                        close=stockValue['Close'].array))
        return fig
    else : 
        raise PreventUpdate 
    
         








if __name__ == '__main__':
    app.run_server(debug=True)