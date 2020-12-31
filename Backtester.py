from initalStrategy import initialStrategy
from DataManager import DataManager
from utils import *
import numpy as np
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt


class Backtester:
    def __init__(self, portfolio, strat, params):
        params = params
        self.strat = strat(portfolio, params)
        # Not a huge fan of this.
        # Returns the portfolio with the signals columns
        self.portfolio = self.strat.generate_signals()
        self.beta = None
        self.open_pos = None
        self.entry_price = None
        self.entry_date = None
        self.close_price = None
        self.rets_df = pd.DataFrame(columns=['symbol', 'entry_date', 'close_date', 'days_held', 'direction',
                                             'entry_price', 'close_price', 'return'])
        self.trans_df = pd.DataFrame(columns=['symbol', 'date', 'direction', 'close', 'price'])
        self.backtest()
        self.losers = self._get_ends(best=False)
        self.winners = self._get_ends(best=True)
        self.total_returns = sum(self.rets_df['return'])

    def _reset_vars(self):
        self.entry_price = None
        self.entry_date = None
        self.close_price = None
        self.open_pos = None

    def _open_pos(self, tckr, row):
        direction = row['open_signal']
        self.open_pos = direction
        self.entry_date = row['date']
        self.entry_price = row['next_open']
        self.trans_df = self.trans_df.append(
            {'symbol': tckr, 'date': self.entry_date, 'direction': direction, 'close': 0, 'price': self.entry_price},
            ignore_index=True)

    def _close_pos(self, tckr, row):
        close_date = row['date']
        close_price = row['next_open']
        returns = (close_price / self.entry_price - 1) * self.open_pos
        days_held = calc_diff(self.entry_date, close_date, type='days')
        self.trans_df = self.trans_df.append(
            {'symbol': tckr, 'date': close_date, 'direction': self.open_pos, 'close': 1, 'price': close_price},
            ignore_index=True)
        self.rets_df = self.rets_df.append({'symbol': tckr, 'entry_date': self.entry_date, 'close_date': close_date,
                                            'days_held': days_held, 'direction': self.open_pos,
                                            'entry_price': self.entry_price, 'close_price': close_price,
                                            'return': returns}, ignore_index=True)
        # reset Variables
        self._reset_vars()

    def backtest(self):
        for tckr, data in self.portfolio.items():
            for index, row in self.portfolio[tckr].iterrows():
                # If no position is open
                if self.open_pos is None:
                    if row['open_signal'] != 0:
                        self._open_pos(tckr=tckr, row=row)
                elif self.open_pos == 1:
                    if row['close_signal'] == 1 or row['close_signal'] == 2:
                        self._close_pos(tckr=tckr, row=row)
                elif self.open_pos == -1:
                    if row['close_signal'] == -1 or row['close_signal'] == 2:
                        self._close_pos(tckr=tckr, row=row)
            if self.open_pos is not None:
                print("Position is still open")
                self._reset_vars()


    def _get_ends(self, best=True):
        if best is True:
            end = self.rets_df[self.rets_df['return'] > 0].sort_values(by='return', ascending=False)
        else:
            end = self.rets_df[self.rets_df['return'] < 0].sort_values(by='return', ascending=True)
        return end

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


if __name__ == '__main__':
    dm = DataManager()
    data = dm.getOneSector(sector="Energy", fromDate="2016-06-01", toDate="2018-06-01")
    params = {'window': 20}
    bt = Backtester(data, initialStrategy, params=params)
    # bt.plot_tckr('APA')
    print(bt.total_returns)
    _ = 1
