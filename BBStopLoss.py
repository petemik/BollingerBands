import pandas as pd
import numpy as np
from utils import *
from DataManager import DataManager
import mplfinance as mpf
import matplotlib.pyplot as plt
from BaseStrategy import BaseStrategy
from Analyzer import Analyzer

class BBStopLoss(BaseStrategy):
    """
    Simple strategy which looks for a squeeze of the Bollinger Band and then looks for direction of the next touch.
    Adds a stop loss to the strategy BollingerBandInitial which is the simplest form of Bolling Band Strategy
    """
    def __init__(self, portfolio, params):
        # Start the process when all indicators are available
        # Something weird going on here with copy,still changes the original???
        # self.portfolio = portfolio.copy()
        self.portfolio = portfolio
        super().__init__()
        # parameters
        self._set_params(params)
        self.add_indicators()
        _ = 1
        # Variables used in the strategy

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
        try:
            self.stop_loss_perc = params['stop_loss_perc']
        except KeyError:
            self.stop_loss_perc = 0.1
        try:
            self.perc_b_upper_threshold = params['perc_b_upper_threshold']
        except KeyError:
            self.perc_b_upper_threshold = 1
        try:
            self.perc_b_lower_threshold = params['perc_b_lower_threshold']
        except KeyError:
            self.perc_b_lower_threshold = 0




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

    def run(self):
        """
        This is the actual strategy
        """
        for tckr, data in self.portfolio.items():
            self._reset_vars()
            open_signal = np.zeros(len(self.portfolio[tckr]))
            close_signal = np.zeros(len(open_signal))
            for index, row in self.portfolio[tckr].iterrows():
                # If there is no open position currently
                if self.open_pos is None:
                    # The conditions to open a position
                    if row['Thin Band Indicator'] == 1 and row['perc_b'] < self.perc_b_lower_threshold:
                        self._open_short(tckr, row)
                        open_signal[index] = -1
                    elif row['Thin Band Indicator'] == 1 and row['perc_b'] > self.perc_b_upper_threshold:
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
                    # Shorter way of saying if price crosses the
                    elif self.open_pos*row['close'] < self.open_pos * self.stop_price:
                        if self.open_pos == 1:
                            self._close_pos(tckr, row)
                            close_signal[index] = 1
                        elif self.open_pos == -1:
                            self._close_pos(tckr, row)
                            close_signal[index] = -1
            if self.open_pos is not None:
                # Eventually need to do something about this
                do_something = True
                # print("Position is still open")
            data.insert(loc=len(data.columns), column='open_signal', value=open_signal)
            data.insert(loc=len(data.columns), column='close_signal', value=close_signal)


if __name__ == '__main__':
    path_to_data = 'C:\\Users\\petem\\Trading\\Data\\S&P\\'
    dm = DataManager(path_to_data=path_to_data)
    sectors = ["Communication Services", "Consumer Discretionary", "Consumer Staples", "Energy", "Financials",
               "Health Care", "Industrials", "Information Technology", "Materials", "Real Estate", "Utilities"]
    data = dm.get_one_sector_SP(sector=sectors[0], fromDate="2015-06-01", toDate="2018-01-01")
    # keys_to_extract = ['CVX']
    # data_subset = {key: data[key] for key in keys_to_extract}
    data = dm.prepare_data(data_dict=data)
    # data_subset = dm.prepare_data(data_dict=data_subset)
    strat = BBStopLoss(data, params={'stop_loss_perc': 1})
    # strat = BBStopLoss(data, params={'stop_loss_perc': 0.2})
    analyzer = Analyzer(strat)
    analyzer.analyze()

