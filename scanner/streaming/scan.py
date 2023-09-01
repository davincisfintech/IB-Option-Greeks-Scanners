import time
from datetime import datetime

from scanner.settings import TZ
from scanner.websocket.main import manager


class Scan:
    def __init__(self, app, avg_ivs):
        self.app = app
        self.test = 0

    def run(self):
        if self.app.secContract_details_end.copy():
            printDictList = []
            try:
                for ticker in self.app.tickers:
                    try:
                        expiries = sorted(self.app.contract_chain_deltas[ticker].keys())
                    except:
                        continue
                    for expiry in expiries:
                        for delta in self.app.deltas:
                            # call-strike
                            call_strike = self.app.contract_chain_deltas.get(ticker, None).get(expiry, None).get(delta,None).get('C', None)
                            if call_strike == None:
                                continue
                            call_strike = list(call_strike.keys())[0]
                            
                            # put-strike
                            put_strike = self.app.contract_chain_deltas.get(ticker, None).get(expiry, None).get(delta,None).get('P', None)
                            if put_strike == None:
                                continue
                            put_strike = list(put_strike.keys())[0]
                            # call-greek
                            call_greek = self.app.contract_chain_deltas.get(ticker, None).get(expiry, None).get(delta,None).get('C', None).get(call_strike, None).get('greek', None)
                            put_greek = self.app.contract_chain_deltas.get(ticker, None).get(expiry, None).get(delta,None).get('P', None).get(put_strike, None).get('greek', None)
                            
                            if call_greek is None or put_greek is None:
                                continue
                            
                            call_vol=call_greek.get('volume', {})
                            put_vol=put_greek.get('volume', {})
                            p_c_ration = put_vol/ call_vol
                            
                            # call-spread / put-spread ---> (ASK/BID)
                            call_bid_ask = self.app.contract_chain_deltas.get(ticker, None).get(expiry, None).get(delta,None).get('C', None).get(call_strike, None).get('bid_ask', None)
                            if call_bid_ask is None:
                                continue
                            put_bid_ask = self.app.contract_chain_deltas.get(ticker, None).get(expiry, None).get(delta,None).get('P', None).get(put_strike, None).get('bid_ask', None)
                            if put_bid_ask is None:
                                continue
                            call_bid = call_bid_ask.get('bid', None)
                            if call_bid is None:
                                continue
                            put_bid = put_bid_ask.get('bid', None)
                            if put_bid is None:
                                continue
                            call_ask = call_bid_ask.get('ask', None)
                            if call_ask is None:
                                continue
                            put_ask = put_bid_ask.get('ask', None)
                            if put_ask is None:
                                continue
                            call_spread = round(abs(call_ask - call_bid), 4)
                            put_spread = round(abs(put_bid - put_ask), 4)
                            
                            
                            

                            # stock
                            stock_df = self.app.ticker_to_stkHist[ticker]
                            historical_vol = self.app.stocks_hist_iv[ticker]
                            stockIv = self.app.stocksIv.get(ticker)
                            beta = self.app.ticker_to_beta[ticker]
                            max_pain = self.app.max_pain.get(f'{ticker}-{expiry}', None)
                            min_pain = self.app.min_pain.get(f'{ticker}-{expiry}', None)
                            OI_R = self.app.OI_resistance[f'{ticker}-{expiry}']
                            OI_S = self.app.OI_support[f'{ticker}-{expiry}']
                            stk_open,stk_close,stk_ltp = stock_df['Open'].iloc[-1],list(stock_df['Close'])[-2],self.app.ltp[ticker]
                            stk_open_per = ((stk_ltp - stk_open) / stk_open) * 100
                            stk_close_per = ((stk_ltp - stk_close) / stk_close) * 100
                            
                         
                            
                            # delta ---> hist_iv / avg_iv_14 / todays_iv / vol_14_avg
                            call_local_symbol = f'{ticker} {expiry} {delta} C {call_strike}'
                            put_local_symbol = f'{ticker} {expiry} {delta} P {put_strike}'
                            if call_local_symbol not in self.app.local_symbol_to_open_close_iv or \
                                    put_local_symbol not in self.app.local_symbol_to_open_close_iv:
                                continue
                            
                            
                            call_open = round(self.app.local_symbol_to_open_close_iv[call_local_symbol]['open'], 3)
                            call_close = round(self.app.local_symbol_to_open_close_iv[call_local_symbol]['close'], 3)
                            call_ltp = round(call_greek.get('optPrice', {}), 3)
                            call_iv_14 = self.app.local_symbol_to_open_close_iv.get(call_local_symbol).get('hist_iv',None)
                            call_iv_14_avg = self.app.local_symbol_to_open_close_iv.get(call_local_symbol).get('avg_iv_14', None)
                            call_iv_today = self.app.local_symbol_to_open_close_iv.get(call_local_symbol).get('todays_iv', None)
                            call_vol_14_avg = self.app.local_symbol_to_open_close_iv.get(call_local_symbol).get('vol_14_avg', None)
                            
                            put_open = round(self.app.local_symbol_to_open_close_iv[put_local_symbol]['open'], 3)
                            put_close = round(self.app.local_symbol_to_open_close_iv[put_local_symbol]['close'], 3)
                            put_ltp = round(put_greek.get('optPrice', {}), 3)
                            put_iv_14 = self.app.local_symbol_to_open_close_iv.get(put_local_symbol).get('hist_iv',None)
                            put_iv_14_avg = self.app.local_symbol_to_open_close_iv.get(put_local_symbol).get('avg_iv_14', None)
                            put_iv_today = self.app.local_symbol_to_open_close_iv.get(put_local_symbol).get('todays_iv',None)
                            put_vol_14_avg = self.app.local_symbol_to_open_close_iv.get(put_local_symbol).get('vol_14_avg', None)
                            
                            call_open_per = ((call_ltp - call_open) / call_open) * 100
                            call_close_per = ((call_ltp - call_close) / call_close) * 100
                            call_change = (call_close_per / stk_close_per)
                            
                            put_open_per = ((put_ltp - put_open) / put_open) * 100
                            put_close_per = ((put_ltp - put_close) / put_close) * 100
                            put_change = (put_close_per / stk_close_per)
                            
                            if call_open_per == 0:
                                call_open_per = 100
                            if call_close_per == 0:
                                call_close_per = 100
                            if put_open_per == 0:
                                put_open_per = 100
                            if put_close_per == 0:
                                put_close_per = 100

                            stk_call_open_per = stk_open_per / call_open_per
                            stk_put_open_per = stk_open_per / put_open_per
                            stk_call_close_per = stk_close_per / call_close_per
                            stk_put_close_per = stk_close_per / put_close_per
                            
                            
                            call_impliedVol = call_greek.get('impliedVol', None)
                            put_impliedVol = put_greek.get('impliedVol', None)
                            netIv = (call_impliedVol - put_impliedVol) * 100
                            
                            delta_iv_14_mean = round((call_iv_14_avg + put_iv_14_avg) / 2, 3)
                            stkOptIv = round(stockIv - ((call_impliedVol + put_impliedVol) / 2), 4)
                            
                            avg_iv = ((call_impliedVol + put_impliedVol) / 2) * 100
                            RR_iv_ratio = (netIv * 100) / 16 - (avg_iv / 16)
                            
                            net_iv_14 = (call_iv_14 - put_iv_14) * 100
                            if net_iv_14 == 0:
                                net_iv_14 = 50
                                
                            rr_iv_14 = ((netIv - net_iv_14) / net_iv_14) * 100
                            
                            net_iv_today = (call_iv_today - put_iv_today) * 100
                            if net_iv_today == 0:
                                net_iv_today = 50
                                
                            rr_iv_today = ((netIv - net_iv_today) / net_iv_today) * 100
                            
                            call_lvg = call_change * netIv
                            put_lvg = put_change * netIv
                            call_volatility = (call_change * historical_vol) / 100   
                            put_volatility = (put_change * historical_vol) / 100
                            call_beta = (call_change * beta) / 100     
                            put_beta = (put_change * beta) / 100                      
                            
                            delta_vol_14_mean = round((call_vol_14_avg + put_vol_14_avg) / 2, 3)
                            
                            
                            
                            
                            
                            
                
                            

                            call_charm = self.app.charm.get(f'{ticker} {expiry} C {call_strike}')
                            put_charm = self.app.charm.get(f'{ticker} {expiry} P {put_strike}')
                            call_vanna = self.app.vanna.get(f'{ticker} {expiry} C {call_strike}')
                            put_vanna = self.app.vanna.get(f'{ticker} {expiry} P {put_strike}')
                            if call_vanna is None or call_charm is None or put_vanna is None or put_charm is None:
                                continue

                            gamma_expo_strikes = self.app.gamma_exp.get(f'{ticker} {expiry}', None).get('strikes', None)
                            gamma_expo_call_gammas = self.app.gamma_exp.get(f'{ticker} {expiry}', None).get(
                                'call_gamma_exp', None)
                            gamma_expo_put_gammas = self.app.gamma_exp.get(f'{ticker} {expiry}', None).get(
                                'put_gamma_exp', None)
                            if gamma_expo_strikes and gamma_expo_call_gammas and gamma_expo_put_gammas and \
                                    len(gamma_expo_strikes) == len(gamma_expo_call_gammas) == len(
                                gamma_expo_put_gammas):
                                ticker_1 = ticker.split()[0]
                                manager.data['chart_data'][f'{ticker_1} {expiry}'] = [gamma_expo_strikes,
                                                                                      gamma_expo_call_gammas,
                                                                                      gamma_expo_put_gammas]
                                manager.data['profile_chart_data'][f'{ticker_1} {expiry}'] = [gamma_expo_strikes,
                                                                                              gamma_expo_call_gammas,
                                                                                              gamma_expo_put_gammas]

                                # Calculationg Net Call and net Put By expiry
                                expiries_to_send = []
                                net_call = []
                                net_put = []

                                for ticker_expiry in self.app.gamma_exp:
                                    # Extract ticker
                                    if len(ticker_expiry.split()) == 7:  # FUT
                                        ticker_get = ' '.join(ticker_expiry.split()[:6])

                                    elif len(ticker_expiry.split()) == 6:  # STK
                                        ticker_get = ' '.join(ticker_expiry.split()[:5])

                                    if ticker_get == ticker:
                                        expiries_to_send.append(ticker_expiry.split()[-1])
                                        net_call.append(
                                            sum(self.app.gamma_exp.get(f'{ticker_expiry}', None).get('call_gamma_exp',
                                                                                                     None)))
                                        net_put.append(
                                            sum(self.app.gamma_exp.get(f'{ticker_expiry}', None).get('put_gamma_exp',
                                                                                                     None)))

                                if isinstance(expiries_to_send, list) and len(expiries_to_send):
                                    manager.data['by_expiry_chart_data'][f'{ticker_1}'] = [expiries_to_send, net_call,
                                                                                           net_put]
                                a, b = sum(gamma_expo_call_gammas), sum(gamma_expo_put_gammas)

                                # VANNA BAR CHART CALCULATION
                                call_strikes = []
                                put_strikes = []
                                call_vanna_values = []
                                put_vanna_values = []
                                symbol_2 = None
                                for local_symbol in self.app.vanna:
                                    # Extract ticker
                                    if len(local_symbol.split()) == 9:  # FUT
                                        _ticker = ' '.join(local_symbol.split()[:6])
                                        _expiry, _right, _strike = local_symbol.split()[-3], local_symbol.split()[-2], \
                                        local_symbol.split()[-1]
                                    if len(local_symbol.split()) == 8:  # STK
                                        _ticker = ' '.join(local_symbol.split()[:5])
                                        _expiry, _right, _strike = local_symbol.split()[-3], local_symbol.split()[-2], \
                                        local_symbol.split()[-1]

                                    if ticker == _ticker and expiry == _expiry:
                                        symbol_2 = _ticker.split()[0]
                                        if _right == 'C':
                                            call_vanna_values.append(self.app.vanna[local_symbol])
                                            call_strikes.append(_strike)
                                        if _right == 'P':
                                            put_vanna_values.append(self.app.vanna[local_symbol])
                                            put_strikes.append(_strike)
                                manager.data['chart_data_vanna'][f'{symbol_2} {expiry}'] = [call_strikes,
                                                                                            call_vanna_values,
                                                                                            put_vanna_values]
                                manager.data['profile_chart_data_vanna'][f'{symbol_2} {expiry}'] = [call_strikes,
                                                                                                    call_vanna_values,
                                                                                                    put_vanna_values]

                                # #Expiries List
                                expiries_vanna = set()
                                for local_symbol in self.app.vanna:
                                    # Extract ticker
                                    if len(local_symbol.split()) == 9:  # FUT
                                        ticker_v = ' '.join(local_symbol.split()[:6])
                                        expiry_v, right_v, strike_v = local_symbol.split()[-3], local_symbol.split()[
                                            -2], local_symbol.split()[-1]

                                    elif len(local_symbol.split()) == 8:  # STK
                                        ticker_v = ' '.join(local_symbol.split()[:5])
                                        expiry_v, right_v, strike_v = local_symbol.split()[-3], local_symbol.split()[
                                            -2], local_symbol.split()[-1]
                                    if ticker_v == ticker:
                                        expiries_vanna.add(expiry_v)
                                expiries_vanna = list(expiries_vanna)
                                expiries_vanna_to_sent = []
                                net_call_vanna_to_sent = []
                                net_put_vanna_to_sent = []
                                symbol_1 = None
                                for expiry_needed_vanna in expiries_vanna:
                                    net_call_vanna = []
                                    net_put_vanna = []
                                    for local_symbol in self.app.vanna:
                                        # Extract ticker
                                        if len(local_symbol.split()) == 9:  # FUT
                                            ticker_v = ' '.join(local_symbol.split()[:6])
                                            expiry_v, right_v, strike_v = local_symbol.split()[-3], \
                                            local_symbol.split()[-2], local_symbol.split()[-1]
                                        elif len(local_symbol.split()) == 8:  # STK
                                            ticker_v = ' '.join(local_symbol.split()[:5])
                                            expiry_v, right_v, strike_v = local_symbol.split()[-3], \
                                            local_symbol.split()[-2], local_symbol.split()[-1]

                                        if ticker_v == ticker and expiry_v == expiry_needed_vanna:
                                            symbol_1 = ticker_v.split()[0]
                                            if right_v == 'C':
                                                net_call_vanna.append(self.app.vanna[local_symbol])
                                            if right_v == 'P':
                                                net_put_vanna.append(self.app.vanna[local_symbol])
                                    expiries_vanna_to_sent.append(expiry_needed_vanna)
                                    net_call_vanna_to_sent.append(sum(net_call_vanna))
                                    net_put_vanna_to_sent.append(sum(net_put_vanna))
                                manager.data['by_expiry_chart_data_vanna'][symbol_1] = [expiries_vanna_to_sent,
                                                                                        net_call_vanna_to_sent,
                                                                                        net_put_vanna_to_sent]

                            now = datetime.now(tz=TZ)
                            t = now.strftime("%H:%M:%S")
                            ticker_2 = ticker.split()[0]
                            localSymbol = f'{ticker_2}-{call_strike}-{put_strike}'
                           

                            printDictList.append(
                                {'time': t,
                                 'delta': delta,
                                 'expiry': expiry,
                                 'localSymbol': localSymbol,
                                 'call_spread': call_spread,
                                 'put_spread': put_spread,
                                  'P/C Volume': round(p_c_ration, 3),
                                 'gamma/C': round(call_greek.get('gamma', {}), 3),
                                 'gamma/P': round(put_greek.get('gamma', {}), 3),
                                 
                                 'avg_c_IV': round(call_iv_14_avg * 100, 2),
                                 'avg_p_IV': round(put_iv_14_avg * 100, 2),
                                 'RR': round(netIv, 2),
                                 'avg_RR_14': round(delta_iv_14_mean * 100, 2),
                                 'hv-iv': stkOptIv,
                                 'RR_iv_ratio': round(RR_iv_ratio, 4),
                                 'RR 14 DAYS': round(rr_iv_14, 2),
                                 'RR TODAY': round(rr_iv_today, 2),
                                 'call_lvg': round(call_lvg, 4),
                                 'put_lvg': round(put_lvg, 4),  
                                 'call_volatility': round(call_volatility, 4), 
                                 'put_volatility': round(put_volatility, 4), 
                                 'call_beta': round(call_beta, 4),  
                                 'put_beta': round(put_beta, 4),                           
                                 'avg_vol_14': delta_vol_14_mean,
                                 
                                 
                                 'max_pain': max_pain,
                                 'min_pain': min_pain,
                                  'OI/R': OI_R,  
                                 'OI/S': OI_S,
                                 
                                 'call/vanna': round(call_vanna, 3),
                                 'put/vanna': round(put_vanna, 3),
                                 'call/charm': round(call_charm, 3),
                                 'put/charm': round(put_charm, 3),
                                 
                                 'call_open_%': round(stk_call_open_per, 3),
                                 'call_close_%': round(stk_call_close_per, 3),
                                 'put_open_%': round(stk_put_open_per, 3),
                                 'put_close_%': round(stk_put_close_per, 3),
                                 

                                 })

            except NameError:
                return
            manager.data['table_data'] = printDictList
            time.sleep(1)
