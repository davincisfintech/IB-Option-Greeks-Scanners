import time

import pandas as pd


class IvBetaCalculation:
    def __init__(self, app, tickers, iv_args):
        self.app = app
        self.tickers = tickers
        self.iv_args = iv_args
        self.what_to_show_list = ['OPTION_IMPLIED_VOLATILITY', 'HISTORICAL_VOLATILITY', 'TRADES']

    def get_ivs(self):
        self.app.nextorderId += 1
        for ticker in self.tickers:
            for whatToShow in self.what_to_show_list:
                df = self.get_historical_data(ticker, whatToShow)
                if whatToShow == 'OPTION_IMPLIED_VOLATILITY':
                    a, b = self.iv_args.split()
                    iv = (float(df[a].iloc[-1]) + float(df[b].iloc[-1])) / 2
                    self.app.stocksIv[ticker] = round(iv, 4)
                elif whatToShow == 'HISTORICAL_VOLATILITY':
                    hv = float(df['Wap'].iloc[-1])
                    self.app.stocks_hist_iv[ticker] = hv

                else:
                    self.app.ticker_to_stkHist[ticker] = df

    def calculate_beta(self):
        for ticker in self.tickers:
            ticker_df = self.app.ticker_to_stkHist[
                ticker] if ticker in self.app.ticker_to_stkHist else self.get_historical_data(ticker, 'TRADES')
            market_df = self.get_historical_data('SPY STK SMART USD 100', 'TRADES')

            ticker_prices = ticker_df['Close']
            market_prices = market_df['Close']

            ticker_returns = ticker_prices.pct_change().dropna()
            market_returns = market_prices.pct_change().dropna()

            covariance = ticker_returns.cov(market_returns)
            market_variance = market_returns.var()

            beta_ticker = covariance / market_variance
            self.app.ticker_to_beta[ticker] = beta_ticker

    def get_historical_data(self, ticker, whatToShow):
        self.app.nextorderId += 1
        contract = self.app.my_contract(ticker)
        reqId = self.app.nextorderId
        self.app.reqHistoricalData(reqId=reqId,
                                   contract=contract,
                                   endDateTime='',
                                   durationStr='1 Y',
                                   barSizeSetting='1 day',
                                   whatToShow=whatToShow,
                                   useRTH=1,
                                   formatDate=1,
                                   keepUpToDate=0,
                                   chartOptions=[])
        self.app.nextorderId += 1

        while reqId not in self.app.histData_end:
            time.sleep(1)
            pass
        df = pd.DataFrame(self.app.histData.get(reqId))
        if df is None:
            return
        df.set_index("Date", inplace=True)

        return df
