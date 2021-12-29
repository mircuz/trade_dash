from time import time
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
import numpy as np
import pandas as pd
import os
from .yfinancefeed import Feed as YFinanceFeed
from .strats.OliStrat import testFunction
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
            # Compute delta time to establish proper Frequency choice
            # Compute proper timezone
            self.data = YFinanceFeed(frequency=60)
            self.data.addBarsFromCSV(self.stockName, 'tickerDump.csv')

        elif provider=='binance':
            self.stockTicker=None
            self.data=None
        
        # Purge downloaded csv
        if os.path.exists("tickerDump.csv"): os.remove("tickerDump.csv")
         
        # Extract data for plots
        df = pd.DataFrame(self.data._MemFeed__values, columns=['Datetime', 'features'])
        self.stockValue = pd.DataFrame(df['Datetime'])
        for key in self.data.getKeys(): 
            feature = [d.get(key) for d in df.iloc[:]['features']]
            self.stockValue[key] = feature

        self.data_skips_weekends = True    #TODO Setup a mech to populate this flag
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
        # OHLC Plot
        fig.add_trace(
            go.Ohlc(
                x=self.stockValue['Datetime'].array,
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
                x=self.stockValue['Datetime'].array,
                y=self.stockValue['Close'].array, 
                marker_color='black',
                name=self.stockName),
            row=scatterPlotRow, col=1)

        # Optional Moving Average Plots
        if EMA20 == True :
            testFunction(self)
            fig.add_trace(
                go.Scatter(
                    x=self.stockValue['Close'][-len(self.EMA20):].index,
                    y=self.EMA20,
                    marker_color='#4169E1',
                    name='EMA20',
                ),
            row=scatterPlotRow, col=1)
            

        
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

        # # Overlap local Minimun and Maximum to the bottom plot
        # self.dateMaxs, self.dateMins = computeMinMax(self.stockValue['Close'])
        # fig.add_trace(
        #    go.Scatter(
        #        mode="markers",
        #        x=self.dateMaxs,
        #        y=self.stockValue['Close'][self.dateMaxs].array, 
        #        marker_symbol=6, marker_color='#00CC96', marker_line_width=2,
        #        showlegend=False,
        #        name='MAX'),
        #     row=scatterPlotRow, col=1)
        # fig.add_trace(
        #    go.Scatter(
        #        mode="markers",
        #        x=self.dateMins,
        #        y=self.stockValue['Close'][self.dateMins].array, 
        #        marker_symbol=5, marker_color='rgb(251,180,174)', marker_line_width=1,
        #        showlegend=False,
        #        name='MIN'),
        #    row=scatterPlotRow, col=1)
        # # Plot shadowed areas based on trends TODO
        # trends, enterDaysTrend, exitDaysTrend = self.minMaxTrend_buylogic(windowSize=6)
        # labels = trends['UpTrend'].dropna().unique().tolist()
        # for label in labels :
        #     fig.add_trace(
        #             go.Scatter(
        #                 x=trends[trends['UpTrend'] == label]['Date'],
        #                 y=self.stockValue['Close'][trends[trends['UpTrend'] == label]['Date']],
        #                 mode="lines",
        #                 marker_color='green',
        #                 name='Positive Trend',
        #             ),
        #         row=scatterPlotRow, col=1)
        # labels = trends['DownTrend'].dropna().unique().tolist()
        # for label in labels :
        #     fig.add_trace(
        #             go.Scatter(
        #                 x=trends[trends['DownTrend'] == label]['Date'],
        #                 y=self.stockValue['Close'][trends[trends['DownTrend'] == label]['Date']],
        #                 mode="lines",
        #                 marker_color='orange',
        #                 name='Negative Trend',    
        #             ),
        #         row=scatterPlotRow, col=1)


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
        if self.data_skips_weekends == True:
            fig.update_xaxes(
                rangebreaks=[
                    dict(bounds=["sat", "mon"]), #hide weekends
                    # dict(values=["2015-12-25", "2016-01-01"])  # hide Christmas and New Year's
                ]
            )
        return fig
