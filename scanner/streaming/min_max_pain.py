import pandas as pd


class MinMaxPain:
    def __init__(self, app):
        self.app = app

    def total_loss_at_strike(self, chain, expiry_price):
        # Calculate loss at strike price
        # All call options with strike price below the expiry price will result in loss for option writers
        in_money_calls = chain[chain['Strike Price'] < expiry_price][["CE OI", "Strike Price"]]
        in_money_calls["CE loss"] = (expiry_price - in_money_calls['Strike Price']) * in_money_calls["CE OI"]

        # All put options with strike price above the expiry price will result in loss for option writers
        in_money_puts = chain[chain['Strike Price'] > expiry_price][["PE OI", "Strike Price"]]
        in_money_puts["PE loss"] = (in_money_puts['Strike Price'] - expiry_price) * in_money_puts["PE OI"]
        total_loss = in_money_calls["CE loss"].sum() + in_money_puts["PE loss"].sum()

        return total_loss

    def run(self):
        if not self.app.secContract_details_end:
            return
        for ticker in self.app.secContract_details_end:
            expiries = sorted(self.app.contract_chain.get(ticker, None).keys()).copy()
            if not isinstance(expiries, list):
                continue

            for expiry in expiries:
                if not self.app.contract_chain[ticker][expiry]['streaming']: continue
                call_OI = list()
                put_OI = list()
                strike_price = list()
                for right in ['C', ]:
                    strikes = sorted(self.app.contract_chain[ticker][expiry][right].keys()).copy()
                    if not isinstance(strikes, list):
                        continue
                    for strike in strikes:
                        call_OI_value = self.app.contract_chain.get(ticker, None).get(expiry, None).get('C', None).get(
                            strike, None).get('greek', None).get('OI', None)
                        put_OI_value = self.app.contract_chain.get(ticker, None).get(expiry, None).get('P', None).get(
                            strike, None).get('greek', None).get('OI', None)
                        call_gamma = self.app.contract_chain.get(ticker, None).get(expiry, None).get('C', None).get(
                            strike, None).get('greek', None).get('gamma', None)
                        put_gamma = self.app.contract_chain.get(ticker, None).get(expiry, None).get('P', None).get(
                            strike, None).get('greek', None).get('gamma', None)

                        if call_OI_value and put_OI_value and \
                                call_gamma and put_gamma:
                            call_OI.append(call_OI_value)
                            put_OI.append(put_OI_value)
                            strike_price.append(strike)

                            # gamma_exposure Calculation 
                            self.app.contract_chain[ticker][expiry]['C'][strike]['greek']['gamma_exposure'] = int(
                                (call_gamma * 100 * call_OI_value * self.app.ltp[ticker] * 0.01) / 1000000)
                            self.app.contract_chain[ticker][expiry]['P'][strike]['greek']['gamma_exposure'] = int(
                                ((-1) * (put_gamma * 100 * put_OI_value * self.app.ltp[ticker] * 0.01)) / 1000000)

                            if self.app.contract_chain[ticker][expiry]['C'][strike]['greek']['gamma_exposure'] and \
                                    self.app.contract_chain[ticker][expiry]['P'][strike]['greek']['gamma_exposure']:
                                if f'{ticker} {expiry}' not in self.app.gamma_exp:
                                    self.app.gamma_exp[f'{ticker} {expiry}'] = {'strikes': list(),
                                                                                'call_gamma_exp': list(),
                                                                                'put_gamma_exp': list()
                                                                                }
                                if strike not in self.app.gamma_exp[f'{ticker} {expiry}']['strikes']:
                                    self.app.gamma_exp[f'{ticker} {expiry}']['strikes'].append(strike)
                                    self.app.gamma_exp[f'{ticker} {expiry}']['call_gamma_exp'].append(
                                        self.app.contract_chain[ticker][expiry]['C'][strike]['greek']['gamma_exposure'])
                                    self.app.gamma_exp[f'{ticker} {expiry}']['put_gamma_exp'].append(
                                        self.app.contract_chain[ticker][expiry]['P'][strike]['greek']['gamma_exposure'])

                chain = pd.DataFrame()
                chain['Strike Price'] = strike_price
                chain['CE OI'] = call_OI
                chain['PE OI'] = put_OI

                strikes = list(chain['Strike Price'])
                losses = [self.total_loss_at_strike(chain, strike) for strike in strikes]
                if losses:
                    minn = losses.index(min(losses))
                    self.app.max_pain[f'{ticker}-{expiry}'] = strikes[minn]

                    maxx = losses.index(max(losses))
                    self.app.min_pain[f'{ticker}-{expiry}'] = strikes[maxx]

                    self.app.OI_resistance[f'{ticker}-{expiry}'] = strikes[call_OI.index(max(call_OI))]
                    self.app.OI_support[f'{ticker}-{expiry}'] = strikes[put_OI.index(max(put_OI))]
