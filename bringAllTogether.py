from BollingerBandInitial import InitialStrategy
from DataManager import DataManager
from Analyzer import Analyzer

if __name__ == '__main__':
    """
    This is a little example of bringing it all together
    """
    # sectors = ["Communication Services", "Consumer Discretionary", "Consumer Staples", "Energy", "Financials",
    #            "Health Care", "Industrials", "Information Technology", "Materials", "Real Estate", "Utilities"]
    # This line below should point to your data, inside the S&P file.
    path_to_data = 'C:\\Users\\petem\\Trading\\Data\\S&P\\'
    dm = DataManager(path_to_data=path_to_data)
    # This collects one sector from the S&P between the desired dates. See the commented for the options
    data = dm.get_one_sector_SP(sector="Energy", fromDate="2015-10-01", toDate="2017-10-01")
    ## keys_to_extract = ['CVX']
    ## data_subset = {key: data[key] for key in keys_to_extract}
    # This function prepares the data in the necessary way for the strategy to work.
    data = dm.prepare_data(data_dict=data)
    # data_subset = dm.prepare_data(data_dict=data_subset)
    # This initialises the strategy
    strat = InitialStrategy(data, params={})
    # Running the analyzer
    analyzer = Analyzer(strat)
    analyzer.analyze()
    # To see monte carlo analysis in action see MCAnalyze.py