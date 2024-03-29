import yfinance as yf
# from matplotlib import pyplot as plt
import pandas as pd
import plotly.graph_objects as go 
from datetime import datetime, timedelta
from stock_price import models


class StockInfo:
    def __init__(self, symbol):
        self.symbol = symbol
        self.close_price = 0
        self.open_price = 0
        self.volume = 0
        self.change = 0
    
    def get_stock_price(self, data):
        if data:
            try:
                return float("{:.2f}".format(data[self.symbol]['Close'][-1]))
            except Exception:
                print('FAILED DOWNLOAD CLOSE PRICE INFO',self.symbol)
                return 0
        else:
            return 0
    
    def get_open_price(self, data):
        if data:
            try:
                return float("{:.2f}".format(data[self.symbol]['Open'][0]))
            except Exception:
                print('FAILED DOWNLOAD OPEN PRICE INFO',self.symbol)
                return 0
        else:
            return 0
        
    def get_stock_volume(self, data):
        if data:
            try:
                return data[self.symbol]['Volume'][-1]
            except Exception:
                print('FAILED DOWNLOAD VOLUME INFO',self.symbol)
                return 0
        else:
            return 0
        
    def get_stock_change(self):
        return float("{:.2f}".format(self.close_price-self.open_price))
    
    def __eq__(self, other):
        return self.symbol.lower() == other.symbol.lower()
    
    def __hash__(self) -> int:
        return hash(self.symbol)

class StockData:
    def __init__(self, period) -> None:
        self.period = period
        self.data = dict()
        self.stocks = list()
    
    def download_data(self,symbol, period, interval):
        try:
            symbol = symbol.upper()
            data = yf.download(symbol,period=period,interval=interval)
        except Exception:
            print('FAILED TO DOWNLOAD: ', symbol)
            data = None
        
        self.data[symbol] = data

    def add_stock(self,symbol):
        stock = StockInfo(symbol)
        if self.period == '1d':
            interval = '60m'
        else:
            interval = '1d'
        self.download_data(symbol,self.period,interval)
        stock.close_price = stock.get_stock_price(self.data)
        stock.open_price = stock.get_open_price(self.data)
        stock.volume = stock.get_stock_volume(self.data)
        stock.change = stock.get_stock_change()
        if stock not in self.stocks:
            self.stocks.append(stock)
    
    def get_stock(self,symbol):
        for stock in self.stocks:
            if stock.symbol == symbol: return stock
        return None # TODO:create None stock is better ?

    def get_time_span(self,data_frame, period):
        if period == '1d':
            timespan = pd.to_datetime(data_frame.index.hour.astype(str) + ':' + data_frame.index.minute.astype(str), format='%H:%M').time
        else:
            timespan = data_frame.index
        return timespan
    
    def plot_stock(self, symbols, period, title):
        fig = go.Figure()
        colors = ['blue', 'red', '#cc8c14', '#28a317', 'black']
        for i, symbol in enumerate(symbols):
            data = self.data[symbol]
            df = pd.DataFrame(data)

            timespan = self.get_time_span(df,period)
            
            # Add trace for stock prices
            fig.add_trace(go.Scatter(x=timespan, y=df['Adj Close'], mode='lines+markers', name=symbol, 
                                    line=dict(color=colors[i], width=1),
                                    marker=dict(color=colors[i], size=3),
                                    hoverinfo='y'))

        # Update layout
        if period == '1d':
            tickformat = 'HH:MM'
        else:
            tickformat = '%m-%d-%Y'
        fig.update_layout(
            title=title,
            xaxis=dict(title='Time', tickformat=tickformat, showgrid=False),
            yaxis=dict(title='Price', showgrid=False),
            showlegend=True,
            legend=dict(x=0, y=1.1, orientation='h'),
            plot_bgcolor='white',
            # autosize=True,
            margin=dict(l=40, r=40, t=80, b=40),
        )

        return fig.to_html(full_html=False)
    
class StockNew:
    def __init__(self, url, headline, symbol):
        self.url = url
        self.headline = headline
        self.symbol = symbol

    def __eq__(self, other: object):
        return self.url == other.url and self.symbol == other.symbol
    
    def __hash__(self):
        return hash((self.url,self.headline))

class News:
    def __init__(self):
        self.new_per_symbol = dict() # new per stock symbol
        self.recent_stock_news = list() # store the stock of recent week

    def add_new(self, new):
        if new.symbol not in self.new_per_symbol:
            self.new_per_symbol[new.symbol] = {new}
        else:
            self.new_per_symbol[new.symbol].add(new)

    # get the stock_news from the past week
    # and maybe delete the new if the url is not still actived
    def read_recent_news_from_db(self, n_day=3):
        one_week_ago = datetime.now() - timedelta(days=n_day)
        object_datas = models.NewsModel.objects.filter(scrapped_date__gte=one_week_ago).order_by('scrapped_date')
        for data in object_datas:
            new = StockNew(data.url, data.headline, data.symbol)
            self.recent_stock_news.append(new)
            self.add_new(new)

    def check_new_in_db(self,symbol, url):
        stock_new = StockNew(url=url, symbol=symbol,headline='')
        return stock_new in self.recent_stock_news
        

