'''
This simple script minimizes the volatility for a given portfolio and determines the optimal 
proportions your principle investment should be distributed. The script was created using methods 
featured in *Python for Finance* by Yves Hilpisch

The script uses scipy to minimize the volatility in a portfolio, where volatility is defined as the
standard deviation of the daily price change. It's recommended to use this script to analyze lower-
volatilty stocks as highly-volatile stocks are very unpredictable. 
'''


from alpha_vantage.timeseries import TimeSeries
import matplotlib.pyplot as plt
from scipy import optimize as spo
import pandas as pd
import numpy as np
import datetime as dt
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
# API_KEY = 'you can get your own API KEY by creating a free account at Alpha Vantage's website'


def get_prices(symbols, date_range, addMarket=True):
    # Get closing prices for all symbols
    all_prices = pd.DataFrame(index=date_range)
    if addMarket and 'SPY' not in symbols:
        symbols = ['SPY'] + symbols
    z = list()
    for sym in symbols:
        ts = TimeSeries(key=API_KEY, output_format='pandas')
        data, meta_data = ts.get_daily(symbol=sym, outputsize='full')
        data.index = pd.to_datetime(data.index)
        df = data.loc[date_range]
        y = df['4. close'].to_frame(name=sym)
        all_prices = all_prices.join(y)
        all_prices.dropna(inplace=True)
    return all_prices


def optimize_porfolio(date_range, symbols, visualize):
    # define the constraint function for scipy optimizer
    def constraint(allocations):
        c = np.sum(allocations) - 1
        return c

    # define the function that minimizes the volatility
    def get_volatility(allocations):
        # normed_prices = all_prices / all_prices.ix[0, :]
        alloc_prices = normed_prices * allocations
        daily_ret = alloc_prices.sum(axis=1)
        daily_ret[1:] = (daily_ret[1:] / daily_ret[:-1].values) - 1
        daily_ret = daily_ret[1:]
        volatility = daily_ret.std() #same as standard deviation
        return volatility

    all_prices = get_prices(symbols, date_range)
    market_prices = all_prices['SPY']/all_prices['SPY'].ix[0,:]
    all_prices = all_prices[symbols]
    num_syms = len(symbols)
    initial_alloc_guess = [1.0 / num_syms] * num_syms
    b = ((0.0, 1.0),) * num_syms
    c = ({'type': 'eq', 'fun': constraint})
    normed_prices = all_prices/all_prices.ix[0, :]
    allocs_opto = spo.minimize(get_volatility, initial_alloc_guess, method='SLSQP', bounds=b, constraints=c, options = {'disp': True})

    # Get daily portfolio values

    alloc_prices = normed_prices * allocs_opto.x
    port_val = alloc_prices.sum(axis=1)

    print(allocs_opto.x)
    # Compare daily portfolio value with SPY using a normalized plot
    if visualize:
        s = str(symbols)
        for r in (('\'', ''), ('[', ''), (']', '')):
            s = s.replace(*r)
        df_temp = pd.concat([port_val, market_prices], keys=['Portfolio: ' + s, 'SPY'], axis=1)
        df_temp.plot()
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.title('Daily Portfolio Value and SPY')
        plt.show()
        pass


if __name__ == '__main__':
    symbols = ['AMZN', 'AAPL', 'GLD']
    start_date = dt.datetime(2008, 6, 1)
    end_date = dt.datetime(2010, 6, 1)
    visualize = True
    date_range = pd.date_range(start_date, end_date)
    optimize_porfolio(date_range, symbols, make_plot)
