import dash
from flask_caching import Cache


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
TIMEOUT_CACHE = 150

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True

# Cache Setup
CACHE_CONFIG = {
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT' : TIMEOUT_CACHE
}

# Init cache
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)