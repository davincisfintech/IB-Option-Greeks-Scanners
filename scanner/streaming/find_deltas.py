import math

import pandas as pd
from scipy.stats import norm

from scanner.settings import logger
from pprint import pprint
import time


class FindDeltas:
    def __init__(self, app, change_time_frame, change_days):
        self.app = app
        self.change_time_frame = change_time_frame
        self.change_days = change_days

    def run(self):
        found_deltas_for_each_expiry = list()
        try:
            if self.app.secContract_details_end:
                for ticker in self.app.secContract_details_end.copy():
                    expiries = sorted(self.app.contract_chain[ticker].keys()).copy()
                    for expiry in expiries:
                        try:
                            if not self.app.contract_chain[ticker][expiry]['streaming']:
                                continue
                            if f'{ticker} {expiry}' in found_deltas_for_each_expiry:
                                continue
                            found_deltas_for_each_expiry.append(f'{ticker} {expiry}')
                            for delta in self.app.deltas:
                                delta_call_strike_new = None
                                delta_put_strike_new = None
                                for right in ['C', 'P']:
                                    try:
                                        strikes = sorted(self.app.contract_chain[ticker][expiry][right].keys()).copy()
                                    except KeyError:
                                        continue
                                    if not strikes:
                                        continue
                                    min_diff = float('inf')
                                    if right == 'C':
                                        for strike in strikes:
                                            greek = self.app.contract_chain[ticker][expiry][right][strike]['greek']
                                            if greek['delta']:
                                                diff = abs(greek['delta'] - delta)
                                                if diff < min_diff:
                                                    min_diff = diff
                                                    delta_call_strike_new = strike
                                    if right == 'P':
                                        for strike in strikes:
                                            greek = self.app.contract_chain[ticker][expiry][right][strike]['greek']
                                            if greek['delta']:
                                                diff = abs(-greek['delta'] - delta)
                                                if diff < min_diff:
                                                    min_diff = diff
                                                    delta_put_strike_new = strike

                                if delta_call_strike_new != None and delta_put_strike_new != None:
                                    self.get_opt_open_close(f'{ticker} {expiry} {delta} C {delta_call_strike_new}')
                                    while f'{ticker} {expiry} {delta} C {delta_call_strike_new}' not in self.app.local_symbol_to_open_close_iv:
                                        pass

                                    self.get_opt_open_close(f'{ticker} {expiry} {delta} P {delta_put_strike_new}')
                                    while f'{ticker} {expiry} {delta} P {delta_put_strike_new}' not in self.app.local_symbol_to_open_close_iv:
                                        pass

                                    delta_call_strike_old = self.app.contract_chain_deltas.get(ticker, {}).get(expiry,
                                                                                                               {}).get(
                                        delta, {}).get('C', {})
                                    # Stop streaming in old call-delta and remove
                                    if isinstance(delta_call_strike_old, dict) and len(delta_call_strike_old):
                                        delta_call_strike_old = list(delta_call_strike_old.keys())[0]
                                        if delta_call_strike_new != delta_call_strike_old:
                                            symbol_incative = f'{ticker} {expiry} {delta} C {delta_call_strike_old}'
                                            self.app.stream_deltas_ids.remove(symbol_incative)
                                            self.app.stop_streaming(self.app.symbol_to_id[symbol_incative])
                                    
                                    # Stop streaming in old put-delta and remove
                                    delta_put_strike_old = self.app.contract_chain_deltas.get(ticker, {}).get(expiry,
                                                                                                              {}).get(
                                        delta, {}).get('P', {})
                                    if isinstance(delta_put_strike_old, dict) and len(delta_put_strike_old):
                                        delta_put_strike_old = list(delta_put_strike_old.keys())[0]
                                        if delta_put_strike_new != delta_put_strike_old:
                                            symbol_incative = f'{ticker} {expiry} {delta} P {delta_put_strike_old}'
                                            self.app.stream_deltas_ids.remove(symbol_incative)
                                            self.app.stop_streaming(self.app.symbol_to_id[symbol_incative])
                                            id = self.app.symbol_to_id[symbol_incative]
                                    
                                    # create delta chain if it is not created yet
                                    if ticker not in self.app.contract_chain_deltas:
                                        self.app.contract_chain_deltas[ticker] = {}

                                    if expiry not in self.app.contract_chain_deltas[ticker]:
                                        self.app.contract_chain_deltas[ticker][expiry] = {}

                                    if delta not in self.app.contract_chain_deltas[ticker][expiry]:
                                        self.app.contract_chain_deltas[ticker][expiry][delta] = {}

                                    for right in ['C', 'P']:
                                        if right not in self.app.contract_chain_deltas[ticker][expiry][delta]:
                                            self.app.contract_chain_deltas[ticker][expiry][delta][right] = {}
        
                                    """
                                    update streaming value either it is first time or 
                                    new closest delta strike has found
                                    """
                                    if (delta_call_strike_old is None) or \
                                            (delta_call_strike_new != delta_call_strike_old):
                                        self.app.contract_chain_deltas[ticker][expiry][delta]['C'] = {}
                                        self.app.contract_chain_deltas[ticker][expiry][delta]['C'][
                                            delta_call_strike_new] = \
                                            self.app.contract_chain[ticker][expiry]['C'][delta_call_strike_new]

                                    if (delta_put_strike_old is None) or \
                                            (delta_put_strike_new != delta_put_strike_old):
                                        self.app.contract_chain_deltas[ticker][expiry][delta]['P'] = {}
                                        self.app.contract_chain_deltas[ticker][expiry][delta]['P'][
                                            delta_put_strike_new] = \
                                            self.app.contract_chain[ticker][expiry]['P'][delta_put_strike_new]

                        except KeyError:
                            continue

        except Exception as e:
            logger.exception(e)
            return

    def get_opt_open_close(self, local_symbol):
        if local_symbol in self.app.local_symbol_to_open_close_iv:
            return
        self.app.local_symbol_to_open_close_iv[local_symbol] = {}
        
        # Extract local_symbol
        try:
            local_symbol = local_symbol.split()
            if len(local_symbol) == 9 and local_symbol[1] == 'STK':
                ticker = ' '.join(local_symbol[:5])
                expiry, delta, right, strike = local_symbol[-4], local_symbol[-3], local_symbol[-2], local_symbol[-1]
            elif len(local_symbol) == 10 and local_symbol[1] == 'FUT':
                ticker = ' '.join(local_symbol[:6])
                expiry, delta, right, strike = local_symbol[-4], local_symbol[-3], local_symbol[-2], local_symbol[-1]
            self.app.nextorderId += 1
            strike = float(strike)
            delta = float(delta)
        except IndexError as e:
            logger.debug(f"IndexError: {e} was raised. 'local_symbol' may not have enough elements.")
            return
        
        # Extract ticker
        try:
            if len(ticker.split()) == 6:  # FUT
                _symbol, _sec_type, _exch, _curr, _multiplier, _expiry_date = ticker.split()
            elif len(ticker.split()) == 5:  # STK
                _symbol, _sec_type, _exch, _curr, _multiplier = ticker.split()
        except ValueError as ve:
            logger.debug(f"ValueError: the number of components in the ticker is unexpected")
            return 
        except Exception as e:
            logger.debug(e)
            return

        if _sec_type == 'STK':
            _sec_type = 'OPT'
        elif _sec_type == 'FUT':
            _sec_type = 'FOP'

        # Contract Build & Send Request
        contract = self.app.my_contract(
            f'{_symbol} {_sec_type} {_exch} {_curr} {_multiplier} {expiry} {strike} {right}')

        # RequestSent-> Option HistData 
        reqId = self.app.nextorderId
        self.app.reqHistoricalData(reqId=reqId,
                                   contract=contract,
                                   endDateTime='',
                                   durationStr='14 D',
                                   barSizeSetting=self.change_time_frame if self.change_time_frame != '1 day' else '8 hours',
                                   whatToShow='TRADES',
                                   useRTH=1,
                                   formatDate=1,
                                   keepUpToDate=1,
                                   chartOptions=[])
        
        # Waiting till option histData is being fetched
        time_out,start_time=20,time.time()
        while reqId not in self.app.histData_end:
            if time.time() - start_time > time_out:
                    logger.debug(f'Error: Time out for option hsitData of : {_symbol}-{expiry}-{strike}-{right}')
                    return 
            pass
        if reqId not in self.app.histData:
                logger.debug(f'Error: no histData in app.histData for {reqId}: {_symbol}-{expiry}-{strike}-{right}')
                return
        df = pd.DataFrame(self.app.histData.get(reqId))
        
        if self.change_time_frame == '1 day':  # FOP historical data is not available in day time frame ,that's why resampling it
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
            df = df.resample('D').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
            df = df.dropna(subset=['Open', 'Close','Volume'])
            

        local_symbol = ' '.join(local_symbol)
        if local_symbol not in self.app.local_symbol_to_open_close_iv:
            logger.debug(f'{local_symbol} not found  in app.local_symbol_to_open_close_iv')
            return
        
        # open
        try:
            self.app.local_symbol_to_open_close_iv[local_symbol]['open'] = df['Open'].iloc[-1]
        except (IndexError,Exception) as e:
            self.app.local_symbol_to_open_close_iv[local_symbol]['open']=0
            logger.debug(f'{local_symbol} Open column out of range or not found {e}')
            
        # close
        try:
            self.app.local_symbol_to_open_close_iv[local_symbol]['close'] = df['Close'].iloc[-2]
        except (IndexError,Exception) as e:
            self.app.local_symbol_to_open_close_iv[local_symbol]['close']=0      
            logger.debug(f'{local_symbol} Close column out of range or not found! {e}')
        
            
        # vol_14_avg
        try:
            self.app.local_symbol_to_open_close_iv[local_symbol]['vol_14_avg'] = df.tail(14)['Volume'].mean() 
        except Exception as e:
            self.app.local_symbol_to_open_close_iv[local_symbol]['vol_14_avg']=0
            logger.debug(f'{local_symbol} unknown error  : {e}!')
        
        # hist_iv
        implied_volatility_14_days_hist = self.calculate_implied_volatility(option_price=list(df['Close'])[0],
                                                                            underlying_price=self.app.ltp[ticker],
                                                                            strike_price=strike,
                                                                            risk_free_rate=0.05,
                                                                            time_to_maturity=float(
                                                                                self.change_days / 365))
        try:
            self.app.local_symbol_to_open_close_iv[local_symbol]['hist_iv'] = round(implied_volatility_14_days_hist, 4)
        except Exception as e:
            self.app.local_symbol_to_open_close_iv[local_symbol]['hist_iv']=0
            logger.exception(f'Unknow exception: {e}')
            

        # todays_iv(Open)
        implied_volatility_today_open = self.calculate_implied_volatility(option_price=df['Open'].iloc[-1],
                                                                          underlying_price=self.app.ltp[ticker],
                                                                          strike_price=strike,
                                                                          risk_free_rate=0.05,
                                                                          time_to_maturity=float(0.5 / 365))
        try:
            self.app.local_symbol_to_open_close_iv[local_symbol]['todays_iv'] = round(implied_volatility_today_open, 4)
        except Exception as e:
            self.app.local_symbol_to_open_close_iv[local_symbol]['todays_iv']=0
            logger.exception(f'Unknow exception: {e}')
        
        # avg_iv_14
        avg_iv = 0
        days_to_expriration = 14
        for i, row in df.tail(14).iterrows():
            close = row['Close']
            iv = self.calculate_implied_volatility(option_price=close,
                                                   underlying_price=self.app.ltp[ticker],
                                                   strike_price=strike,
                                                   risk_free_rate=0.04,
                                                   time_to_maturity=float(days_to_expriration / 365))
            days_to_expriration -= 1
            if isinstance(iv,(float,int)):
                avg_iv += iv
                
        if avg_iv!=0:
                avg_iv = avg_iv / 14
                self.app.local_symbol_to_open_close_iv[local_symbol]['avg_iv_14'] = round(avg_iv, 4)
        else:
            self.app.local_symbol_to_open_close_iv[local_symbol]['avg_iv_14']=0
            logger.debug(f'Failed to calculate avg_iv_14 (14 days average) for :{local_symbol}')
        
        # Final Varifications To Prevent None values to be stored
        for key in ['Open','close','vol_14_avg','hist_iv','todays_iv','avg_iv_14']:
            value=self.app.local_symbol_to_open_close_iv[key]
            if not isinstance(value,(float,int)):
                self.app.local_symbol_to_open_close_iv[key]=0
                
            
            

    def calculate_implied_volatility(self, option_price, underlying_price, strike_price, risk_free_rate,
                                     time_to_maturity):
        try:
            # Define the Black-Scholes formula for calculating the option price
            def black_scholes_call_price(volatility):
                d1 = (math.log(underlying_price / strike_price) + (
                            risk_free_rate + (volatility ** 2) / 2) * time_to_maturity) / (
                                 volatility * math.sqrt(time_to_maturity))
                d2 = (math.log(underlying_price / strike_price) + (
                            risk_free_rate - (volatility ** 2) / 2) * time_to_maturity) / (
                                 volatility * math.sqrt(time_to_maturity))
                # d2 = d1 - volatility * math.sqrt(time_to_maturity)
                return underlying_price * norm.cdf(d1) - strike_price * math.exp(
                    -risk_free_rate * time_to_maturity) * norm.cdf(d2)

            # Define the derivative of the Black-Scholes formula with respect to volatility
            def black_scholes_vega(volatility):
                d1 = (math.log(underlying_price / strike_price) + (
                            risk_free_rate + (volatility ** 2) / 2) * time_to_maturity) / (
                                 volatility * math.sqrt(time_to_maturity))
                return underlying_price * norm.pdf(d1) * math.sqrt(time_to_maturity)

            # Implement the Newton-Raphson method to solve for implied volatility
            def newton_raphson_method(target_price):
                max_iterations = 100
                tolerance = 0.09
                initial_guess = 0.5
                volatility = initial_guess

                for _ in range(max_iterations):
                    price = black_scholes_call_price(volatility)
                    vega = black_scholes_vega(volatility)
                    if vega == 0 or vega <= 2:
                        return volatility

                    # Update the volatility estimate
                    volatility -= (price - target_price) / vega

                    # Check for convergence
                    if abs(price - target_price) < tolerance:
                        return volatility

                return 0.10  # remove None   # If convergence is not achieved within the maximum iterations

            # Calculate the implied volatility
            implied_volatility = newton_raphson_method(option_price)
            return implied_volatility

        except (ValueError, ZeroDivisionError) as error:
            # Handle specific exceptions and continue execution
            logger.info("An error occurred in  function calculate_implied_volatility:", error)
            return None

        except Exception as error:
            # Handle any other exceptions and continue execution
            logger.info("An unexpected error occurred in function calculate_implied_volatility:", error)
            return None
