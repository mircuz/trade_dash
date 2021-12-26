from src.layout import app
from waitress import serve

DEBUG_STATUS = False

# MAIN
if __name__ == '__main__':
    if DEBUG_STATUS == False:
        serve(app.server, host='0.0.0.0', port=8050)
    else: 
        app.run_server(debug=True)