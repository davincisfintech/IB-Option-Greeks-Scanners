import requests
import base64
from pprint import pprint
import time



api_key_and_secret = 'bb4d0be7f8ed4b1b9ec0:fundrisq123@'
token = base64.b64encode(bytes(api_key_and_secret, encoding='utf-8')).decode()
headers={
    'Authorization': f'Basic {token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',}




res = requests.post('https://ews.fip.finra.org/fip/rest/ews/oauth2/access_token?grant_type=client_credentials',
                    headers={'Authorization': f'Basic {token}'}).json()

req_data=requests.post('https://api.finra.org/data/group/otcMarket/name/equityShortInterest?limit=500000000',
                   headers=headers).json()
pprint(req_data[-1])
for d in req_data:
    if d['issueSymbolIdentifier']=='SPY':
        pprint(d)

