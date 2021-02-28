import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
import numpy as np
import pandas as pd
from .forecast import AutoARIMA, prophet
from itertools import compress
from .utils import derivative, computeMinMax


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
        self.momentumDerivative = []
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
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.005, row_heights=[0.45, 0.1, 0.45], 
                specs=[[{"secondary_y": False}], [{"secondary_y": True}], [{"secondary_y": False}]])
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
            enterDay_20_50, exitDay_20_50, upsDate_20_50, positiveDiffs_20_50 = self.MA_buyLogic(self.EMA20, self.EMA50, self.stockValue['Close'][-len(self.EMA20):].index) 

            fig.add_trace(
                go.Scatter(
                    x=enterDay_20_50,
                    y=self.stockValue['Close'][enterDay_20_50],
                    mode="markers",
                    marker_color='blue',
                    marker_symbol=108,
                    name='Enter MA',
                    marker_line_width=8
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
                    marker_line_width=8
                ),
            row=1, col=1)
        if trigger_50_200 == 1 :
            enterDay_50_200, exitDay_50_200, upsDate_50_200, positiveDiffs_50_200 = self.MA_buyLogic(self.EMA50, self.SMA200, self.stockValue['Close'][-len(self.EMA50):].index) 
        

        # Plot the Momentum & Volume
        if Momentum == True :
            df = pd.DataFrame({'mom' : self.momentum, 'date' : self.stockValue['Close'].index[len(self.stockValue['Close'].array)-len(self.momentum):]})
            dMom = pd.DataFrame({'mom' : self.momentumDerivative, 'date' : self.stockValue['Close'].index[len(self.stockValue['Close'].array)-len(self.momentumDerivative):]})
            
            # Volume on secondary axis
            fig.add_trace(
                go.Bar(
                    x=self.stockValue['Close'].index,
                    y=self.stockValue['Volume'].values /max(self.stockValue['Volume']),
                    marker_color='silver',
                    name='Volume',
                ),row=2, col=1,
                secondary_y=True)
            fig['layout']['yaxis3'].update(range=[-0.6, 0.6])
            
            # Momentum
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['mom'],
                    marker=dict(
                        # cmax=max(df['mom']),
                        # cmid=0,
                        # cmin=min(df['mom']),
                        color='gray',
                        size=1,
                        autocolorscale=True
                    ),
                    name='Momentum',
                ),row=2, col=1,
                secondary_y=False)
            
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
        maxs, mins = computeMinMax(self.stockValue['Close'])
        fig.add_trace(
           go.Scatter(
               mode="markers",
               x=maxs,
               y=self.stockValue['Close'][maxs].array, 
               marker_symbol=6, marker_color='rgb(251,180,174)', marker_line_width=2,
               showlegend=False,
               name='MAX'),
            row=scatterPlotRow, col=1)
        fig.add_trace(
           go.Scatter(
               mode="markers",
               x=mins,
               y=self.stockValue['Close'][mins].array, 
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
                margin=dict(l=80, r=80, t=20, b=10),
            )
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]), #hide weekends
                #dict(values=["2015-12-25", "2016-01-01"])  # hide Christmas and New Year's
            ]
        )
        return fig


    def computeMomentum(self,nDays=14) :
        """
        Compute Momentum and its derivative

        Parameters
        ----------
        nDays : int, optional
            Days used to compute the momentum, by default 14
        """
        Mom = []
        for days in range(nDays,len(self.stockValue['Close'].array)) :
            Mom.append(self.stockValue['Close'].array[days] - self.stockValue['Close'].array[days-nDays])
        self.momentum = Mom
        self.momentumDerivative = derivative(self.momentum, schema='upwind', order='third')


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


    def MA_buyLogic(self, first, second, timeHistory) :
        """
        In Out market logic based on Moving Average only
        It will advice to buy when the first MA is above the second MA, typically 
        we use EMA20 as first and EMA50 as second

        Parameters
        ----------
        first : array
            moving average self object
        second : array
            moving average self object
        timeHistory : array.index
            indexes of the values which define the perimeter of the array

        Returns
        -------
        enterDay
            Days in which buy is wise (Delta >0)
        exitDay
            Days in which sell is wise (Delta <0)
        upsDate
            List of timestamps of positive deltas
        positiveDiffs
            List of values of the positive deltas
        """        
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
