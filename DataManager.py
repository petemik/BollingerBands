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
    def __init__(self, path_to_data=None):
        # Alpha vantage API KEY
        self.path_to_data = path_to_data
        # List of the sectors wikipedia breaks the S&P into
        self.categoryList = {"Communication Services": 0, "Consumer Discretionary": 1, "Consumer Staples": 2,
                             "Energy": 3, "Financials": 4, "Health Care": 5, "Industrials": 6,
                             "Information Technology": 7, "Materials": 8, "Real Estate": 9, "Utilities": 10}

    def _convert_weekly(self, df):
        df['Date'] = pd.to_datetime(df.index)
        weekly = df
        weekly['Week Number'] = df['Date'].dt.week
        weekly['Year'] = df['Date'].dt.year
        weekly = weekly.groupby(['Year', 'Week Number']).agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last',
             'adjusted_close': 'last', 'volume': 'sum',
             'dividend_amount': 'sum', 'split_coefficient': 'max'})
        # Drop first and last as not sure if they are full weeks
        weekly.drop(weekly.tail(1).index, inplace=True)
        weekly.drop(weekly.head(1).index, inplace=True)
        return weekly


    def get_one_sector_SP(self, sector="Energy", fromDate="2015-01-01", toDate="2020-09-21", weekly=False):
        """
        This is the most used function of this class. It doesn't fetch from Alphavantage but from the saved files you get from fetchSP
        :param sector: The sector you want to fetch
        :param fromDate: The date you want to start fetching
        :param toDate: the date you want to end fetching
        :return: empty but saves the data to self.data as a dictionary in the format {[tckr]: data} for every ticker
        """
        sector_number = self.categoryList[sector]
        sector_dict = {}
        for filename in os.listdir(self.path_to_data):
            if str(sector_number) in filename:
                try:
                    symbol = re.match(r"([a-z]+)([0-9]+)", filename, re.I).groups()[0]
                except:
                    print("Wtf is going on: {}".format(filename))
                    continue
                sector_dict[str(symbol)] = pd.read_csv(self.path_to_data + filename, index_col=1).iloc[::-1]
                sector_dict[str(symbol)] = sector_dict[str(symbol)].drop(sector_dict[str(symbol)].columns[0], axis=1)
                sector_dict[str(symbol)] = sector_dict[str(symbol)][fromDate:toDate]
                if weekly==True:
                    sector_dict[str(symbol)] = self._convert_weekly(sector_dict[str(symbol)])

        data_dict = sector_dict
        data_dict = self._remove_incomplete_data(data_dict)
        return data_dict

    def get_all_sector_SP(self, fromDate="2015-01-01", toDate="2020-09-21", limit=150, cleanse=True):
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
        files = os.listdir(self.path_to_data)
        count_files = len(files)
        counter = 0
        try:
            sample = random.sample(range(count_files), limit)
        except ValueError:
            sample = np.arange(0, count_files)
        for filename in os.listdir(self.path_to_data):
            if counter in sample:
                try:
                    symbol = re.match(r"([a-z]+)([0-9]+)", filename, re.I).groups()[0]
                except:
                    print("Wtf is going on: {}".format(filename))
                    continue
                sector_dict[str(symbol)] = pd.read_csv(self.path_to_data + filename, index_col=1).iloc[::-1]
                sector_dict[str(symbol)] = sector_dict[str(symbol)].drop(sector_dict[str(symbol)].columns[0], axis=1)
                sector_dict[str(symbol)] = sector_dict[str(symbol)][fromDate:toDate]
            counter += 1
        data_dict = sector_dict
        if cleanse:
            data_dict = self._remove_incomplete_data(data_dict)
        return data_dict

    def _remove_incomplete_data(self, data):
        """
        Cleans up the data to ensure they are all the same size, some symbols don't have full amount of data
        :return: The cleaned up data
        """
        size_array = []
        for symbol, dataframe in data.items():
            size_array.append(dataframe.shape[0])
        mode_size = mode(size_array)
        data = {k:v for k, v in data.items() if v.shape[0] == mode_size}
        return data

    def prepare_data(self, data_dict):
        """
        This needs to be general to all strategies. If I start fiddling with it then I need to change how it works
        """
        clean_data_dict = {}
        for symbol, df in data_dict.items():
            clean_data = df.dropna()
            if 'date' not in clean_data.columns:
                clean_data.index.name = 'date'
                clean_data.reset_index(inplace=True)
            clean_data.insert(loc=len(clean_data.columns), column='next_open', value=clean_data['open'].shift(-1))
            if df['split_coefficient'].max() != 1 or df['split_coefficient'].min() != 1:
                continue
            clean_data_dict[symbol] = clean_data
        return clean_data_dict




if __name__ == "__main__":
    # This is just here as a tester
    path_to_data = 'C:\\Users\\petem\\Trading\\Data\\S&P\\'
    x = DataManager(path_to_data)
    data = x.get_one_sector_SP(sector='Energy', fromDate="2010-01-01", toDate="2020-09-21")
