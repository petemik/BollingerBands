from initalyPlayground import BollingerBand
import pandas as pd
import numpy as np
from utils import *
from DataManager import DataManager
import mplfinance as mpf
import matplotlib.pyplot as plt
from Analyzer import Analyzer


class initialStrategy(Analyzer):
    """
    Simple strategy which looks for a squeeze of the Bollinger Band and then looks for direction of the next touch.
    No stop loss atm will look at implementing later.
    """
    def __init__(self, portfolio, params):
        # Start the process when all indicators are available
        self.portfolio = self._clean_portfolio(portfolio)
        super().__init__(self.portfolio)

        # parameters
        self._set_params(params)
        self.add_indicators()

        # Variables used in the strategy
        self.open_pos = None
        self.entry_price = None
        self.entry_date = None
        self.close_price = None

    def _set_params(self, params):
        """
        Sets the parameters of the system to default values if not given in the dictionary
        """
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
        """
        Cleans the portfolio so that is adds in the next_open price as well sorting out indexes etc
        """
        clean_portfolio = {}
        for tckr, data in portfolio.items():
            clean_data = data.dropna()
            clean_data.index.name = 'date'
            clean_data.reset_index(inplace=True)
            clean_data.insert(loc=len(clean_data.columns), column='next_open', value=clean_data['open'].shift(-1))
            clean_portfolio[tckr] = clean_data

        return clean_portfolio

    def add_indicators(self):
        """
        Adds a bunch of indicators that are used in the strategy
        """
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
            data['Thin Band Touch'] = np.where((data['BandWidth'] < 1.1*data['BandWidth Low']), 1, 0)
            data['Thin Band Indicator'] = data['Thin Band Touch'].rolling(window=5).max()
            data['Thick Band Indicator'] = np.where((data['BandWidth'] > 0.8 * data['BandWidth High']), 1, 0)
            # Measure of the trend
            data['Trend'] = data['ma'].diff().rolling(window=5).mean()
            data['Trend of Trend'] = data['Trend'].diff().rolling(window=15).mean()

    def _reset_vars(self):
        self.entry_price = None
        self.entry_date = None
        self.close_price = None
        self.open_pos = None

    def _open_short(self, tckr, row):
        self._open_pos(tckr, row, direction=-1)

    def _open_long(self, tckr, row):
        self._open_pos(tckr, row, direction=1)

    def _open_pos(self, tckr, row, direction):
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

    def run(self):
        # THIS HERE IS THE STRATEGY. CAN POTENTIALLY EXTRAPOLATE OUT SLIGHTLY FURTHER BUT NOT SUFFICIENTLY COMPLEX YET
        for tckr, data in self.portfolio.items():
            self._reset_vars()
            open_signal = np.zeros(len(self.portfolio[tckr]))
            close_signal = np.zeros(len(open_signal))
            for index, row in self.portfolio[tckr].iterrows():
                # If there is no open position currently
                if self.open_pos is None:
                    # The conditions to open a position
                    if row['Thin Band Indicator'] == 1 and row['perc_b'] < 0:
                        self._open_short(tckr, row)
                        open_signal[index] = -1
                    elif row['Thin Band Indicator'] == 1 and row['perc_b'] > 1:
                        self._open_long(tckr, row)
                        open_signal[index] = 1
                # What to look for when position is open
                else:
                    # close_signal indicator
                    if row['Thick Band Indicator'] == 1:
                        if self.open_pos == 1:
                            self._close_pos(tckr, row)
                            close_signal[index] = 1
                        elif self.open_pos == -1:
                            self._close_pos(tckr, row)
                            close_signal[index] = -1
            if self.open_pos is not None:
                # Eventually need to do something about this
                print("Position is still open")
            data.insert(loc=len(data.columns), column='open_signal', value=open_signal)
            data.insert(loc=len(data.columns), column='close_signal', value=close_signal)

if __name__=='__main__':
    dm = DataManager()
    data = dm.getOneSector(sector="Energy", fromDate="2015-01-01", toDate="2017-06-01")
    # Worst performing
    # keys_to_extract = ['HES', 'HFC', 'PXD', 'HAL', 'MRO']
    # Best Performing
    # keys_to_extract = ['OKE', 'HFC', 'SLB', 'MPC', 'APA']
    keys_to_extract = ['HES', 'HFC', 'PXD', 'HAL', 'MRO', 'OKE', 'HFC', 'SLB', 'MPC', 'APA']
    data_subset = {key: data[key] for key in keys_to_extract}
    params = {}
    strat = initialStrategy(data_subset, params)
    # This generates the signals as well as the transaction and returns df
    strat.run()
    # This provides information about the strategy being run
    strat.analyze()
