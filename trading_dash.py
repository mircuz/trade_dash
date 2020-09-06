import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import scipy.signal as signal
import numpy as np


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Dash Layout
app.layout = html.Div([
    html.H2("PyTrade"),
    html.Div(className='row', children=[
            html.P(className='two columns', children="Enter the name of the Stock "),
            dcc.Input(className='one columns', id='stockName', value='AAPL', type='text'),
    ]),
    dcc.Graph(id='stockGraph'),

    html.Strong('Tools'),
    html.Div(
        className='row',
        children=[
            daq.BooleanSwitch(
                label='EMA20',
                className='one columns',
                id='EMA20Toggle',
                on=False,
                color='#4169E1',
            ),
            daq.BooleanSwitch(
                label='EMA50',
                className='one columns',
                id='EMA50Toggle',
                on=False,
                color='#9400D3',
            ),
            daq.BooleanSwitch(
                label='SMA200',
                className='one columns',
                id='SMA200Toggle',
                on=False,
                color="#FF1493",
            ),
        ]
    )
])



# Callbacks
@app.callback(
    Output('stockGraph','figure'),
    [Input('stockName','value'),
     Input('EMA20Toggle','on'),
     Input('EMA50Toggle','on'),
     Input('SMA200Toggle','on')]
    )
def updateStock(stockName,EMA20,EMA50,SMA200) :
        if len(stockName)==4:
            currentStock = Stock(stockName)
            figHandler = currentStock.updateGraphs(EMA20,EMA50,SMA200)
            return figHandler
        else : 
            raise PreventUpdate 


# Class Definition
class Stock(object):

    def __init__(self,stockName) :
        self.stockName = stockName
        self.stockTicker = yf.Ticker(self.stockName.upper())
        self.stockValue = self.stockTicker.history(period='2y',interval='1d',group_by='ticker')


    def updateGraphs(self,EMA20,EMA50,SMA200) :
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.005)
        # OHLCPlot
        fig.add_trace(
            go.Ohlc(
                x=self.stockValue['Close'].index,
                open=self.stockValue['Open'].array,
                high=self.stockValue['High'].array,
                low=self.stockValue['Low'].array,
                close=self.stockValue['Close'].array),
            row=1, col=1)
        if SMA200 == True :
            sma200 = self.computeMA(nDays=200,kind='simple')
            fig.add_trace(
                go.Scatter(
                    x=self.stockValue['Close'][-200:].index,
                    y=sma200,
                    marker_color='#FF1493',
                )
            )
        # ScatterPlot
        fig.add_trace(
            go.Scatter(
                x=self.stockValue['Close'].index,
                y=self.stockValue['Close'].array, 
                marker_color='black'),
            row=2, col=1)
        
        # MinMax Plot
        maxs, mins = self.computeMinMax()
        fig.add_trace(
            go.Scatter(
                mode="markers",
                x=self.stockValue['Close'][maxs].index,
                y=self.stockValue['Close'].array[maxs], 
                marker_symbol=144, marker_color='rgb(251,180,174)', marker_line_width=5,
                showlegend=False),
            row=2, col=1)
        fig.add_trace(
            go.Scatter(
                mode="markers",
                x=self.stockValue['Close'][mins].index,
                y=self.stockValue['Close'].array[mins], 
                marker_symbol=143, marker_color='#00CC96', marker_line_width=5,
                showlegend=False),
            row=2, col=1)

        fig.update(layout_xaxis_rangeslider_visible=False)
        fig = self.layout_update(fig)
        return fig
    

    def layout_update(self, fig) :
        fig.update_layout(
                showlegend=False,
                title=self.stockTicker.info['shortName'] + ' Stocks',
                height=700,
                shapes = [dict(
                            x0='2020-08-09', x1='2020-08-09', y0=0, y1=1, xref='x', yref='paper',
                            line_width=2)],
            )
        return fig


    def computeMinMax(self) :
        peaksList, _ = signal.find_peaks(self.stockValue['Close'].array,distance=5)
        lowsList, _ = signal.find_peaks(-self.stockValue['Close'].array,distance=5)
        return peaksList,lowsList


    def computeMA(self,nDays=20,kind='simple') :
        if kind == 'simple' :
            SMA = []
            for i in range(nDays) :
                SMA.append((1/nDays)*sum(self.stockValue['Close'].array[np.arange(-i-nDays,-i)]))
            SMA.reverse()
            return SMA
        if kind == 'exp' :
            pass
    
         



if __name__ == '__main__':
    app.run_server(debug=True)