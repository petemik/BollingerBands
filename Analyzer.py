from initalStrategy import initialStrategy
from DataManager import DataManager
from utils import *
import numpy as np
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt


class Analyzer:
    def __init__(self, portfolio):
        self.portfolio = portfolio

        # Not a huge fan of this.
        # Returns the portfolio with the signals columns
        self.rets_df = pd.DataFrame(columns=['symbol', 'entry_date', 'close_date', 'days_held', 'direction',
                                             'entry_price', 'close_price', 'return'])
        self.trans_df = pd.DataFrame(columns=['symbol', 'date', 'direction', 'close', 'price'])
        self.losers = None
        self.winners = None
        self.total_returns = None

    def get_returns(self):
        self.total_returns = np.sum(self.rets_df['return'])

    def get_losers_winners(self):
        self.losers = self._get_ends(best=False)
        self.winners = self._get_ends(best=True)

    def get_sharpe(self):
        print("Not implemented yet")

    def _get_ends(self, best=True):
        if best is True:
            end = self.rets_df[self.rets_df['return'] > 0].sort_values(by='return', ascending=False)
        else:
            end = self.rets_df[self.rets_df['return'] < 0].sort_values(by='return', ascending=True)
        return end

    def analyze(self):
        self.get_returns()
        self.get_losers_winners()
        print("\n\n")
        print("Total Cumulative Returns: {}%".format(round(self.total_returns, 2)*100))
        print("The 5 biggest losers were: \n")
        print(self.losers.head(n=5))
        print("The 5 biggest winners were: \n")
        print(self.winners.head(n=5))

        while True:
            print("\n\n")
            request = input("Which stock do you want to see? \n Type h for help \n")
            if request == "h":
                print("The options are: ")
                print("Type \'e\' to exit program")
                print("Type \'l\' to see available stocks")
                print("Type \'[Stock Ticker]\' to get a plot of that stock")
            elif request == 'e':
                break
            elif request == 'l':
                print(self.portfolio.keys())
            elif request in list(self.portfolio.keys()):
                self.plot_tckr(request)
            else:
                print("Sorry, did not recognise this request")

    def plot_tckr(self, tckr='APA'):
        stock = self.portfolio[tckr]
        if 'date' in stock.columns:
            stock.index = pd.to_datetime(stock['date'])
            del stock['date']
        stock_trans = self.trans_df[self.trans_df['symbol'] == tckr]
        if 'date' in stock_trans.columns:
            stock_trans.index = pd.to_datetime(stock_trans['date'])
        longs = stock_trans[(stock_trans['direction'] == 1) & (stock_trans['close'] == 0)]['price'].rename('price_longs')
        shorts = stock_trans[(stock_trans['direction'] == -1) & (stock_trans['close'] == 0)]['price'].rename('price_shorts')
        close = stock_trans[stock_trans['close'] != 0]['price'].rename('price_close')

        ap = [mpf.make_addplot(stock['Bollinger High'], color='b'), mpf.make_addplot(stock['Bollinger Low'], color='b'),
              mpf.make_addplot(stock['ma'], color='g'),
              mpf.make_addplot(stock['perc_b'], ylabel='perc_b', panel=1),
              mpf.make_addplot(np.ones(len(stock['perc_b'])), color='g', panel=1),
              mpf.make_addplot(np.zeros(len(stock['perc_b'])), color='g', secondary_y=False, panel=1),
              mpf.make_addplot(stock['Intensity'], ylabel='Volume', type='bar', panel=2),
              mpf.make_addplot(stock['BandWidth'], ylabel='BandWidth', panel=3),
              mpf.make_addplot(stock['BandWidth High'], panel=3),
              mpf.make_addplot(stock['BandWidth Low'], panel=3),
              mpf.make_addplot(stock['Trend'], ylabel='Trend', panel=4)]

        if len(longs) != 0:
            stock = stock.merge(longs, how='left', left_index=True, right_index=True, suffixes=('', '_longs'))
            ap.append(mpf.make_addplot(stock['price_longs'], type='scatter', marker='^', color='g', markersize=100))
        if len(shorts) != 0:
            stock = stock.merge(shorts, how='left', left_index=True, right_index=True, suffixes=('', '_shorts'))
            ap.append(mpf.make_addplot(stock['price_shorts'], type='scatter', marker='v', color='g', markersize=100))
        if len(close) != 0:
            stock = stock.merge(close, how='left', left_index=True, right_index=True, suffixes=('', '_close'))
            ap.append(mpf.make_addplot(stock['price_close'], type='scatter', marker='^', color='r', markersize=100))
        mpf.plot(stock, type='candle', addplot=ap, title=tckr)
        plt.show()

