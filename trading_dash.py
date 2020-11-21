import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import scipy.signal as signal
import numpy as np
import pandas as pd
import os
from flask_caching import Cache
import time


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
CACHE_CONFIG = {
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT' : 300
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)


# Dash Layout
app.layout = html.Div([
    html.H2("Prototype of an Advisoring Dashboard"),
    html.Div(className='row', children=[
            html.P(className='two columns', children="Enter the name of the Stock "),
            dcc.Input(className='one columns', id='stockName', value='AAPL', type='text',debounce=True),
    ]),

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
            daq.BooleanSwitch(
                label='Momentum',
                className='one columns',
                id='MomentumToggle',
                on=False,
                color='#C0C0C0',
            ),
        ]
    ),
    html.H4(id='graphTitle', children=''),
    dcc.Graph(id='stockGraph', config={'scrollZoom':True}),

    dcc.ConfirmDialog(
        id='noDataFound',
        message='No Data Found, check Stock Name',
    ),
])



# Callbacks
@app.callback(
    [Output('graphTitle','children')],
    Input('stockName','value')
)
def updateStock(stockName) :
    if len(stockName)>=4:
        globalStore(stockName)
        return [stockMem.stockTicker.info['shortName'] + ' Stocks']


@app.callback(
    [Output('stockGraph','figure'),
     Output('noDataFound', 'displayed')],
    [Input('graphTitle','children'),
     Input('EMA20Toggle','on'),
     Input('EMA50Toggle','on'),
     Input('SMA200Toggle','on'),
     Input('MomentumToggle','on')]
    )
def updateGraph(stockName,EMA20,EMA50,SMA200,Momentum) :
    if stockMem.stockValue.empty is False :
        stockMem.updateGraphs(EMA20,EMA50,SMA200,Momentum)
        return [
            stockMem.figHandler,
            False
                ]
    else :
        return [
            dash.no_update,
            True
        ]


stockMem = []

@cache.memoize()
def globalStore(name) :
    global stockMem
    stockMem = Stock(name)
    stockMem.computeMomentum()
    stockMem.EMA20  = stockMem.computeMA(nDays=20, kind='exp')
    stockMem.EMA50  = stockMem.computeMA(nDays=50, kind='exp')
    stockMem.SMA200 = stockMem.computeMA(nDays=200, kind='simple')
    return stockMem

