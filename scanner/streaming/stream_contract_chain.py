from scanner.settings import logger
from scanner.streaming.venna_charm import VennaCharm


class StreamOptionchain:
    def __init__(self, app):
        self.app = app

    def run(self):
        self.app.nextorderId += 1
        if self.app.secContract_details_end:
            try:
                for ticker in self.app.secContract_details_end:
                    try:
                        expiries = sorted(self.app.contract_chain[ticker].keys()).copy()
                    except:
                        continue
                    for expiry in expiries:
                        for right in ['C', 'P']:
                            try:
                                strikes = self.app.contract_chain.get(ticker, {}).get(expiry, {}).get(right, {}).keys()
                            except KeyError:
                                continue
                            if strikes is None:
                                continue
                            if ticker in self.app.secContract_details_end and strikes is None:
                                logger.debug(
                                    f'Error : inside stream_contract_chain strikes not available for {ticker}-{expiry}-{right} ')
                            for strike in strikes:
                                # Add venna
                                obj = VennaCharm(app=self.app, ticker=ticker, expiry=expiry, right=right,
                                                 strike=strike, )
                                obj.run()

                                s = f'{ticker} {expiry} {right} {strike}'
                                strike = float(strike)
                                reqId = self.app.nextorderId
                                self.app.id_to_localSymnol[reqId] = s
                                self.app.nextorderId += 1

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
                                self.app.reqMktData(reqId=reqId, contract=contract, genericTickList="106,100,101",
                                                    snapshot=False,
                                                    regulatorySnapshot=False, mktDataOptions=[])


            except NameError:
                return

        logger.info(f'contract chain streamed!')
