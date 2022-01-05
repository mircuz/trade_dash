from dash import dcc
from dash import html
import dash_daq as daq
from datetime import date
import os
from .stockClass import Stock
from .server import app
from .dashCallbacks import updateGraph, updateStock, stockMem, globalStore


# Dashboard Layout
app.layout = html.Div([
    html.H2("CS Analytics Platform"),
    html.Div(className='row', children=[
            html.P(className='two columns', children="Enter the name of the Stock "),
            dcc.Input(className='two columns', id='stockName', value='BTCUSDT', type='text',debounce=True),
            dcc.Input(className='one columns', id='period_inspected', value='15d', type='text',debounce=True),
            dcc.Input(className='one columns', id='timeframe', value='30m', type='text',debounce=True),
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
                color='black',
            ),
            daq.BooleanSwitch(
                label='MACD',
                className='one columns',
                id='MACDToggle',
                on=False,
                color='#00BFFF',
            ),
            daq.BooleanSwitch(
                label='LSTM',
                className='one columns',
                id='LSTMToggle',
                on=False,
                color='lightcoral',
            ),
            daq.BooleanSwitch(
                label='Prophet',
                className='one columns',
                id='ProphetToggle',
                on=False,
                color='lightblue',
            ),
        ]
    ),
    html.Br(),
    html.H5(id='graphTitle', children=''),
    dcc.Graph(id='stockGraph', config={'scrollZoom':True}),

    dcc.ConfirmDialog(
        id='noDataFound',
        message='No Data Found, check Stock Name',
    ),
])
