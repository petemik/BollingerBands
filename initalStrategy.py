from initalyPlayground import BollingerBand
import pandas as pd
import numpy as np
from utils import *
from DataManager import DataManager
import mplfinance as mpf
import matplotlib.pyplot as plt


class initialStrategy:
    """
    Simple strategy which looks for a squeeze of the Bollinger Band and then looks for direction of the next touch.
    No stop loss atm will look at implementing later.
    """
    def __init__(self, portfolio, params):
        # Start the process when all indicators are available
        self.portfolio = self._clean_portfolio(portfolio)
        # parameters
        self._set_params(params)
        self.add_indicators()

    def _set_params(self, params):
        try:
            self.prep_buy_window = params['prep_buy_window']
        except KeyError:
            # Default value
            self.prep_buy_window = 7
        try:
            self.window = params['window']
        except KeyError:
            self.window = 20
        try:
            self.width = params['width']
        except KeyError:
            self.width = 2
        try:
            self.bandwidth_window = params['bandwidth_window']
        except KeyError:
            self.bandwidth_window = 125

    def _clean_portfolio(self, portfolio):
        clean_portfolio = {}
        for tckr, data in portfolio.items():
            clean_data = data.dropna()
            clean_data.index.name = 'date'
            clean_data.reset_index(inplace=True)
            clean_data.insert(loc=len(clean_data.columns), column='next_open', value=clean_data['open'].shift(-1))
            clean_portfolio[tckr] = clean_data

        return clean_portfolio

    def add_indicators(self):
        for stock, data in self.portfolio.items():
            # Volume Indicator Intraday intensity https://www.investopedia.com/terms/i/intradayintensityindex.asp
            data['ma'] = data['close'].rolling(window=self.window).mean()
            data['std'] = data['close'].rolling(window=self.window).std()
            data['Bollinger High'] = data['ma'] + self.width * data['std']
            data['Bollinger Low'] = data['ma'] - self.width * data['std']
            data['Intensity'] = (((data['close'] * 2 - data['high'] - data['low'])
                                  / ((data['high'] - data['low']) * data['volume']))).rolling(window=20).mean()
            # A different volume indicator but I use intensity for the plots
            data['Volume Indicator'] = 100 * data['volume'] / data['volume'].rolling(window=50).mean()
            # This is a measure of how close to the band you are. 0 means hit lower band, 1 upper band, 0.5 means hitting moving average
            data['perc_b'] = (data['close'] - data['Bollinger Low']) / (data['Bollinger High'] - data['Bollinger Low'])
            # How wide the bands are, is a measure of volatility
            data['BandWidth'] = (data['Bollinger High'] - data['Bollinger Low']) / data['ma']
            # Gives an upper boundary for when bandwidth is high
            data['BandWidth High'] = data['BandWidth'].rolling(window=self.bandwidth_window).max()
            data['BandWidth Low'] = data['BandWidth'].rolling(window=self.bandwidth_window).min()
            # Measure of the trend
            data['Trend'] = data['ma'].diff().rolling(window=5).mean()
            data['Trend of Trend'] = data['Trend'].diff().rolling(window=15).mean()

    def plot_indicators(self, tckr='APA'):
        stock = self.portfolio[tckr]
        stock.index = pd.to_datetime(stock['date'])

        ap = [mpf.make_addplot(stock['Bollinger High'], color='b'), mpf.make_addplot(stock['Bollinger Low'], color='b'),
              mpf.make_addplot(stock['ma'], color='g'),
              mpf.make_addplot(stock['perc_b'], ylabel='perc_b', panel=1), mpf.make_addplot(np.ones(len(stock['perc_b'])), color='g', panel=1),
              mpf.make_addplot(np.zeros(len(stock['perc_b'])), color='g', secondary_y=False, panel=1),
              mpf.make_addplot(stock['Intensity'], ylabel='Volume', type='bar', panel=2),
              mpf.make_addplot(np.zeros(len(stock['perc_b'])), color='g', panel=2),
              mpf.make_addplot(stock['BandWidth'], ylabel='BandWidth',  panel=3), mpf.make_addplot(stock['BandWidth High'], panel=3),
              mpf.make_addplot(stock['BandWidth Low'], panel=3),
              mpf.make_addplot(stock['Trend'], ylabel='Trend', panel=4),
              mpf.make_addplot(stock['Trend of Trend'], ylabel='Trend Trend', panel=5)]
        mpf.plot(stock, type='candle', addplot=ap)
        plt.show()

    def generate_signals(self):
        # return_df = self.portfolio
        for tckr, data in self.portfolio.items():
            # 0 means no open position, 1 long open, -1 short open
            open_pos = 0
            prep_buy_date = None
            # open_signal represents when to open positions, close represents when to close positions
            open_signal = np.zeros(len(self.portfolio[tckr]))
            close = np.zeros(len(open_signal))
            for index, row in self.portfolio[tckr].iterrows():
                # If there is no open positio
                # If there is a squeeze prepare to buy
                if row['BandWidth'] < row['BandWidth Low']*1.1:
                    prep_buy_date = row['date']
                ## These are the two buy conditions
                # Open short if recently had a squeeze and now there is a touching of the  lower band
                if prep_buy_date is not None:
                    if calc_diff(starting=prep_buy_date, ending=row['date'], type='days') <= self.prep_buy_window \
                            and row['perc_b'] < 0:
                        open_signal[index] = -1
                    # Open long if recently had a squeeze and now there is a touching of the  lower band
                    elif calc_diff(starting=prep_buy_date, ending=row['date'], type='days') <= self.prep_buy_window \
                            and row['perc_b'] > 1:
                        open_signal[index] = 1
                # Now we are determining the close conditions as here there is an open_pos
                # The close condition is close when bandwidth balloons to suggest end of trend.
                if row['BandWidth'] > 0.8*row['BandWidth High']:
                    # -1 means close a short, 1 means close a long, 2 means close any open position
                    close[index] = 2

            data.insert(loc=len(data.columns), column='open_signal', value=open_signal)
            data.insert(loc=len(data.columns), column='close_signal', value=close)
        return self.portfolio

if __name__=='__main__':
    dm = DataManager()
    data = dm.getOneSector(sector="Energy", fromDate="2015-01-01", toDate="2017-06-01")
    # Worst performing
    #keys_to_extract = ['HES', 'HFC', 'PXD', 'HAL', 'MRO']
    # Best Performing
    #keys_to_extract = ['OKE', 'HFC', 'SLB', 'MPC', 'APA']
    keys_to_extract = ['HES', 'HFC', 'PXD', 'HAL', 'MRO', 'OKE', 'HFC', 'SLB', 'MPC', 'APA']
    data_subset = {key: data[key] for key in keys_to_extract}
    params = {}
    strat = initialStrategy(data_subset, {})
    strat.generate_signals()
    _ = 1














