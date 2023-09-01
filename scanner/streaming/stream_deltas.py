class StreamDeltas:
    def __init__(self, app):
        self.app = app

    def run(self):
        self.app.nextorderId += 1
        try:
            if self.app.secContract_details_end:
                for ticker in self.app.tickers:
                    try:
                        expiries = sorted(self.app.contract_chain_deltas[ticker].keys())
                    except:
                        continue
                    for expiry in expiries:
                        for delta in self.app.deltas:
                            for right in ['C', 'P']:
                                try:
                                    strikes = self.app.contract_chain_deltas.get(ticker, {}).get(expiry, {}).get(delta,
                                                                                                                 {}).get(
                                        right, {}).keys()
                                except KeyError:
                                    continue
                                if strikes is None:
                                    continue
                                for strike in strikes:
                                    s = f'{ticker} {expiry} {delta} {right} {strike}'
                                    if s in self.app.stream_deltas_ids:
                                        continue
                                    self.app.stream_deltas_ids.add(s)
                                    reqId = self.app.nextorderId
                                    self.app.symbol_to_id[s] = reqId
                                    self.app.id_to_localSymnol[reqId] = s
                                    self.app.bid_ask_reqId[reqId] = s

                                    # Extract ticker
                                    if len(ticker.split()) == 6:  # FUT
                                        _symbol, _sec_type, _exch, _curr, _multiplier, _expiry_date = ticker.split()
                                    elif len(ticker.split()) == 5:  # STK
                                        _symbol, _sec_type, _exch, _curr, _multiplier = ticker.split()

                                    if _sec_type == 'STK':
                                        _sec_type = 'OPT'
                                    elif _sec_type == 'FUT':
                                        _sec_type = 'FOP'

                                    # Contract Build & Send Request
                                    contract = self.app.my_contract(
                                        f'{_symbol} {_sec_type} {_exch} {_curr} {_multiplier} {expiry} {strike} {right}')
                                    if not self.app.validate_opt_contract(contract):
                                        continue
                                    self.app.nextorderId += 1
                                    self.app.reqMktData(reqId=reqId, contract=contract, genericTickList="106",
                                                        snapshot=False,
                                                        regulatorySnapshot=False, mktDataOptions=[])

        except NameError:
            return