# Class Definitions
class Stock(object) :

    def __init__(self,stockName) :
        self.stockName = stockName
        self.stockTicker = yf.Ticker(self.stockName.upper())
        self.stockValue = self.stockTicker.history(period='5y',interval='1d',group_by='ticker') 
        self.momentum   = []
        self.EMA20      = []
        self.EMA50      = []
        self.SMA200     = []
        self.figHandler = []
        

    def updateGraphs(self,EMA20,EMA50,SMA200,Momentum) :
        if Momentum == True :
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.005, row_heights=[0.45, 0.1, 0.45])
            # Embed the Momentum graph between the OHLC and minMax graph
            scatterPlotRow = 3
        else :
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.005)
            scatterPlotRow= 2
        # OHLCPlot
        fig.add_trace(
            go.Ohlc(
                x=self.stockValue['Close'].index,
                open=self.stockValue['Open'].array,
                high=self.stockValue['High'].array,
                low=self.stockValue['Low'].array,
                close=self.stockValue['Close'].array,
                name=self.stockName),
            row=1, col=1)

        # Optional Moving Average Plots
        if SMA200 == True :
            fig.add_trace(
                go.Scatter(
                    x=self.stockValue['Close'][-200:].index,
                    y=self.SMA200,
                    marker_color='#FF1493',
                    name='SMA200',
                ),
            row=1, col=1)

        if EMA50 == True :
            fig.add_trace(
                go.Scatter(
                    x=self.stockValue['Close'][-50:].index,
                    y=self.EMA50,
                    marker_color='#9400D3',
                    name='EMA50',
                ),
            row=1, col=1)
        
        if EMA20 == True :
            fig.add_trace(
                go.Scatter(
                    x=self.stockValue['Close'][-20:].index,
                    y=self.EMA20,
                    marker_color='#4169E1',
                    name='EMA20',
                ),
            row=1, col=1)

        if Momentum == True :
            MomDays = 15
            df = pd.DataFrame({'mom' : self.momentum, 'date' : self.stockValue['Close'].index[MomDays:]})
            # Momentum Raise
            fig.add_trace(
                go.Bar(
                    x=df.where(df['mom'] > 10).dropna()['date'],
                    y=df.where(df['mom'] > 10).dropna()['mom'],
                    marker_color='turquoise',
                    name='Momentum',
                ),row=2, col=1)
            # Momentum Down
            fig.add_trace(
                go.Bar(
                    x=df.where(df['mom'] < -10).dropna()['date'],
                    y=df.where(df['mom'] < -10).dropna()['mom'],
                    marker_color='purple',
                    name='Momentum',
                ),row=2, col=1)
            # Momentum Steady
            fig.add_trace(
                go.Bar(
                    x=df.where((df['mom'] < 10) & (df['mom'] > -10)).dropna()['date'],
                    y=df.where((df['mom'] < 10) & (df['mom'] > -10)).dropna()['mom'],
                    marker_color='silver',
                    name='Momentum',
                ),row=2, col=1)
            

        # ScatterPlot
        fig.add_trace(
            go.Scatter(
                x=self.stockValue['Close'].index,
                y=self.stockValue['Close'].array, 
                marker_color='black',
                name=self.stockName),
            row=scatterPlotRow, col=1)
        
        # MinMax Plot
        maxs, mins = self.computeMinMax()
        fig.add_trace(
           go.Scatter(
               mode="markers",
               x=self.stockValue['Close'][maxs].index,
               y=self.stockValue['Close'].array[maxs], 
               marker_symbol=141, marker_color='rgb(251,180,174)', marker_line_width=2,
               showlegend=False,
               name='MAX'),
            row=scatterPlotRow, col=1)
        fig.add_trace(
           go.Scatter(
               mode="markers",
               x=self.stockValue['Close'][mins].index,
               y=self.stockValue['Close'].array[mins], 
               marker_symbol=141, marker_color='#00CC96', marker_line_width=2,
               showlegend=False,
               name='MIN'),
           row=scatterPlotRow, col=1)


        fig.update(layout_xaxis_rangeslider_visible=False)
        self.figHandler = self.layout_update(fig)
    

    def layout_update(self, fig) :
        fig.update_layout(
                showlegend=False,
                # title=self.stockTicker.info['shortName'] + ' Stocks',
                height=700,
                # shapes = [dict(
                #             x0='2020-08-09', x1='2020-08-09', 
                #             y0=0, y1=1, xref='x', yref='paper',
                #             line_width=2
                #         )],
            )
        return fig


    def computeMinMax(self) :
        peaksList, _ = signal.find_peaks(self.stockValue['Close'].array,distance=10)
        lowsList, _ = signal.find_peaks(-self.stockValue['Close'].array,distance=10)
        return peaksList,lowsList


    def computeMomentum(self,nDays=15) :
        Mom = []
        for days in range(len(self.stockValue['Close'].array[nDays:])) :
            Mom.append(self.stockValue['Close'].array[days] - self.stockValue['Close'].array[days-nDays])
        self.momentum = Mom 
        print('Momentum calc completed')


    def computeMA(self,nDays=20,kind='simple') :
        if kind == 'simple' :
            SMA = []
            for i in range(nDays) :
                SMA.append((1/nDays)*sum(self.stockValue['Close'].array[np.arange(-i-nDays,-i)]))
            SMA.reverse()
            return SMA
        if kind == 'exp' :
            EMA = [(1/nDays)*sum(self.stockValue['Close'].array[-2*nDays:-nDays])]
            K = 2/(nDays+1)
            for i in range(1,nDays) :
                EMA.append(K* (self.stockValue['Close'].array[-nDays+i] - EMA[-1]) + EMA[-1])
            return EMA


if __name__ == '__main__':
    app.run_server(debug=True)