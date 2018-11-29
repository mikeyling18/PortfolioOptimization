
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
API_KEY = 'GFTVBJ9OZBU5IXA1'

def get_prices(symbols, date_range, addMarket=True):
    # Get closing prices for all symbols
    all_prices = pd.DataFrame(index=date_range)
    if addMarket and 'SPY' not in symbols:
        symbols = ['SPY'] + symbols
    for sym in symbols:
        ts = TimeSeries(key=API_KEY, output_format='pandas')
        data, meta_data = ts.get_daily(symbol=sym, outputsize='full')
        data.index = pd.to_datetime(data.index)
        df = data.reindex(date_range)
        y = df['4. close'].to_frame(name=sym)
        all_prices = all_prices.join(y)
        all_prices.dropna(inplace=True)
    return all_prices

def get_portfolio_value(orders_file, start_val, commission):
    df = pd.read_csv(orders_file, parse_dates=False)            # create dataframe from the orders csv file
    df['Date'] = pd.to_datetime(df['Date'])                     # convert the Date column to datetime format
    symbols = df['Symbol'].unique().tolist()                    # get all the unique symbols in df and create a list
    dateRange = pd.date_range(min(df['Date']), max(df['Date']))     # get the starting and ending date of the orders csv file

    df_prices = get_prices(symbols, dateRange)                       # get prices of the symbols in orders csv file
    df_prices['Current Value'] = 1                                       # set the Current Value column to 1 for arbitrary place holder

    # Fill forwards, then fill back 
    df_prices.fillna(method = 'ffill')
    df_prices.fillna(method = 'bfill')

    df_trades = pd.DataFrame(index=df_prices.index, columns=df_prices.columns)
    df_trades.sort_index()
    df_trades[df_trades != 0] = 0
    df_trades.iloc[0]['Current Value'] = start_val

    for index, row in df.iterrows():

        num_shares = row['Shares']              # get the number of shares involved in the sell or buy
        share = row['Symbol']                   # get the symbol involved in the sell or buy
        date = row['Date']                      # get the date of the sell or buy order
        order_type = row['Order']               # get the order type ('BUY' or 'SELL')

        if order_type == 'SELL':
            price = df_prices.loc[date][share]
            # the number of shares of that company is decreased by the number of shares in the order
            df_trades.loc[date][share] = df_trades.loc[date][share] - num_shares
            # and the amount Current Value increases by the price * number of shares being sold
            df_trades.loc[date]['Current Value'] = df_trades.loc[date]['Current Value'] + (price * num_shares)
        elif order_type == 'BUY':
            price = df_prices.loc[date][share]
            df_trades.loc[date][share] = df_trades.loc[date][share] + num_shares
            df_trades.loc[date]['Current Value'] = df_trades.loc[date]['Current Value'] - (price * num_shares)
        # flat fee of $(commission) is applied to each order
        df_trades.loc[date]['Current Value'] -= commission

    values = df_trades.cumsum() * df_prices

    # get the sum of the columns to get the values data frame in the correct format
    return pd.DataFrame(values.sum(axis = 1))

def get_stats(portfolio_value):

    daily_ret = portfolio_value.copy()
    daily_ret[1:] = (daily_ret[1:] / daily_ret[:-1].values) - 1
    daily_ret = daily_ret[1:]

    # Get portfolio statistics (note: std_daily_ret = volatility)
    cr = (portfolio_value[-1] / portfolio_value[0]) - 1
    adr = daily_ret.mean()
    sddr = daily_ret.std()

    # calculate Sharpe Ratio
    sf = 252.0
    rfr = 0.0
    sr = pow(sf, .5) * (daily_ret - rfr).mean() / sddr

    return adr, sddr, sr, cr

if __name__ == "__main__":
    order_file = "orders.csv"
    starting_value = 2000000
    commission = 9.95

    # Process orders
    portfolio_value = get_portfolio_value(orders_file=order_file, start_val=starting_value, commission=commission)
    if isinstance(portfolio_value, pd.DataFrame):
        portfolio_value = portfolio_value[portfolio_value.columns[0]] # just get the first column
    else:
        "warning, code did not return a DataFrame"
    
    # Get portfolio stats
    average_daily_return, std_daily_return, sharpe_ratio, cumulative_return = get_stats(portfolio_value)

    # Compare portfolio against SPX
    print("Sharpe Ratio of Fund: {}".format(sharpe_ratio))
    print("Cumulative Return of Fund: {}".format(cumulative_return))
    print("Standard Deviation of Fund: {}".format(std_daily_return))
    print("Average Daily Return of Fund: {}".format(average_daily_return))
    print("Initial Portfolio Value: {}".format(starting_value))
    print("Final Portfolio Value: {}".format(portfolio_value[-1]))


