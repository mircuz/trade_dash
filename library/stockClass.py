import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import scipy.signal as signal
import numpy as np
import pandas as pd
from .forecast import train_model


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
        self.stockValue = self.stockTicker.history(period='5y',interval='1d',group_by='ticker') 
        self.momentum   = []
        self.EMA20      = []
        self.EMA50      = []
        self.SMA200     = []
        self.figHandler = []
        

    def updateGraphs(self,EMA20,EMA50,SMA200,Momentum,Forecast) :
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
        Forecast : bool
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
        if Forecast == True :
            predictions_time, predictions, mse = train_model(self)
            # Line
            fig.add_trace(
                go.Scatter(
                    mode="markers",
                    x=predictions_time,
                    y=predictions,
                    name=self.stockName + ' Forecast',
                    marker_color='lightcoral',
                    marker_line_width=1,
                    marker_symbol=41),
                row=scatterPlotRow, col=1)
            # Upper threshold of confidence
            fig.add_trace(
                go.Scatter(
                    mode=None,
                    x=predictions_time,
                    y=predictions+mse,
                    fill=None,
                    marker_color='lightcoral',
                    name=self.stockName+' Forecast'),
                row=scatterPlotRow, col=1)
            # Lower threshold of confidence
            fig.add_trace(
                go.Scatter(
                    mode=None,
                    x=predictions_time,
                    y=predictions-mse,
                    fill='tonexty',
                    marker_color='lightcoral',
                    name=self.stockName+' Forecast'),
                row=scatterPlotRow, col=1)

        # Overlap local Minimun and Maximum to the bottom plot
        maxs, mins = self.computeMinMax()
        fig.add_trace(
           go.Scatter(
               mode="markers",
               x=self.stockValue['Close'][maxs].index,
               y=self.stockValue['Close'].array[maxs], 
               marker_symbol=6, marker_color='rgb(251,180,174)', marker_line_width=2,
               showlegend=False,
               name='MAX'),
            row=scatterPlotRow, col=1)
        fig.add_trace(
           go.Scatter(
               mode="markers",
               x=self.stockValue['Close'][mins].index,
               y=self.stockValue['Close'].array[mins], 
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
        Compute local Maximum and Minimum 

        Returns
        -------
        list 
            List of the local Maximum of the stock
        list
            List of the local minimum of the stock 
        """
        peaksList, _ = signal.find_peaks(self.stockValue['Close'].array,distance=10)
        lowsList, _ = signal.find_peaks(-self.stockValue['Close'].array,distance=10)
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
