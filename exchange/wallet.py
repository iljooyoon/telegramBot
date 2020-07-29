import requests

from exchange.Exchange import Exchange


class wallet(Exchange):
    def __init__(self, setting_file):
        super(wallet, self).__init__('wallet')

        self.host = "https://api.ethplorer.io"

        self.load_settings(setting_file)
        self.market_price = {}

    def get_wallets(self):
        end_point = "/getAddressInfo/{addr}?apiKey={apiKey}"

        asset_list = []
        self.market_price = {}

        for address in self.addresses:
            res = self.conn.get(self.host, end_point.format(addr=address['addr'], apiKey=address['apiKey']))

            if res.status_code == 200:
                response = res.json()

                cur = 'ETH'
                count = response['ETH']['balance']

                asset_list.append([self.name, cur, count])

                for token in response['tokens']:
                    if 'symbol' in token['tokenInfo']:
                        cur = token['tokenInfo']['symbol']
                        count = token['balance'] / 10**int(token['tokenInfo']['decimals'])

                        asset_list.append([self.name, cur, count])

                        if token['tokenInfo']['price'] is not False and token['tokenInfo']['price']['currency'] == 'USD':
                            exchange = requests.get('https://earthquake.kr:23490/query/USDKRW').json()['USDKRW'][0]

                            self.market_price[cur] = token['tokenInfo']['price']['rate'] * exchange

        return asset_list

    def get_market_price(self, symbols):
        return self.market_price
