Welcome to Bollinger Bands with Pete!

In this project we used pre-saved historical data to backtest and analyze (both implemented in this project) bollinger band strategies. As a fun extra to the project we also implemented Monte Carlo Simulations to better validate the strategies

The files: \
\
Analyzer - This contains the analyzer. Running this prints out information about the backtest such as the total returns, and the biggest losing and winning trades. It also gives you the option to plot any individual symbol with the trades displayed on there. This allows for convenient analysing of the model as you can try to pinpoint where the trades are going wrong/right. \
\
BaseStrategy - This is a parent Strategy and is useless on its own. All new strategies should import from here. If a new strategy is to be created it should be a child of this and be structurally similar to *BollingBandInitial*. Note: The strategies need not be Bolling Band Related. Create the indicators in the *add_indicator* function, add the logic to the run function and you have an entirely new strategy. \
\
BBStopLoss - This is an extension of *BollingerBandInitial* which has a basic stop loss implemented. It is a good example of how simple it can be to edit models, compare this to *BollingerBandInitial* \
\
BBWithTrend - This was an extension of BBStopLoss which only bought stocks if the signal is in line with the short term trend. Spoiler Alert: It did not work. \
\
BollingerBandInitial - This is a create example of how to implement a strategy and if you wish to use this code to build different strategies I'd use this as a guideline. \
\
bringAllTogether - As soon as you look at this code I recommend opening and running this to get an idea of the outcome of the code (It will also likely hit you with a load of imports). Make sure you change the filepath. This will also allow you to see the key functions and classes within the code. \
\
MCAnalyze - This was a fun addition to the project. In order to better validate the model I created a monte carlo analysis tool. This runs slightly seperately to the analyzer so is not included in *bringAllTogether* but make sure to check it out, there is an example use at the bottom of the class \
\
utils - Just has some random useful functions in it, wouldn't worry too much about this. \
\
Any questions feel free to connect with me on linkedin at: www.linkedin.com/in/petermikhaeil or email me at petemikhaeil3@gmail.com
