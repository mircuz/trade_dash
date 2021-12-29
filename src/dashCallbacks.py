from .server import app, cache, TIMEOUT_CACHE
from .stockClass import Stock
import dash
from dash.dependencies import Input, Output, State


# Setup the Stock object into the cache
stockMem = []

@cache.memoize(timeout=TIMEOUT_CACHE)
def globalStore(name, period_inspected, timeframe) :
    """
    Used to cache the stock

    Parameters
    ----------
    name : str
        Name of the stock to load

    Returns
    -------
    Object
        Stock object accessible across the callbacks
    """
    global stockMem
    stockMem = Stock(name, period_inspected, timeframe)
    # if stockMem.stockValue.empty is False :
    #     stockMem.computeMomentum()
    #     stockMem.EMA20  = stockMem.computeMA(nDays=20, kind='exp')
    #     stockMem.EMA50  = stockMem.computeMA(nDays=50, kind='exp')
    #     stockMem.SMA200 = stockMem.computeMA(nDays=200, kind='simple')
    return stockMem


# Callbacks
@app.callback(
    [Output('graphTitle','children'),
     Output('noDataFound', 'displayed')],
     Input('stockName','value'),
     Input('period_inspected','value'),
     Input('timeframe','value')
)
def updateStock(stockName, period_inspected, timeframe) :
    """
    Takes the stock name queried by the user and use it to
    generate a new stock object 

    Parameters
    ----------
    stockName : str
        Name of the stock to investigate

    Returns
    -------
    list
        The first entry of the list represent the name of the stock
        which will be used as new graph title
        The second entry is used to trigger the noDataFound popup
    """
    if len(stockName)>0:
        globalStore(stockName, period_inspected, timeframe)
        if stockMem.stockValue.empty is False :
            try : 
                return [
                        [stockMem.stockTicker.info['shortName'] + ' Stocks'],
                        False
                    ]
            except :
                return [
                        [stockMem.stockTicker.ticker + ' Stocks'],
                        False
                    ]
        else :
            return [
                    dash.no_update,
                    True
                ]
    else :
        return [
                dash.no_update,
                True
            ]


@app.callback(
    [Output('stockGraph','figure')],
    [Input('graphTitle','children'),
     Input('EMA20Toggle','on'),
     Input('EMA50Toggle','on'),
     Input('SMA200Toggle','on'),
     Input('MomentumToggle','on'),
     Input('MACDToggle','on'),
     Input('LSTMToggle','on'),
     Input('ProphetToggle','on')]
    )
def updateGraph(stockName,EMA20,EMA50,SMA200,Momentum,MACD,LSTM,Prophet) :
    """
    This routine is used to render the graph and act as interface 
    between the dashboard and the Stock class method updateGraphs 

    Parameters
    ----------
    stockName : str
        Trigger used to call this routine after updateStock(stockName) 
    EMA20 : bool
        See Stock.updateGraphs
    EMA50 : bool
        See Stock.updateGraphs
    SMA200 : bool
        See Stock.updateGraphs
    Momentum : bool
        See Stock.updateGraphs
    Forecast : bool
        See Stock.updateGraphs

    Returns
    -------
    Plotly figure handler
        Figure which will be rendered
    """
    if stockMem.stockValue.empty is False :
        stockMem.updateGraphs(EMA20,EMA50,SMA200,Momentum,MACD,LSTM,Prophet)
        return [stockMem.figHandler]
    else :
        return [dash.no_update]
