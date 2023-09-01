from scanner.settings import logger
from scanner.streaming.min_max_pain import MinMaxPain


class UpdateStremingKeyInContractChain:
    def __init__(self, app):
        self.app = app

    def run(self):
        if self.app.secContract_details_end.copy():
            for ticker in self.app.secContract_details_end:
                try:
                    try:
                        expiries = sorted(self.app.contract_chain[ticker].keys()).copy()
                    except:
                        continue
                    for expiry in expiries:
                        i = 0
                        for right in ['C', 'P']:
                            for strike in sorted(self.app.contract_chain[ticker][expiry][right].keys()).copy():
                                if (self.app.contract_chain[ticker][expiry][right][strike]['greek']['delta']) and \
                                        ((self.app.contract_chain[ticker][expiry][right][strike]['greek'][
                                            'impliedVol'])) and \
                                        ((self.app.contract_chain[ticker][expiry][right][strike]['greek']['gamma'])) and \
                                        ((self.app.contract_chain[ticker][expiry][right][strike]['greek']['OI'])) and \
                                        ((self.app.contract_chain[ticker][expiry][right][strike]['greek'][
                                            'optPrice'])) and \
                                        ((self.app.contract_chain[ticker][expiry][right][strike]['bid_ask']['bid'])) and \
                                        ((self.app.contract_chain[ticker][expiry][right][strike]['bid_ask']['ask'])) and \
                                        ((self.app.contract_chain[ticker][expiry][right][strike]['greek']['volume'])):
                                    i = i + 1
                        if i >= int((self.app.up_down * 4 * 70) / 100):  # change
                            if self.app.contract_chain[ticker][expiry]['streaming'] != True:
                                self.app.contract_chain[ticker][expiry]['streaming'] = True
                                logger.info(f'Total Fetched Strikes for {ticker} {expiry} : {i}')
                                obj = MinMaxPain(self.app)  # change
                                obj.run()

                # contract data is yet to be fetched                                       
                except KeyError:
                    continue
