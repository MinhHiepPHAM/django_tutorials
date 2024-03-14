import requests
from django.conf import settings
import yfinance as yf


def get_stock_price(symbols,period='5d'):
    # base_url = 'https://www.alphavantage.co/query'
    # function = 'GLOBAL_QUOTE'

    stock_prices = dict()
    stock_volumes = dict()
    stock_changes = dict()
    for symbol in symbols:
        # params = {
        #     'symbol': symbol,
        #     'apikey': settings.ALPHA_VANTAGE_API_KEY,
        #     'function': function,
        # }

        try:
            symbol = symbol.upper()
            data = yf.download(symbol,period=period)
            # print(data)
            stock_prices[symbol] =  float("{:.2f}".format(data['Close'][-1]))  # Adjust this based on the actual API response
            stock_volumes[symbol] = data['Volume'][-1]
            stock_changes[symbol] = float("{:.2f}".format(data['Close'][-1]-data['Open'][0]))
        except KeyError:
            stock_prices[symbol] = None
            stock_volumes[symbol] = None
            stock_changes[symbol] = None
            
    return stock_prices, stock_volumes, stock_changes
