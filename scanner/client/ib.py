import time

import pytz
from dateutil.parser import parse

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper
from scanner.settings import logger
from scanner.utilis.days_to_expiries import needed_expiries
from scanner.utilis.remove_strikes import remove_strikes


class TradingApp(EWrapper, EClient):
    def __init__(self, tickers, deltas, up_down, days_to_expiries, tick_type_iv, delay_in_minutes):
        EClient.__init__(self, self)
        self.test = 0
        self.tick_type_iv = tick_type_iv
        self.delay_in_minutes = delay_in_minutes
        self.contract_chain = {}
        self.secContract_details_end = list()
        self.contract_ticker_id = {}
        self.ltp = {}
        self.symbol_to_id = {}
        self.stream_ltp_ids = {}
        self.stream_found_deltas_ids = {}
        self.stream_bid_ask_ids = {}
        self.id_to_greek_value = {}
        self.contract_chain_deltas = {}
        self.tickers = tickers
        self.ticker_to_conId = {}
        self.secDfId_to_symbol = {}
        self.delta_strike_symbol_id = {}
        self.deltas_found = {}
        self.id_to_localSymnol = {}
        self.expiries = list()
        self.tickers = tickers
        self.deltas = deltas
        self.up_down = up_down
        self.stocksIv = {}
        self.stocks_hist_iv = {}
        self.ticker_to_beta = {}
        self.histData = {}
        self.histData_end = set()
        self.errors_store = set()
        self.ticker_sent = {}
        self.test = None
        self.bid_ask_reqId = {}
        self.days_to_expiries = days_to_expiries
        self.id_to_delta = {}
        self.id_to_iv = {}
        self.stopped_ids = set()
        self.stream_deltas_ids = set()
        self.contract_details_end = list()
        self.error_ids = list()
        self.annual_vol = dict()
        self.charm = dict()
        self.vanna = dict()
        self.min_pain = dict()
        self.max_pain = dict()
        self.OI_resistance = dict()
        self.OI_support = dict()
        self.ticker_to_stkHist = dict()
        self.local_symbol_to_hist_data = dict()
        self.local_symbol_to_open_close_iv = dict()
        self.local_symbol_id_hist_data = dict()
        self.gamma_exp = dict()
        self.counter = 0

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId

    def stop_streaming(self, reqId):
        super().cancelMktData(reqId)

    def error(self, reqId, errorCode: int, errorString: str, advancedOrderRejectJson=""):
        super().error(reqId, errorCode, errorString, advancedOrderRejectJson)
        self.error_ids.append(reqId)
        errorCode = int(errorCode)
        if errorCode == 10090:
            return
        if errorCode == 300:
            return
        if advancedOrderRejectJson:
            logger.debug("Error. Id:", reqId, "Code:", errorCode, "Msg:", errorString, "AdvancedOrderRejectJson:",
                         advancedOrderRejectJson)
        else:
            if errorCode != 300:
                logger.debug(f'Error. Id:", {reqId} "Code:", {errorCode}, "Msg:", {errorString}')

    def stock_ltp(self):
        self.nextorderId += 1
        for ticker in self.tickers:
            reqId = self.nextorderId
            self.ticker_sent[reqId] = ticker
            self.nextorderId += 1
            contract = self.my_contract(ticker)
            self.reqMktData(reqId=reqId, contract=contract, genericTickList="", snapshot=False,
                            regulatorySnapshot=False, mktDataOptions=[])
            time.sleep(1)
        return

    def my_contract(self, ticker):
        ticker = ticker.split()
        if len(ticker) == 5:  # STK
            symbol, sec_type, exch, curr, multiplier = ticker
            contract = self.make_contract(symbol=symbol, sec_type=sec_type, exch=exch, curr=curr, multiplier=multiplier)
        elif len(ticker) == 6:  # FUT
            symbol, sec_type, exch, curr, multiplier, expiry_date = ticker
            contract = self.make_contract(symbol=symbol, sec_type=sec_type, exch=exch, curr=curr, multiplier=multiplier,
                                          expiry_date=expiry_date)
        elif len(ticker) == 8:  # OPT/FOP
            symbol, sec_type, exch, curr, multiplier, expiry_date, strike, opt_type = ticker
            contract = self.make_contract(symbol=symbol, sec_type=sec_type, exch=exch, curr=curr, multiplier=multiplier,
                                          expiry_date=expiry_date, strike=strike, opt_type=opt_type)
        return contract

    def contractDetails(self, reqId, contractDetails):
        self.ticker_to_conId[contractDetails.contract.symbol] = contractDetails.contract.conId

    def contractDetailsEnd(self, reqId: int):
        super().contractDetailsEnd(reqId)
        self.contract_details_end.append(reqId)

    def get_contract_ids(self):
        for symbol in self.tickers:
            contract = self.my_contract(symbol)
            reqId = self.nextorderId
            self.reqContractDetails(reqId, contract)
            self.nextorderId += 1
            time.sleep(1)

    def my_ticker(self, ticker):
        ticker = ticker.split()
        if len(ticker) == 5:  # STK
            symbol, sec_type, exch, curr, multiplier = ticker
        if len(ticker) == 6:  # FUT
            symbol, sec_type, exch, curr, multiplier, expiry_date = ticker
        return symbol

    def historicalData(self, reqId, bar):
        date_str = bar.date if len(bar.date.split()) < 2 else bar.date.split()[0] + ' ' + bar.date.split()[1]
        date_str = parse(date_str).astimezone(pytz.timezone('US/Eastern'))
        if reqId not in self.histData:
            self.histData[reqId] = [
                {"Date": date_str, "Open": bar.open, "High": bar.high, "Low": bar.low, "Close": bar.close,
                 "Volume": bar.volume, "Wap": bar.wap}]
        else:
            self.histData[reqId].append(
                {"Date": date_str, "Open": bar.open, "High": bar.high, "Low": bar.low, "Close": bar.close,
                 "Volume": bar.volume, "Wap": bar.wap})

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        self.histData_end.add(reqId)

    def update_greek(self, localSymbol, _delta=None, impliedVol=None, bid_price=None, ask_price=None, OI=None,
                     volume=None, gamma=None, optPrice=None, gamma_exposure=None):
        try:
            localSymbol = localSymbol.split()
            if (len(localSymbol) == 8 and localSymbol[1] == 'STK') or (
                    len(localSymbol) == 9 and localSymbol[1] == 'FUT'):
                if len(localSymbol) == 8 and localSymbol[1] == 'STK':
                    ticker = ' '.join(localSymbol[:5])
                    expiry, right, strike = localSymbol[-3], localSymbol[-2], localSymbol[-1]
                elif len(localSymbol) == 9 and localSymbol[1] == 'FUT':
                    ticker = ' '.join(localSymbol[:6])
                    expiry, right, strike = localSymbol[-3], localSymbol[-2], localSymbol[-1]
                strike = float(strike)

                if _delta:
                    self.contract_chain[ticker][expiry][right][strike]['greek']['delta'] = _delta
                if impliedVol:
                    self.contract_chain[ticker][expiry][right][strike]['greek']['impliedVol'] = impliedVol
                if bid_price:
                    self.contract_chain[ticker][expiry][right][strike]['bid_ask']['bid'] = bid_price
                if ask_price:
                    self.contract_chain[ticker][expiry][right][strike]['bid_ask']['ask'] = ask_price
                if volume:
                    self.contract_chain[ticker][expiry][right][strike]['greek']['volume'] = volume
                if OI:
                    self.contract_chain[ticker][expiry][right][strike]['greek']['OI'] = OI * 1000
                if gamma:
                    self.contract_chain[ticker][expiry][right][strike]['greek']['gamma'] = gamma
                if optPrice:
                    self.contract_chain[ticker][expiry][right][strike]['greek']['optPrice'] = optPrice


            elif (len(localSymbol) == 9 and localSymbol[1] == 'STK') or (
                    len(localSymbol) == 10 and localSymbol[1] == 'FUT'):
                if len(localSymbol) == 9 and localSymbol[1] == 'STK':
                    ticker = ' '.join(localSymbol[:5])
                    expiry, delta, right, strike = localSymbol[-4], localSymbol[-3], localSymbol[-2], localSymbol[-1]
                elif len(localSymbol) == 10 and localSymbol[1] == 'FUT':
                    ticker = ' '.join(localSymbol[:6])
                    expiry, delta, right, strike = localSymbol[-4], localSymbol[-3], localSymbol[-2], localSymbol[-1]
                delta = float(delta)
                strike = float(strike)

                if _delta:
                    self.contract_chain_deltas[ticker][expiry][delta][right][strike]['greek']['delta'] = _delta
                if impliedVol:
                    self.contract_chain_deltas[ticker][expiry][delta][right][strike]['greek']['impliedVol'] = impliedVol

                if bid_price:
                    self.contract_chain_deltas[ticker][expiry][delta][right][strike]['bid_ask']['bid'] = bid_price
                if ask_price:
                    self.contract_chain_deltas[ticker][expiry][delta][right][strike]['bid_ask']['ask'] = ask_price
                if volume:
                    self.contract_chain_deltas[ticker][expiry][delta][right][strike]['greek']['volume'] = volume
                if OI:
                    self.contract_chain_deltas[ticker][expiry][delta][right][strike]['greek']['OI'] = OI
                if gamma:
                    self.contract_chain_deltas[ticker][expiry][delta][right][strike]['greek']['gamma'] = gamma
                if optPrice:
                    self.contract_chain_deltas[ticker][expiry][delta][right][strike]['greek']['optPrice'] = optPrice

        except KeyError:
            return

    # 27 is tick type for call option OI, use 28 if put option
    # 8 is tick type for volume
    def tickSize(self, reqId, tickType, size):
        super().tickSize(reqId, tickType, size)
        s = self.id_to_localSymnol.get(reqId)
        if s and tickType == 27:
            self.update_greek(localSymbol=s, OI=int(size))
        if s and tickType == 28:
            self.update_greek(localSymbol=s, OI=int(size))
        if s and tickType == 8:
            self.update_greek(localSymbol=s, volume=int(size))

    def tickGeneric(self, tickerId, field, value):
        super().tickGeneric(tickerId, field, value)
        s = self.id_to_localSymnol.get(tickerId)
        if not s:
            return
        if field == 24 and value and self.tick_type_iv == 24:
            self.update_greek(localSymbol=s, impliedVol=value)

    def tickOptionComputation(self, reqId, tickType, tickAttrib, impliedVol, delta, optPrice, pvDividend, gamma, vega,
                              theta, undPrice):
        super().tickOptionComputation(reqId, tickType, tickAttrib, impliedVol, delta, optPrice, pvDividend, gamma, vega,
                                      theta, undPrice)
        if reqId in self.stopped_ids:
            return
        if reqId in self.id_to_localSymnol:
            s = self.id_to_localSymnol.get(reqId)
            if s:
                if tickType == 11:
                    if gamma:
                        self.update_greek(localSymbol=s, gamma=gamma)
                    if optPrice:
                        self.update_greek(localSymbol=s, optPrice=optPrice)
                if tickType == 12 and self.tick_type_iv == 12:
                    if impliedVol:
                        self.update_greek(localSymbol=s, impliedVol=impliedVol)
                if tickType == 13 and self.tick_type_iv in [12, 24]:
                    if delta:
                        self.id_to_delta[reqId] = round(float(delta), 4)
                        self.update_greek(localSymbol=s, _delta=delta)

        if (len(s.split()) == 8 and s.split()[1] == 'STK') or (len(s.split()) == 9 and s.split()[1] == 'FUT'):
            if len(s.split()) == 8 and s.split()[1] == 'STK':
                ticker = ' '.join(s.split()[:5])
                expiry, right, strike = s.split()[-3], s.split()[-2], s.split()[-1]
            elif len(s.split()) == 9 and s.split()[1] == 'FUT':
                ticker = ' '.join(s.split()[:6])
                expiry, right, strike = s.split()[-3], s.split()[-2], s.split()[-1]
            strike = float(strike)

            greek = self.contract_chain[ticker][expiry][right][strike]['greek']
            bid_ask = self.contract_chain[ticker][expiry][right][strike]['bid_ask']

            if (greek['delta'] and greek['impliedVol'] and greek['gamma']) and \
                    greek['volume'] and greek['OI'] and greek['optPrice']:
                if bid_ask:
                    if 'bid' in bid_ask and 'ask' in bid_ask:
                        self.stop_streaming(reqId)
                        self.stopped_ids.add(reqId)

    def tickPrice(self, reqId, tickType, price, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        if reqId in self.stopped_ids:
            return
        if reqId in self.ticker_sent:
            if tickType == 4 or tickType == 68:
                ticker = self.ticker_sent[reqId]
                self.ltp[ticker] = price
                return
        if reqId in self.id_to_localSymnol:
            s = self.id_to_localSymnol.get(reqId)
            if s:
                if tickType == 1 or tickType == 66:
                    self.update_greek(localSymbol=s, bid_price=price)
                if tickType == 2 or tickType == 67:
                    self.update_greek(localSymbol=s, ask_price=price)

    def get_contract_chain(self):
        for ticker in self.tickers:
            reqId = self.nextorderId
            self.secDfId_to_symbol[reqId] = ticker
            ticker = ticker.split()

            self.reqSecDefOptParams(
                reqId=reqId,
                underlyingSymbol=ticker[0],
                futFopExchange=ticker[2] if len(ticker) == 6 else '',
                underlyingSecType=ticker[1],
                underlyingConId=self.ticker_to_conId[ticker[0]])
            self.nextorderId += 1

            logger.info(f'reqSecDefOptParams sent for {ticker[0]}')
            ticker = ' '.join(ticker)
            while ticker not in self.contract_chain:
                time.sleep(0.5)
                pass
            self.secContract_details_end.append(ticker)
            expirations = sorted(self.contract_chain[ticker].keys())
            needed_expirations = sorted(needed_expiries(self.days_to_expiries, expirations))

            for key in sorted(self.contract_chain[ticker].keys()).copy():
                if key not in needed_expirations:
                    del self.contract_chain[ticker][key]

    def securityDefinitionOptionParameter(self, reqId, exchange, underlyingConId, tradingClass, multiplier,
                                          expirations, strikes):
        ticker = self.secDfId_to_symbol[reqId]
        if exchange == ticker.split()[2]:
            if not expirations or not strikes or not exchange:
                return
            expirations = sorted(expirations)
            strikes = sorted(strikes)
            strikes = remove_strikes(strikes_list=strikes, ltp=self.ltp[ticker], up_down=self.up_down, ticker=ticker)

            if ticker not in self.contract_chain:
                self.contract_chain[ticker] = {}
            for expiry in expirations:
                self.contract_chain[ticker][expiry] = {'C': {}, 'P': {}, 'streaming': False}
            for expiry in expirations:
                for right in ['C', 'P']:
                    for strike in strikes:
                        self.contract_chain[ticker][expiry][right][strike] = {
                            'greek': {
                                'delta': None,
                                'gamma': None,
                                'impliedVol': None,
                                'OI': None,
                                'volume': None,
                                'optPrice': None,
                                'gamma_exposure': None, },
                            'bid_ask': {}}

    @staticmethod
    def make_contract(symbol, sec_type, exch, prim_exch=None, curr='USD', opt_type=None, expiry_date=None,
                      strike=None, multiplier=None, tradingClass=None):
        contract = Contract()
        contract.symbol = str(symbol)
        contract.secType = sec_type
        contract.exchange = exch
        contract.currency = str(curr)
        contract.multiplier = multiplier

        if expiry_date != None:
            contract.lastTradeDateOrContractMonth = str(expiry_date)
        if opt_type != None:
            contract.right = str(opt_type)
        if strike != None:
            contract.strike = float(strike)
        if tradingClass != None:
            contract.tradingClass = tradingClass
        if prim_exch is not None:
            contract.primaryExch = prim_exch
        return contract

    def validate_opt_contract(self, contract_to_varify):
        try:
            self.nextorderId += 1
            reqId = self.nextorderId
            self.reqContractDetails(reqId, contract_to_varify)

            # in seconds
            TIME_OUT = 15
            start_time = time.time()
            while reqId not in self.contract_details_end + self.error_ids:
                if time.time() - start_time > TIME_OUT:
                    logger.debug(f'Error: Time out for :{reqId}')
                    return False
                time.sleep(0.1)
            if reqId in self.contract_details_end:
                return True
            return False
        except Exception as e:
            logger.exception(e)
