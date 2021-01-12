from DataManager import DataManager
import numpy as np
import pandas as pd
from BBStopLoss import BBStopLoss
from Analyzer import Analyzer
import matplotlib.pyplot as plt


class MCAnalyze:
    """
    This class is used to for Monte Carlo Analysis of the strategy.
    Returning a confidence value for the strategies success

    The idea of Monte Carlo analysis is to observe the "what-if" cases of the portfolio.
    Answering the question, did we just get lucky that in our reality the strategy just happens to have worked for the
    data, or is it picking up something fundamental?

    In order to answer this question it generates n randomised portfolio with the same underlying properties as the
    original portfolio (same drift and standard deviation). It then tests the strategy on these portfolios and compares
    it to the true returns on the real data. If the strategy performs no better on the real data than the randomised
    data, we know it is picking up no fundamental market behaviours. It has just got lucky with the data we have put
    into it over the time frame. We would expect this strategy to perform poorly on real data
    """
    def __init__(self, strat, data, params):
        """
        This class needs the strategy as a class i.e. just as BBStopLoss not as BBStopLoss(data, params).
        Also requires prepared data and paramaters for the strategy as a dict
        """
        self.portfolio = data
        self.strat = strat
        self.params = params
        self.real_strat = strat(self.portfolio, self.params)
        self.real_returns = Analyzer(self.real_strat).get_returns()

    def _generate_random_portfolio(self, portfolio):
        """
        This generates a "what-if" portfolio similar to that of the input portfolio but where at every timestep the
        returns are randomised within paramaters set by the initial data.
        I.e it the randomised data will have the same std and drift as the original.
        This is used in monte carlo analysis
        """
        mc_portfolio = {}
        for tckr, data in portfolio.items():
            # The code below just creates this "what-if" portfolio. Based off this article
            # https://www.quantnews.com/introduction-monte-carlo-simulation/
            log_returns = np.log(1+data['close'].pct_change())
            close_open_diff_std = np.nanstd((data['close'].values - data['open'].values) / data['close'].values)
            u = log_returns.mean()
            var = log_returns.var()
            drift = u - (0.5 * var)
            std = log_returns.std()
            days = len(data)
            daily_returns = np.exp(drift + std * np.random.normal(loc=0, scale=1, size=days))
            c0 = data['close'].iloc[0]
            o0 = data['open'].iloc[0]
            close_prices = np.zeros(days)
            close_prices[0] = c0
            for d in range(1, days):
                close_prices[d] = close_prices[d - 1] * daily_returns[d]
            open_prices = close_prices[:-1] * (1 + np.random.normal(loc=0, scale=close_open_diff_std, size=days-1))
            open_prices = np.concatenate((np.array([o0]), open_prices))
            # This needs work as currently fills in with real values if no ability to make up yet
            df = pd.DataFrame({'date': data['date'], 'open': open_prices, 'close': close_prices,
                               'high': data['high'], 'low': data['low'], 'volume': data['volume'],
                               'split_coefficient': data['split_coefficient']})
            mc_portfolio[tckr] = df
        return mc_portfolio

    def run_MC(self, iterations=50):
        """
        This runs the actual monte carlo simulation for the desired number of iterations
        """
        # Number of times the true result beats the randomised data
        success = 0
        # plt.title("Monte Carlo Plot")
        # plt.ylabel("Close Price")
        # plt.xlabel("Days")
        # plt.plot(self.portfolio['APA']['close'].values, linewidth=5, label="Real Data", zorder=100)
        for i in range(0, iterations):
            # Generate Fake Data
            temp_portfolio = self._generate_random_portfolio(self.portfolio)
            # Prepare Fake Data
            fake_data = dm.prepare_data(temp_portfolio)
            plt.plot(fake_data['APA']['close'].values)
            # Run the Strategy on Fake Data
            strat = self.strat(fake_data, params={'stop_loss_perc': 1})
            # Get Returns on Fake Data
            analyzer = Analyzer(strat)
            fake_returns = analyzer.get_returns()
            # Compare Fake returns to real returns
            if fake_returns <= self.real_returns:
                success += 1
            print("Iteration {}/{}".format(i+1, iterations))
        # plt.legend()
        # plt.show()
        print("This strategy beats random {}% of the time".format(100 * (success) / iterations))



if __name__=='__main__':
    # Example of how to use the MC Simulation
    path_to_data = 'C:\\Users\\petem\\Trading\\Data\\S&P\\'
    dm = DataManager(path_to_data=path_to_data)
    sectors = ["Communication Services", "Consumer Discretionary", "Consumer Staples", "Energy", "Financials",
               "Health Care", "Industrials", "Information Technology", "Materials", "Real Estate", "Utilities"]
    data = dm.get_one_sector_SP(sector=sectors[3], fromDate="2015-06-01", toDate="2018-01-01")
    data = dm.prepare_data(data_dict=data)
    params = {'stop_loss_perc': 1}
    mc = MCAnalyze(BBStopLoss, data, params)
    mc.run_MC(50)