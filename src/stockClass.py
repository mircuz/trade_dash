from time import time
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
import numpy as np
import pandas as pd
import os
from pyalgotrade.feed.csvfeed import Feed
import pyalgotrade.dataseries
import pyalgotrade.technical
from .forecast import AutoARIMA, prophet, lstm
from itertools import compress
from datetime import datetime, timedelta
from .utils import derivative, computeMinMax, nearest, nearest_yesterday, ColNum2ColName
from trendet import identify_df_trends


# Class Definitions
class Stock(object) :
    """Class designed to collect stock info

    Attributes
    ----------
    stockName : str
        Name of the stock we want to investigate
    stockTicker : yfinance object
        Yahoo finance object which collect informations from the web
    data : DataFrame
        DataFrame which collect the value of the stock splitted in Open, Close, Low and High


    Methods
    -------
    updateGraphs(EMA20,EMA50,SMA200,Momentum)
        Update Graphs rendering the class attributes
    
    layout_update(fig)
        Update the figure handler to fit better the screen
    """

    def __init__(self,stockName, period_inspected, timeframe, provider='yahoo') :
        """
        Stock Constructor

        Parameters
        ----------
        stockName : str
            Name of the stock to investigate

        period_inspected : str
            Length of the timeseries

        timeframe : str
            Time window of each bar
        """
        self.stockName = stockName.upper()
        if provider=='yahoo':
            self.stockTicker = yf.Ticker(self.stockName)
            self.stockTicker.history(
                period=period_inspected, 
                interval=timeframe, 
                group_by='ticker')\
                .to_csv('tickerDump.csv')
            self.data = Feed('Datetime', "%Y-%m-%d %H:%M:%S%z")

        elif provider=='binance':
            self.stockTicker=None
            self.data=None
        
        # Load Data
        self.data.addValuesFromCSV('tickerDump.csv')
        if os.path.exists("tickerDump.csv"): os.remove("tickerDump.csv")
        # Create dataseries
        self.DataSeries = self.data.createDataSeries(self.data.getKeys(), self.data._BaseFeed__maxLen) 
        # Extract data for plots
        df = pd.DataFrame(self.data._MemFeed__values, columns=['Datetime', 'features'])
        self.stockValue = pd.DataFrame(df['Datetime'])
        for key in self.data.getKeys(): 
            feature = [d.get(key) for d in df.iloc[:]['features']]
            self.stockValue[key] = feature
        self.figHandler = []
        

    def updateGraphs(self,EMA20,EMA50,SMA200,Momentum,MACD,LSTM,Prophet) :
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
        MACD : bool
            Trigger to render the attribute
        ARIMA : bool
            Trigger to render the attribute
        Prophet : bool
            Trigger to render the attribute
        """
        if ((Momentum == True) or (MACD == True)) :
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.005, row_heights=[0.30, 0.25, 0.45], 
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


        # Plot the Momentum & Volume
        if ((Momentum == True) or (MACD == True)) :
            df = pd.DataFrame({'mom' : self.momentum, 'date' : self.stockValue['Close'].index[len(self.stockValue['Close'].array)-len(self.momentum):]})
            dMom = pd.DataFrame({'mom' : self.momentumDerivative, 'date' : self.stockValue['Close'].index[len(self.stockValue['Close'].array)-len(self.momentumDerivative):]})
            
            # Volume on secondary axis
            fig.add_trace(
                go.Bar(
                    x=self.stockValue['Close'].index,
                    y=self.stockValue['Volume'].values /max(self.stockValue['Volume']),
                    marker_color='black',
                    name='Volume',
                    opacity=0.45,
                ),row=2, col=1,
                secondary_y=True)
            fig['layout']['yaxis3'].update(range=[-0.6, 0.6])
            
            if Momentum == True :
                # Momentum
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=df['mom'],
                        marker=dict(
                            color='black',
                            size=1,
                            autocolorscale=True
                        ),
                        name='Momentum',
                    ),row=2, col=1,
                secondary_y=False)

            if MACD == True :
                # MACD
                self.MACD = self.computeMACD()
                fig.add_trace(
                    go.Scatter(
                        x=self.stockValue['Close'][-len(self.MACD):].index,
                        y=self.MACD,
                        marker=dict(
                            color='#00BFFF',
                            size=1,
                            autocolorscale=True
                        ),
                        name='MACD',
                    ),row=2, col=1,
                secondary_y=False)
                # Overlap Maximum and Minimum of MACD
                dfMACD = pd.Series(data=self.MACD, index=self.stockValue['Close'].index[len(self.stockValue['Close'].array)-len(self.MACD):])
                self.dateMaxsMACD, self.dateMinsMACD = computeMinMax(dfMACD,length=200, tollerance=4.0)
                fig.add_trace(
                    go.Scatter(
                        mode="markers",
                        x=self.dateMaxsMACD,
                        y=dfMACD[self.dateMaxsMACD].array, 
                        marker_symbol=6, marker_color='#00CC96', marker_line_width=2,
                        showlegend=False,
                        name='MAX'),
                    row=2, col=1)
                fig.add_trace(
                    go.Scatter(
                        mode="markers",
                        x=self.dateMinsMACD,
                        y=dfMACD[self.dateMinsMACD].array, 
                        marker_symbol=5, marker_color='rgb(251,180,174)', marker_line_width=1,
                        showlegend=False,
                        name='MIN'),
                    row=2, col=1)
            

        # Bottom plot
        # ScatterPlot of closing values
        fig.add_trace(
            go.Scatter(
                x=self.stockValue['Close'].index,
                y=self.stockValue['Close'].array, 
                marker_color='black',
                name=self.stockName),
            row=scatterPlotRow, col=1)

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
            row=scatterPlotRow, col=1)
            trigger_50_200 += 0.5

        if EMA50 == True :
            fig.add_trace(
                go.Scatter(
                    x=self.stockValue['Close'][-len(self.EMA50):].index,
                    y=self.EMA50,
                    marker_color='#9400D3',
                    name='EMA50',
                ),
            row=scatterPlotRow, col=1)
            trigger_20_50 += 0.5;   trigger_50_200 += 0.5
        
        if EMA20 == True :
            fig.add_trace(
                go.Scatter(
                    x=self.stockValue['Close'][-len(self.EMA20):].index,
                    y=self.EMA20,
                    marker_color='#4169E1',
                    name='EMA20',
                ),
            row=scatterPlotRow, col=1)
            trigger_20_50 += 0.5

        # Suggested In/Out based on EMAs
        if trigger_20_50 == 1 :
            enterDay_20_50, exitDay_20_50 = self.MA_buyLogic(self.EMA20, self.EMA50, self.stockValue['Close'][-len(self.EMA50):].index) 
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
            row=scatterPlotRow, col=1)
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
            row=scatterPlotRow, col=1)
        if trigger_50_200 == 1 :
            enterDay_50_200, exitDay_50_200, upsDate_50_200, positiveDiffs_50_200 = self.MA_buyLogic(self.EMA50, self.SMA200, self.stockValue['Close'][-len(self.SMA200):].index) 
        
        # Forecast
        if LSTM == True :
            if self.LSTM_forecast == [] : self.LSTM_days, self.LSTM_forecast = lstm(self, epochs=10, trainingSetDim=0.85)
            #forecasted, lowerConfidence, upperConfidence = AutoARIMA(self)
            # Line
            fig.add_trace(
                go.Scatter(
                    mode="lines",
                    x=self.LSTM_days,
                    y=self.LSTM_forecast,
                    name='LSTM',
                    marker_color='lightcoral',
                    marker_line_width=1),
                row=scatterPlotRow, col=1)
            # # Upper threshold of confidence
            # fig.add_trace(
            #     go.Scatter(
            #         mode=None,
            #         x=upperConfidence.index,
            #         y=np.exp(upperConfidence.values),
            #         fill=None,
            #         marker_color='lightcoral',
            #         name=self.stockName+' Forecast'),
            #     row=scatterPlotRow, col=1)
            # # Lower threshold of confidence
            # # fig.add_trace(
            #     go.Scatter(
            #         mode=None,
            #         x=lowerConfidence.index,
            #         y=np.exp(lowerConfidence.values),
            #         fill='tonexty',
            #         marker_color='lightcoral',
            #         name=self.stockName+' Forecast'),
            #     row=scatterPlotRow, col=1)

        # Forecast
        # if Prophet == True :
        #     if self.prophetForecast.empty : self.prophetForecast, self.prophetForecast_m30 = prophet(self)
        #     days = self.prophetForecast.ds.dt.date.array
        #     days_m30 = self.prophetForecast_m30.ds.dt.date.array
        #     # Line of the prediction_m30
        #     fig.add_trace(
        #         go.Scatter(
        #             mode="lines",
        #             x=days_m30[-60:],
        #             y=np.exp(self.prophetForecast_m30.yhat[-60:]),
        #             name='Prophet t-30 Forecast',
        #             marker_color='lightcoral',
        #             marker_line_width=1),
        #         row=scatterPlotRow, col=1)
        #     # Line of the prediction
        #     fig.add_trace(
        #         go.Scatter(
        #             mode="lines",
        #             x=days[-45:],
        #             y=np.exp(self.prophetForecast.yhat)[-45:],
        #             name='Prophet Today Forecast',
        #             marker_color='#3283FE',
        #             marker_line_width=1),
        #         row=scatterPlotRow, col=1)
        #     # Upper threshold of confidence
        #     fig.add_trace(
        #         go.Scatter(
        #             mode=None,
        #             x=days[-60:],
        #             y=np.exp(self.prophetForecast.yhat_upper[-60:]),
        #             #fill=None,
        #             marker_color='lightblue',
        #             name=self.stockName+' Forecast'),
        #         row=scatterPlotRow, col=1)
        #     # Lower threshold of confidence
        #     fig.add_trace(
        #         go.Scatter(
        #             mode=None,
        #             x=days[-60:],
        #             y=np.exp(self.prophetForecast.yhat_lower[-60:]),
        #             #fill='tonexty',
        #             marker_color='lightblue',
        #             name=self.stockName+' Forecast'),
        #         row=scatterPlotRow, col=1)

        # Overlap local Minimun and Maximum to the bottom plot
        self.dateMaxs, self.dateMins = computeMinMax(self.stockValue['Close'])
        fig.add_trace(
           go.Scatter(
               mode="markers",
               x=self.dateMaxs,
               y=self.stockValue['Close'][self.dateMaxs].array, 
               marker_symbol=6, marker_color='#00CC96', marker_line_width=2,
               showlegend=False,
               name='MAX'),
            row=scatterPlotRow, col=1)
        fig.add_trace(
           go.Scatter(
               mode="markers",
               x=self.dateMins,
               y=self.stockValue['Close'][self.dateMins].array, 
               marker_symbol=5, marker_color='rgb(251,180,174)', marker_line_width=1,
               showlegend=False,
               name='MIN'),
           row=scatterPlotRow, col=1)
        # Plot shadowed areas based on trends TODO
        trends, enterDaysTrend, exitDaysTrend = self.minMaxTrend_buylogic(windowSize=6)
        labels = trends['UpTrend'].dropna().unique().tolist()
        for label in labels :
            fig.add_trace(
                    go.Scatter(
                        x=trends[trends['UpTrend'] == label]['Date'],
                        y=self.stockValue['Close'][trends[trends['UpTrend'] == label]['Date']],
                        mode="lines",
                        marker_color='green',
                        name='Positive Trend',
                    ),
                row=scatterPlotRow, col=1)
        labels = trends['DownTrend'].dropna().unique().tolist()
        for label in labels :
            fig.add_trace(
                    go.Scatter(
                        x=trends[trends['DownTrend'] == label]['Date'],
                        y=self.stockValue['Close'][trends[trends['DownTrend'] == label]['Date']],
                        mode="lines",
                        marker_color='orange',
                        name='Negative Trend',    
                    ),
                row=scatterPlotRow, col=1)


        # Finishing touches
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
        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update_layout(
                showlegend=False,
                height=700,
                margin=dict(l=80, r=80, t=20, b=10),
            )
        # fig.update_xaxes(
        #     rangebreaks=[
        #         dict(bounds=["sat", "mon"]), #hide weekends
        #         # dict(values=["2015-12-25", "2016-01-01"])  # hide Christmas and New Year's
        #     ]
        # )
        return fig


    # def computeMomentum(self,nDays=14) :
    #     """
    #     Compute Momentum (Rate of Change) and its derivative

    #     Parameters
    #     ----------
    #     nDays : int, optional
    #         Days used to compute the momentum, by default 14
    #     """
    #     Mom = []
    #     for days in range(nDays,len(self.stockValue['Close'].array)) :
    #         Mom.append(100*(self.stockValue['Close'].array[days] - self.stockValue['Close'].array[days-nDays])/self.stockValue['Close'].array[days-nDays])
    #     self.momentum = Mom
    #     self.momentumDerivative = derivative(self.momentum, schema='upwind', order='first')


    # def computeMA(self,nDays=20,kind='simple',limiter=None) :
    #     """
    #     Compute Moving averages

    #     Parameters
    #     ----------
    #     nDays : int, optional
    #         Days used to compute the moving average, by default 20
    #     kind : str, optional
    #         Specify if moving average is simple ('simple') or exponential ('exp'), 
    #         by default 'simple'
    #     limiter : int, optional
    #         Define the limit of backward steps, by default is None

    #     Returns
    #     -------
    #     list
    #         Simple/Exponential Moving average of the last nDays
    #     """
    #     # Number of backward steps
    #     if limiter != None : limit = min(len(self.stockValue['Close'])-nDays,limiter)     
    #     else : limit = len(self.stockValue['Close'])-nDays

    #     if kind == 'simple' :
    #         SMA = []
    #         for i in range(limit) :
    #             SMA.append((1/nDays)*sum(self.stockValue['Close'].array[np.arange(-i-nDays,-i)]))
    #         SMA.reverse()
    #         return SMA
    #     if kind == 'exp' :
    #         EMA = [(1/nDays)*sum(self.stockValue['Close'].array[-limit:-limit+nDays])]
    #         K = 2/(nDays+1)
    #         for i in range(1,limit) :
    #             EMA.append(K* (self.stockValue['Close'].array[-limit-nDays+i] - EMA[i-1]) + EMA[i-1])
    #         return EMA


    # def computeMACD(self,nDays=[3,10]) :
    #     shortTerm = self.computeMA(nDays=nDays[0])
    #     longTerm = self.computeMA(nDays=nDays[1])
    #     MACD = []
    #     for i in range(len(longTerm)) :
    #         MACD.append(shortTerm[i] - longTerm[i])
    #     return MACD


    # def minMaxTrend_buylogic(self, daysToSubtract=180, windowSize=3) :
    #     trend = []
    #     # At each iteration compare the value with last Min and Max 
    #     daysToSubtract = min(daysToSubtract, len(self.stockValue['Close']))
    #     for i in range(daysToSubtract) :
    #         lastMin = nearest_yesterday(self.dateMins, self.stockValue.iloc[-daysToSubtract+i].name)
    #         lastMax = nearest_yesterday(self.dateMaxs, self.stockValue.iloc[-daysToSubtract+i].name)
    #         if (lastMax == []) or (lastMin == []) : continue
    #         if self.stockValue['Close'][-daysToSubtract+i] > self.stockValue['Close'][lastMax] :
    #             trend.append((self.stockValue.iloc[-daysToSubtract+i].name,1))
    #         elif self.stockValue['Close'][-daysToSubtract+i] < self.stockValue['Close'][lastMin] :
    #             trend.append((self.stockValue.iloc[-daysToSubtract+i].name,-1))
    #         else :
    #             trend.append((self.stockValue.iloc[-daysToSubtract+i].name,0))


    #     # Count trends in a window
    #     weightedTrend = pd.DataFrame(columns=['Date','UpTrend','DownTrend'])
    #     labelN = 1
    #     label = ColNum2ColName(labelN)
    #     for i in range(windowSize, len(trend)) :
    #         # If at least 70% of points says it is a positive trend append as positive
    #         if [x[1] for x in trend[i-windowSize:i]].count(1) >= int(0.6*windowSize) : 
    #             toAppend = pd.DataFrame.from_dict({'Date':[trend[i][0]], 'UpTrend':[label]})
    #             weightedTrend = weightedTrend.append(toAppend)
    #         # Otherwise if 70% of points says it is a negative trend then append as negative
    #         elif [x[1] for x in trend[i-windowSize:i]].count(-1) >= int(0.6*windowSize) : 
    #             toAppend = pd.DataFrame.from_dict({'Date':[trend[i][0]], 'DownTrend':[label]})
    #             weightedTrend = weightedTrend.append(toAppend)
    #         # Else skip
    #         else :
    #             labelN +=1
    #             label = ColNum2ColName(labelN)
    #     labels = weightedTrend['UpTrend'].dropna().unique().tolist()
    #     enterDays = [];     exitDays = []
    #     for label in labels :
    #         if len(weightedTrend[weightedTrend['UpTrend'] == label]) < 4 : continue
    #         enterDays.append(weightedTrend[weightedTrend['UpTrend'] == label]['Date'].iloc[0])
    #         exitDays.append(weightedTrend[weightedTrend['UpTrend'] == label]['Date'].iloc[-1])
    #     return weightedTrend, enterDays, exitDays


    # def MA_buyLogic(self, first, second, timeHistory) :
    #     """
    #     In Out market logic based on Moving Average only
    #     It will advice to buy when the first MA is above the second MA, typically 
    #     we use EMA20 as first and EMA50 as second

    #     Parameters
    #     ----------
    #     first : array
    #         moving average self object
    #     second : array
    #         moving average self object
    #     timeHistory : array.index
    #         indexes of the values which define the perimeter of the array

    #     Returns
    #     -------
    #     enterDay
    #         Days in which buy is wise (Delta >0)
    #     exitDay
    #         Days in which sell is wise (Delta <0)
    #     upsDate
    #         List of timestamps of positive deltas
    #     positiveDiffs
    #         List of values of the positive deltas
    #     """        
    #     # Delta first vs second positive => ascending trend
    #     zipped = zip(first, second[-len(first):])
    #     difference = [];    comp = []
    #     # Compute difference between two indexees
    #     for i, j in zipped :
    #         difference.append(i-j) 
    #     # Of the difference takes only the positive indexes
    #     for i in difference :
    #         comp.append(i>0)

    #     # Create label list to define segments
    #     labelNumber = 1;    label = ColNum2ColName(labelNumber)
    #     labelArray = [label]
    #     for i in range(1,len(comp)):
    #         if comp[i] == comp[i-1] : 
    #             labelArray.append(label)
    #         else : 
    #             labelNumber += 1
    #             label = ColNum2ColName(labelNumber)
    #             labelArray.append(label)

    #     enterDay = [];  exitDay = []
    #     df = pd.DataFrame(data = list(zip(difference, timeHistory, comp, labelArray)), columns= ['difference', 'day', 'flagPositivity', 'label'])
    #     for l in labelArray :
    #         tempDf = df[
    #             (df['flagPositivity'] == 1) &
    #             (df['label'] == l)
    #         ]
    #         if not tempDf.empty :
    #             enterDay.append(tempDf['day'].iloc[0])
    #             exitDay.append(tempDf['day'].iloc[-1])
        
    #     return enterDay, exitDay


    # def computePercentualGain(self,start,end) : 
    #     array = self.stockValue.loc[start:end]['Close'].array
    #     yesterday_perc = 1
    #     for day in range(len(array)-1):
    #         today_perc = 1 + (array[day+1] - array[day])/array[day]
    #         today_perc*=yesterday_perc
    #         yesterday_perc=today_perc
    #     return today_perc