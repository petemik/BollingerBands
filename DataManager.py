import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import os.path
import matplotlib.pyplot as plt
import sys
import re
import time
import numpy as np
from statistics import mode
import random

class DataManager:
    def __init__(self):
        # Alpha vantage API KEY
        self.apikey = "HZ50R56073QJNJ2V"
        self.modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.plot = False
        self.SPList = None
        # List of the sectors wikipedia breaks the S&P into
        self.categoryList = {"Communication Services": 0, "Consumer Discretionary": 1, "Consumer Staples": 2,
                             "Energy": 3, "Financials": 4, "Health Care": 5, "Industrials": 6,
                             "Information Technology": 7, "Materials": 8, "Real Estate": 9, "Utilities": 10}
        self.data = None

    def convert_weekly(self, data):
        data['Date'] = pd.to_datetime(data.index)
        weekly = data
        weekly['Week Number'] = data['Date'].dt.week
        weekly['Year'] = data['Date'].dt.year
        weekly = weekly.groupby(['Year', 'Week Number']).agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last',
             'adjusted_close': 'last', 'volume': 'sum',
             'dividend_amount': 'sum', 'split_coefficient': 'max'})
        # Drop first and last as not sure if they are full weeks
        weekly.drop(weekly.tail(1).index, inplace=True)
        weekly.drop(weekly.head(1).index, inplace=True)
        return weekly


    def fetchSPList(self):
        """
        This function returns a dataframe of every company in the S&P500, its sector and its sector encoding determined
        by self.categoryList
        :return: Returns a df with every company in the S&P500, its sector and its sector encoding.
        """
        website_url = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies").text
        soup = BeautifulSoup(website_url, 'lxml')
        table = soup.find('table', {'class': "wikitable"})
        symbols = []
        sectors = []
        for items in table.find_all('tr')[1::1]:
            data = items.find_all(['th', 'td'])
            try:
                symbol = data[0].text.rstrip()
                sector = data[3].text.rstrip()
                symbols.append(symbol)
                sectors.append(sector)
            except:
                continue
        dict = {"symbols": symbols, "sectors": sectors}
        df = pd.DataFrame.from_dict(dict)
        df['sectors'] = df['sectors'].astype('category')
        df['sectorsEnc'] = df['sectors'].cat.codes
        self.SPList = df
        return df

    def fetch_intraday(self, tckr, frequency='15min',
                    slice='year1month1'):
        """

        :param tckr: The ticker of the company you want to fetch intraday data for
        :param frequency: the frequency of which you want to fetch the data for
        :param slice: The period of which you want to fetch the data for (see alphavtange docs)
        :return: a dataframe of the response from alphavtange will be OHLC for the stock
        """
        params = {'symbol': tckr, "function": "TIME_SERIES_INTRADAY_EXTENDED",
                  "interval": frequency, "slice": slice, "apikey": self.apikey}
        response = requests.get(url="https://www.alphavantage.co/query?", params=params)
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        if not df.shape[0]:
            print("It may be the case this ticker does not exist: {}".format(tckr))
            exit()
        return df

    def nMonthDataImport(self, tckr, n=6, frequency='15min', plot=False):
        """
        This uses fetch intraday to fetch the past n months of data
        :param tckr: Ticker/Symbol of the company you want to fetch
        :param n: How many months back you want to fetch
        :param frequency: The frequency of data you want to fetch
        :param plot: Option to plot the close values of the data
        :return: Empty but stores the data into self.data
        """
        data = self.fetch_intraday(tckr=tckr, frequency=frequency, slice="year1month1")
        for i in range(2, n + 1):
            slice = "year" + str(int(i > 12) + 1) + "month" + str(i % 12)
            new_month = self.fetch_intraday(tckr=tckr, frequency=frequency, slice=slice)
            # I think this is going to be the wrong way round
            data = data.append(new_month, ignore_index=True)
        # flip the data
        data = data.iloc[::-1].reset_index().drop(columns=['index'])
        self.data = data
        data.to_csv(self.modpath + "\Data\Stocks\\" + tckr + ".csv")
        if plot:
            plt.plot(data.index, data.close)
            plt.show()

    def fetchSP(self):
        """
        This functions fetches and saves tje full list of the S&P500 and saves them to a csv with the name
        [tckr][SectorEncodingn].csv
        :return: Empty but saves all the files to CSV
        """
        # The API limit is 5 calls in one minute or one every 12 seconds
        SPList = self.fetchSPList()
        # ShortList
        # SPList = SPList.head(2)

        # TODO: implement a check to see if the data has actually been recieved
        for row in SPList.itertuples(index=True, name='Pandas'):
            try:
                os.path.getsize(self.modpath + "\Data\S&P\\" + str(row.symbols) + str(row.sectorsEnc) + ".csv")
            except:
                print("Cannot find file: {}".format("\Data\S&P\\" + str(row.symbols) + str(row.sectorsEnc) + ".csv"))
                continue
            if os.path.getsize(self.modpath + "\Data\S&P\\" + str(row.symbols) + str(row.sectorsEnc) + ".csv") < 252:
                params = {'symbol': str(row.symbols), "function": "TIME_SERIES_DAILY_ADJUSTED",
                          "outputsize": 'full', "datatype": "csv", "apikey": self.apikey}
                try:
                    response = requests.get(url="https://www.alphavantage.co/query?", params=params)
                except:
                    print("Error with the API not sure why")
                    continue
                csv_data = StringIO(response.text)
                df = pd.read_csv(csv_data)
                df.to_csv(self.modpath + "\Data\S&P\\" + str(row.symbols) + str(row.sectorsEnc) + ".csv")
                print("Succesfully saved {}".format(row.symbols))
                time.sleep(12)
                if os.path.getsize(self.modpath + "\Data\S&P\\" + str(row.symbols) + str(row.sectorsEnc) + ".csv") < 252:
                    print("Did not Sucessfuly overwrite {}".format(row.symbols))
            else:
                print("Already have saved file for {}".format(row.symbols))

    def getOneSector(self, sector="Energy", fromDate="2015-01-01", toDate="2020-09-21", log=False, weekly=False):
        """
        This is the most used function of this class. It doesn't fetch from Alphavantage but from the saved files you get from fetchSP
        :param sector: The sector you want to fetch
        :param fromDate: The date you want to start fetching
        :param toDate: the date you want to end fetching
        :return: empty but saves the data to self.data as a dictionary in the format {[tckr]: data} for every ticker
        """
        sector_number = self.categoryList[sector]
        sector_dict = {}
        sector_dict['SP500'] = pd.read_csv(self.modpath + "\\..\\Data\\S&P\\SP.csv", index_col=1).iloc[::-1]
        sector_dict['SP500'] = sector_dict['SP500'].drop(sector_dict['SP500'].columns[0], axis=1)
        sector_dict['SP500'] = sector_dict['SP500'][fromDate:toDate]
        for filename in os.listdir(self.modpath + "\\..\\Data\\S&P"):
            if str(sector_number) in filename:
                try:
                    symbol = re.match(r"([a-z]+)([0-9]+)", filename, re.I).groups()[0]
                except:
                    print("Wtf is going on: {}".format(filename))
                    continue
                sector_dict[str(symbol)] = pd.read_csv(self.modpath + "\\..\\Data\\S&P" + "\\" + filename, index_col=1).iloc[::-1]
                sector_dict[str(symbol)] = sector_dict[str(symbol)].drop(sector_dict[str(symbol)].columns[0], axis=1)
                sector_dict[str(symbol)] = sector_dict[str(symbol)][fromDate:toDate]
                if weekly==True:
                    sector_dict[str(symbol)] = self.convert_weekly(sector_dict[str(symbol)])
                if log:
                    sector_dict[str(symbol)]['log_adjusted_close'] = np.log(sector_dict[str(symbol)]['adjusted_close'])

        self.data = sector_dict
        self.cleanse()
        return self.data





    def getAllSector(self, fromDate="2015-01-01", toDate="2020-09-21", limit=150, cleanse=False):
        """
        This is the most used function of this class. It doesn't fetch from Alphavantage but from the saved files you get from fetchSP
        :param sector: The sector you want to fetch
        :param fromDate: The date you want to start fetching
        :param toDate: the date you want to end fetching
        :return: empty but saves the data to self.data as a dictionary in the format {[tckr]: data} for every ticker
        """
        sector_dict = {}
        seed = 7
        random.seed(seed)
        sector_dict['SP500'] = pd.read_csv(self.modpath + "\Data\\S&P\\SP.csv", index_col=1).iloc[::-1]
        sector_dict['SP500'] = sector_dict['SP500'].drop(sector_dict['SP500'].columns[0], axis=1)
        sector_dict['SP500'] = sector_dict['SP500'][fromDate:toDate]
        files = os.listdir(self.modpath+"\Data\\S&P")
        count_files = len(files)
        counter = 0
        try:
            sample = random.sample(range(count_files), limit)
        except ValueError:
            sample = np.arange(0, count_files)
        for filename in os.listdir(self.modpath+"\Data\\S&P"):
            if counter in sample:
                try:
                    symbol = re.match(r"([a-z]+)([0-9]+)", filename, re.I).groups()[0]
                except:
                    print("Wtf is going on: {}".format(filename))
                    continue
                sector_dict[str(symbol)] = pd.read_csv(self.modpath + "\Data\\S&P" + "\\" + filename, index_col=1).iloc[::-1]
                sector_dict[str(symbol)] = sector_dict[str(symbol)].drop(sector_dict[str(symbol)].columns[0], axis=1)
                sector_dict[str(symbol)] = sector_dict[str(symbol)][fromDate:toDate]
            counter += 1
        self.data = sector_dict
        if cleanse:
            self.cleanse()

    def cleanse(self):
        """
        Cleans up the data to ensure they are all the same size, some synbols don't have full amount of data
        :return: The cleaned up data
        """
        size_array = []
        for symbol, dataframe in self.data.items():
            size_array.append(dataframe.shape[0])
        mode_size = mode(size_array)
        self.data = {k:v for k, v in self.data.items() if v.shape[0] == mode_size}
        return self.data

    def calcReturnsSingle(self, df):
        """
        Calculates the returns, percent returns and logReturns for  a single ticker
        :param df: the data you want to calculate the returns for
        :return: The dataframe with extra returns, pctReturns and logReturns Columns
        """
        df['returns'] = df['adjusted_close'].diff()
        df['pctReturns'] = df['adjusted_close'].pct_change()
        df['logReturns'] = np.log(1+df['pctReturns'])
        return df

    def calcReturns(self):
        """
        Does the above but for the entire dictionary.
        :return:
        """
        for key, value in self.data.items():
            self.data[key] = self.calcReturnsSingle(value)

    def fetch_fundamentals(self):
        params = {'symbol': "AAPL", "function": "OVERVIEW",
                   "apikey": self.apikey}
        try:
            response = requests.get(url="https://www.alphavantage.co/query?", params=params)
        except:
            print("It dang fucked up")

        print("debug")


if __name__ == "__main__":
    # This is just here as a tester
    x = DataManager()
    x.getAllSector(fromDate="2010-01-01", toDate="2020-09-21", cleanse=False, limit=500)
    new_dict = {}
    for symbol, data in x.data.items():
        new_dict[symbol] = np.mean(data['volume'])
    print(min(new_dict, key=new_dict.get))
    # x.fetch_fundamentals()
    # x.calcReturns()
    print("hi")
