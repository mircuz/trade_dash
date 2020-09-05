import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import scipy.signal as signal


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
])


# Callbacks
@app.callback(
    Output('stockGraph','figure'),
    [Input('stockName','value')]
    )
def updateStock(stockName) :
        if len(stockName)==4:
            currentStock = Stock(stockName)
            figHandler = currentStock.updateGraphs()
            return figHandler
        else : 
            raise PreventUpdate 


# Class Definition
class Stock(object):

    def __init__(self,stockName) :
        self.stockName = stockName
        self.stockTicker = yf.Ticker(self.stockName.upper())
        self.stockValue = self.stockTicker.history(period='2y',interval='1d',group_by='ticker')


    def updateGraphs(self) :
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
            coeff = (1/nDays)*sum(self.stockValue['Close'].array[-nDays])
        if kind == 'exp' :
            pass
    
         



if __name__ == '__main__':
    app.run_server(debug=True)