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
        self.trans_df = self._get_transactions()
        self.rets_df = self._get_returns()
        self.cum_returns = sum(self.rets_df['return'])
        self.losers = self._get_ends(best=False)
        self.winners = self._get_ends(best=True)


    def _get_transactions(self):
        trans_df = pd.DataFrame(columns=['symbol', 'date', 'close', 'next_open', 'p', 'close_pos'])
        for tckr, data in self.portfolio.items():
            data.insert(loc=len(data.columns), column='next_open', value=data['open'].shift(-1))
            transaction = data[(data['p'] != 0) | (data['close_pos'] != 0)]
            trans_df = pd.concat([trans_df, transaction[['close', 'date', 'next_open', 'p', 'close_pos']]], axis=0, ignore_index=True)
            trans_df['symbol'].fillna(value=tckr, inplace=True)
        return trans_df

    def _get_returns(self):
        rets = self.trans_df
        rets['entry'] = rets['next_open'].shift(1)
        rets['entry_date'] = rets['date'].shift(1).astype(str)
        rets['date'] = rets['date'].astype(str)
        rets['return'] = (rets['next_open']/rets['entry'] - 1)*rets['close_pos']
        rets['pos_length'] = rets.apply(lambda x: calc_diff(x['entry_date'], x['date'], type='days'), axis=1)
        rets = rets[rets['close_pos'] != 0]
        return rets

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
        longs = stock_trans[stock_trans['p'] == 1]['next_open']
        shorts = stock_trans[stock_trans['p'] == -1]['next_open']
        close = stock_trans[stock_trans['close_pos'] != 0]['next_open']

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
            ap.append(mpf.make_addplot(stock['next_open_longs'], type='scatter', marker='^', color='g', markersize=100))
        if len(shorts) != 0:
            stock = stock.merge(shorts, how='left', left_index=True, right_index=True, suffixes=('', '_shorts'))
            ap.append(mpf.make_addplot(stock['next_open_shorts'], type='scatter', marker='v', color='g', markersize=100))
        if len(close) != 0:
            stock = stock.merge(close, how='left', left_index=True, right_index=True, suffixes=('', '_close'))
            ap.append(mpf.make_addplot(stock['next_open_close'], type='scatter', marker='^', color='r', markersize=100))
        mpf.plot(stock, type='candle', addplot=ap, title=tckr)
        plt.show()


if __name__ == '__main__':
    dm = DataManager()
    data = dm.getOneSector(sector="Energy", fromDate="2016-06-01", toDate="2018-06-01")
    params = {'window': 20}
    bt = Backtester(data, initialStrategy, params=params)
    print(bt.cum_returns)
    _ = 1
