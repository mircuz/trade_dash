import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import os
from .stockClass import Stock
from .server import app
from .dashCallbacks import updateGraph, updateStock, stockMem, globalStore


# Dash Layout
app.layout = html.Div([
    html.H2("Prototype of an Advisoring Dashboard"),
    html.Div(className='row', children=[
            html.P(className='two columns', children="Enter the name of the Stock "),
            dcc.Input(className='one columns', id='stockName', value='AAPL', type='text',debounce=True),
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
                color='#C0C0C0',
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
