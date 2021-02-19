import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import scipy.signal as signal
import numpy as np
import pandas as pd
from .forecast import AutoARIMA, prophet
from itertools import compress


# Class Definitions
class Stock(object) :
    """Class designed to collect stock info

    Attributes
    ----------
    stockName : str
        Name of the stock we want to investigate
    stockTicker : yfinance object
        Yahoo finance object which collect informations from the web
    stockValue : DataFrame
        DataFrame which collect the value of the stock splitted in Open, Close, Low and High
    momentum : DataFrame
        Dataframe representing the momentum index
    EMA20 : Array
        Array representing the exponential moving average of the last 20 days
    EMA50 : Array
        Array representing the exponential moving average of the last 50 days
    SMA200 : Array
        Array representing the simple moving average of the last 200 days
    figHandler : Plotly figure
        Handler to the figure


    Methods
    -------
    updateGraphs(EMA20,EMA50,SMA200,Momentum)
        Update Graphs rendering the class attributes
    
    layout_update(fig)
        Update the figure handler to fit better the screen

    computeMinMax()
        Compute local Maximum and Minimum 

    computeMomentum(nDays=15)
        Compute Momentum
    
    computeMA(nDays=20,kind='simple')
        Compute Moving Average
    """

    def __init__(self,stockName) :
        """
        Stock Constructor

        Parameters
        ----------
        stockName : str
            Name of the stock to investigate
        """
        self.stockName = stockName
        self.stockTicker = yf.Ticker(self.stockName.upper())
        self.stockValue = self.stockTicker.history(period='max',interval='1d',group_by='ticker') 
        self.momentum   = []
        self.EMA20      = []
        self.EMA50      = []
        self.SMA200     = []
        self.figHandler = []
        

    def updateGraphs(self,EMA20,EMA50,SMA200,Momentum,ARIMA,Prophet) :
        """
        Update the graphs embeded in figHandler with the class attributes queried

        Parameters
        ----------
        EMA20 : bool
            Trigger to render the attribute
        EMA50 : bool
            Trigger to render the attribute
        SMA200 : bool
            Trigger to render the attribute
        Momentum : bool
            Trigger to render the attribute
        ARIMA : bool
            Trigger to render the attribute
        Prophet : bool
            Trigger to render the attribute
        """
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
        trigger_20_50 = 0;  trigger_50_200 = 0  
        if SMA200 == True :
            fig.add_trace(
                go.Scatter(
                    x=self.stockValue['Close'][-len(self.SMA200):].index,
                    y=self.SMA200,
                    marker_color='#FF1493',
                    name='SMA200',
                ),
            row=1, col=1)
            trigger_50_200 += 0.5

        if EMA50 == True :
            fig.add_trace(
                go.Scatter(
                    x=self.stockValue['Close'][-len(self.EMA50):].index,
                    y=self.EMA50,
                    marker_color='#9400D3',
                    name='EMA50',
                ),
            row=1, col=1)
            trigger_20_50 += 0.5;   trigger_50_200 += 0.5
        
        if EMA20 == True :
            fig.add_trace(
                go.Scatter(
                    x=self.stockValue['Close'][-len(self.EMA20):].index,
                    y=self.EMA20,
                    marker_color='#4169E1',
                    name='EMA20',
                ),
            row=1, col=1)
            trigger_20_50 += 0.5

        if trigger_20_50 == 1 :
            enterDay_20_50, exitDay_20_50, upsDate_20_50, positiveDiffs_20_50 = self.MA_semaphore(self.EMA20, self.EMA50, self.stockValue['Close'][-len(self.EMA20):].index) 

            fig.add_trace(
                go.Scatter(
                    x=enterDay_20_50,
                    y=self.stockValue['Close'][enterDay_20_50],
                    mode="markers",
                    marker_color='blue',
                    marker_symbol=108,
                    name='Enter MA',
                    marker_line_width=4
                ),
            row=1, col=1)
            fig.add_trace(
                go.Scatter(
                    x=exitDay_20_50,
                    y=self.stockValue['Close'][exitDay_20_50],
                    mode="markers",
                    marker_color='#AF0038',
                    marker_symbol=107,
                    name='Exit MA',
                    marker_line_width=4
                ),
            row=1, col=1)
        if trigger_50_200 == 1 :
            enterDay_50_200, exitDay_50_200, upsDate_50_200, positiveDiffs_50_200 = self.MA_semaphore(self.EMA50, self.SMA200, self.stockValue['Close'][-len(self.EMA50):].index) 
        

        # Plot the Momentum 
        if Momentum == True :
            MomDays = len(self.stockValue['Close']) - len(self.momentum)
            df = pd.DataFrame({'mom' : self.momentum, 'date' : self.stockValue['Close'].index[MomDays:]})
            # Use different colors to identify momentum behaviours 
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
            
        # Bottom plot
        # ScatterPlot of closing values
        fig.add_trace(
            go.Scatter(
                x=self.stockValue['Close'].index,
                y=self.stockValue['Close'].array, 
                marker_color='black',
                name=self.stockName),
            row=scatterPlotRow, col=1)

        # Forecast
        if ARIMA == True :
            forecasted, lowerConfidence, upperConfidence = AutoARIMA(self)
            # Line
            fig.add_trace(
                go.Scatter(
                    mode="markers",
                    x=forecasted.index,
                    y=np.exp(forecasted.values),
                    name=self.stockName + ' Forecast',
                    marker_color='lightcoral',
                    marker_line_width=1),
                row=scatterPlotRow, col=1)
            # Upper threshold of confidence
            fig.add_trace(
                go.Scatter(
                    mode=None,
                    x=upperConfidence.index,
                    y=np.exp(upperConfidence.values),
                    fill=None,
                    marker_color='lightcoral',
                    name=self.stockName+' Forecast'),
                row=scatterPlotRow, col=1)
            # Lower threshold of confidence
            fig.add_trace(
                go.Scatter(
                    mode=None,
                    x=lowerConfidence.index,
                    y=np.exp(lowerConfidence.values),
                    fill='tonexty',
                    marker_color='lightcoral',
                    name=self.stockName+' Forecast'),
                row=scatterPlotRow, col=1)

        # Forecast
        if Prophet == True :
            prophetForecast = prophet(self)
            # Line
            fig.add_trace(
                go.Scatter(
                    mode="markers",
                    x=prophetForecast.ds,
                    y=np.exp(prophetForecast.yhat),
                    name=self.stockName + ' Prophet',
                    marker_color='blue',
                    marker_line_width=1),
                row=scatterPlotRow, col=1)
            # Upper threshold of confidence
            fig.add_trace(
                go.Scatter(
                    mode=None,
                    x=prophetForecast.ds[-90:],
                    y=np.exp(prophetForecast.yhat_upper[-90:]),
                    fill=None,
                    marker_color='lightblue',
                    name=self.stockName+' Forecast'),
                row=scatterPlotRow, col=1)
            # Lower threshold of confidence
            fig.add_trace(
                go.Scatter(
                    mode=None,
                    x=prophetForecast.ds[-90:],
                    y=np.exp(prophetForecast.yhat_lower[-90:]),
                    fill='tonexty',
                    marker_color='lightblue',
                    name=self.stockName+' Forecast'),
                row=scatterPlotRow, col=1)

        # Overlap local Minimun and Maximum to the bottom plot
        maxs, mins = self.computeMinMax()
        fig.add_trace(
           go.Scatter(
               mode="markers",
               x=self.stockValue['Close'][maxs[-30:]].index,
               y=self.stockValue['Close'].array[maxs[-30:]], 
               marker_symbol=6, marker_color='rgb(251,180,174)', marker_line_width=2,
               showlegend=False,
               name='MAX'),
            row=scatterPlotRow, col=1)
        fig.add_trace(
           go.Scatter(
               mode="markers",
               x=self.stockValue['Close'][mins[-30:]].index,
               y=self.stockValue['Close'].array[mins[-30:]], 
               marker_symbol=5, marker_color='#00CC96', marker_line_width=1,
               showlegend=False,
               name='MIN'),
           row=scatterPlotRow, col=1)

        # Finishing touches
        fig.update(layout_xaxis_rangeslider_visible=False)
        self.figHandler = self.layout_update(fig)
    

    def layout_update(self, fig) :
        """
        Update the figure handler to fit better the screen

        Parameters
        ----------
        fig : Plotly figure handler
            Figure handler on which the properties will be applied

        Returns
        -------
        fig : Plotly figure handler
            Figure handler on which the properties have been applied
        """
        fig.update_layout(
                showlegend=False,
                height=700,
                margin=dict(l=80, r=80, t=20, b=10)
                # shapes = [dict(
                #             x0='2020-08-09', x1='2020-08-09', 
                #             y0=0, y1=1, xref='x', yref='paper',
                #             line_width=2
                #         )],
            )
        return fig


    def computeMinMax(self) :
        """
        Compute local Maximum and Minimum in the last 90 days

        Returns
        -------
        list 
            List of the local Maximum of the stock
        list
            List of the local minimum of the stock 
        """
        # Reverse list to have the peaks tackled on the latest values instead of historical ones
        peaksList, _ = signal.find_peaks(self.stockValue['Close'].values[::-1],distance=10)
        lowsList, _ = signal.find_peaks(-self.stockValue['Close'].values[::-1],distance=10)
        return peaksList,lowsList


    def computeMomentum(self,nDays=15) :
        """
        Compute Momentum

        Parameters
        ----------
        nDays : int, optional
            Days used to compute the momentum, by default 15
        """
        Mom = []
        for days in range(len(self.stockValue['Close'].array[nDays:])) :
            Mom.append(self.stockValue['Close'].array[days] - self.stockValue['Close'].array[days-nDays])
        self.momentum = Mom[16:]


    def computeMA(self,nDays=20,kind='simple') :
        """
        Compute Moving averages

        Parameters
        ----------
        nDays : int, optional
            Days used to compute the moving average, by default 20
        kind : str, optional
            Specify if moving average is simple ('simple') or exponential ('exp'), 
            by default 'simple'

        Returns
        -------
        list
            Simple/Exponential Moving average of the last nDays
        """
        limit = 360     # Number of backward steps
        if kind == 'simple' :
            SMA = []
            for i in range(limit) :
                SMA.append((1/nDays)*sum(self.stockValue['Close'].array[np.arange(-i-nDays,-i)]))
            SMA.reverse()
            return SMA
        if kind == 'exp' :
            EMA = [(1/nDays)*sum(self.stockValue['Close'].array[-limit:-limit+nDays])]
            K = 2/(nDays+1)
            for i in range(1,limit) :
                EMA.append(K* (self.stockValue['Close'].array[-limit-nDays+i] - EMA[i-1]) + EMA[i-1])
            return EMA


    def trend_identification_minMax(self) :
        #TBD
        pass 


    def MA_semaphore(self, first, second, timeHistory) :
        # Delta first vs second positive => ascending trend
        zipped = zip(first, second[-len(first):])
        difference = [];    comp = []
        # Compute difference between two indexees
        for i, j in zipped :
            difference.append(i-j) 
        # Of the difference takes only the positive indexes
        for i in difference :
            comp.append(i>0)
        # Timestamp of the positive differences
        upsDate = timeHistory[comp]
        # Optional deltas between values to get better looking viz
        positiveDiffs = list(compress(difference, comp))
        # Compute best entry and exit from the market
        enterDay = [];  exitDay = []
        while comp != [] :
            # Compute the first day in which we had positive delta
            day = np.argwhere(np.array(comp)==True)
            if day.shape[0] == 0 : 
                break
            enterDay.append(timeHistory[day.min()])
            # Reduce the size of the array by discarding values before the enterDay
            comp = comp[day.min():];  timeHistory = timeHistory[day.min():]

            # Compute the first day in which we had negative delta
            day = np.argwhere(np.array(comp)==False)
            if day.shape[0] == 0 : 
                break
            exitDay.append(timeHistory[day.min()])
            # Reduce the size of the array by discarding values before the exitDay
            comp = comp[day.min():];  timeHistory = timeHistory[day.min():]
        
        return enterDay, exitDay, upsDate, positiveDiffs
