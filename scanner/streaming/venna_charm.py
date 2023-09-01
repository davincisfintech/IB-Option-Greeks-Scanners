import math
from datetime import datetime

import numpy as np
from scipy.stats import norm


class VennaCharm:
    def __init__(self, app, ticker, expiry, right, strike):
        self.app = app
        self.ticker = ticker
        self.expiry = expiry
        self.right = right
        self.strike = strike
        self.hist_df = dict()
        self.right = right
        self.type_of_right = {'C': 1, 'P': -1}
        self.T = self.calculate_time_to_expiry(expiry)  # Time To expiry
        if self.T == 0: self.T = 1  # To prevent zero divison error for todays expiry contract
        self.sigma = self.annual_volatility(self.ticker)  # Annual Volatility
        self.Type = self.type_of_right[right]  # 1 for a Call, - 1 for a put
        self.S = float(list(self.hist_df[self.ticker]['Close'])[-1])  # LTP of underlying security
        self.K = float(strike)  # Option strike
        self.r = 0.03  # Risk free intrest rate
        self.sigmaT = self.sigma * self.T ** 0.5  # sigma*T for reusability
        self.d1 = (math.log(self.S / self.K) + \
                   (self.r + 0.5 * (self.sigma ** 2)) \
                   * self.T) / self.sigmaT
        self.d2 = self.d1 - self.sigmaT
        if (self.ticker not in self.app.annual_vol) or \
                (self.ticker not in self.hist_df):
            return None

    def run(self):
        # Charm
        charm = self.calculate_charm()
        if charm:
            self.app.charm[f'{self.ticker} {self.expiry} {self.right} {self.strike}'] = round(charm, 4)
        vanna = self.calculate_vanna()
        if vanna:
            self.app.vanna[f'{self.ticker} {self.expiry} {self.right} {self.strike}'] = vanna

    # Annual Volatility of ticker
    def annual_volatility(self, ticker):
        df = self.app.ticker_to_stkHist[self.ticker]
        self.hist_df[ticker] = df
        returns = np.diff(df['Close']) / df['Close'][:-1]
        volatility = np.std(returns) * np.sqrt(252)
        self.app.annual_vol[ticker] = volatility
        return float(volatility)

    def calculate_time_to_expiry(self, expiration_date_str):
        # Convert date strings to datetime objects
        current_date = datetime.now().strftime("%Y%m%d")
        current_date = datetime.strptime(current_date, "%Y%m%d")
        expiration_date = datetime.strptime(expiration_date_str, "%Y%m%d")
        time_to_expiry = expiration_date - current_date
        days_to_expiry = time_to_expiry.days
        time_to_expiry_years = days_to_expiry / 365.0
        return float(time_to_expiry_years)

    def calculate_charm(self):
        dfq = math.e ** (-self.T)
        if self.Type == 1:
            return (1.0 / 365.0) * -dfq * (norm.pdf(self.d1) * ((self.r) / (self.sigmaT) - self.d2 / (2 * self.T)) \
                                           * norm.cdf(self.d1))
        else:
            return (1.0 / 365.0) * -dfq * (norm.pdf(self.d1) * ((self.r) / (self.sigmaT) - self.d2 / (2 * self.T)) \
                                           * norm.cdf(-self.d1))

    def calculate_vanna(self):
        return 0.01 * -math.e ** (-self.T) * self.d2 / self.sigma * norm.pdf(self.d1)
