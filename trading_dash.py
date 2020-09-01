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
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.005)
        # OHLCPlot
        fig.add_trace(
            go.Ohlc(
                x=stockValue['Close'].index,
                open=stockValue['Open'].array,
                high=stockValue['High'].array,
                low=stockValue['Low'].array,
                close=stockValue['Close'].array),
            row=1, col=1)
        # ScatterPlot
        fig.add_trace(
            go.Scatter(
                x=stockValue['Close'].index,
                y=stockValue['Close'].array, 
                marker_color='black'),
            row=2, col=1)
        
        # MinMax Plot
        maxs, mins = computeMinMax(stockValue)
        fig.add_trace(
            go.Scatter(
                mode="markers",
                x=stockValue['Close'][maxs].index,
                y=stockValue['Close'].array[maxs], 
                marker_symbol='circle-open', marker_color='red', marker_line_width=5,
                showlegend=False),
            row=2, col=1)
        fig.add_trace(
            go.Scatter(
                mode="markers",
                x=stockValue['Close'][mins].index,
                y=stockValue['Close'].array[mins], 
                marker_symbol='circle-open', marker_color='green', marker_line_width=5,
                showlegend=False),
            row=2, col=1)

        fig.update(layout_xaxis_rangeslider_visible=False)
        fig = layout_update(fig, stockTicker)
        return fig
    else : 
        raise PreventUpdate 
    

def layout_update(fig, stockTicker) :
    fig.update_layout(
            showlegend=False,
            title=stockTicker.info['shortName'] + ' Stocks',
            height=700,
            shapes = [dict(
                        x0='2020-08-09', x1='2020-08-09', y0=0, y1=1, xref='x', yref='paper',
                        line_width=2)],
        )
    return fig
         

def computeMinMax(stockValue) :
    peaksList, _ = signal.find_peaks(stockValue['Close'].array,distance=5)
    lowsList, _ = signal.find_peaks(-stockValue['Close'].array,distance=5)
    return peaksList,lowsList





if __name__ == '__main__':
    app.run_server(debug=True)