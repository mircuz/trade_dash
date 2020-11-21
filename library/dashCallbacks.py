from .server import app, cache
from .stockClass import Stock
import dash
from dash.dependencies import Input, Output, State


# Setup Shared Data
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