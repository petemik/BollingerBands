from DataManager import DataManager
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np

class BollingerBand:
    """
    Has to be careful around splits and dividends
    """
    def __init__(self, portfolio, params):
        self.portfolio = portfolio

        self.window = 20
        self.width = 2

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
            data['Volume Indicator'] = 100 * data['volume']/data['volume'].rolling(window=50).mean()
            # This is a measure of how close to the band you are. 0 means hit lower band, 1 upper band, 0.5 means hitting moving average
            data['perc_b'] = (data['close'] - data['Bollinger Low'])/(data['Bollinger High'] - data['Bollinger Low'])
            # How wide the bands are, is a measure of volatility
            data['BandWidth'] = (data['Bollinger High'] - data['Bollinger Low']) / data['ma']
            # Gives an upper boundary for when bandwidth is high
            data['BandWidth High'] = data['BandWidth'].rolling(window=125, min_periods=75).max()
            data['BandWidth Low'] = data['BandWidth'].rolling(window=125, min_periods=75).min()
            # Measure of the trend
            data['Trend'] = data['ma'].diff().rolling(window=5).mean()
            data['Trend of Trend'] = data['Trend'].diff().rolling(window=15).mean()


    def plot_indicators(self, tckr='APA'):
        stock = self.portfolio[tckr]
        stock.index = pd.to_datetime(stock.index)
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


    def plot_bollinger(self):
        counter = 0
        fig, axs = plt.subplots(nrows=5)
        for stock, data in self.portfolio.items():
            axs[counter].plot(data['close'], marker='o')
            axs[counter].plot(data['ma'])
            axs[counter].plot(data['Bollinger High'])
            axs[counter].plot(data['Bollinger Low'])
            axs[counter].xaxis.set_major_locator(plt.MaxNLocator(10))
            counter += 1
            if counter > 4:
                break
        plt.show()

if __name__=='__main__':
    dm = DataManager()
    data = dm.getOneSector(sector="Energy", fromDate="2015-01-01", toDate="2017-06-01")
    bb = BollingerBand(portfolio=data, params=7)
    bb.add_indicators()
    stock = data['APA']
    stock.index = pd.to_datetime(stock.index)
    bb.plot_indicators()
    # ap = [mpf.make_addplot(stock['Bollinger High'], color='b'), mpf.make_addplot(stock['Bollinger Low'], color='b'),
    #       mpf.make_addplot(stock['ma'], color='g'),
    #       mpf.make_addplot(stock['trend'], panel=1)]
    # mpf.plot(stock, type='candle', addplot=ap)

    plt.show()

    # bb.add_bollinger()
    # bb.add_indicators()
    # fig, axs = plt.subplots(2)
    
    # plt.plot()
    #bb.plot_bollinger()


