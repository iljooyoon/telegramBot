import time
import hmac
import hashlib
import base64
import urllib.parse as url_parse
import decimal

from exchange.Exchange import Exchange


class bithumb(Exchange):
    def __init__(self, setting_file):
        super(bithumb, self).__init__('bithumb')

        self.host = "https://api.bithumb.com"

        self.load_settings(setting_file)

    def get_wallets(self):
        end_point = "/info/balance"

        data = {"currency": "ALL"}
        nonce = str(int(time.time() * 1000))
        query_string = end_point + chr(0) + url_parse.urlencode(data) + chr(0) + nonce
        h = hmac.new(self.secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha512)
        api_sign = base64.b64encode(h.hexdigest().encode('utf-8'))

        headers = {
            "Api-Key": self.access_key.encode('utf-8'),
            "Api-Sign": api_sign,
            "Api-Nonce": nonce
        }

        res = self.conn.post(self.host, end_point, headers=headers, body=data)

        response = res.json()

        asset_list = []

        for key in response['data'].keys():
            if not key.startswith('total_') or decimal.Decimal(response['data'][key]) == 0:
                continue

            cur = key.split('_')[1].upper()
            count = float(response['data'][key])

            asset_list.append([self.name, cur, count])

        return asset_list

    def get_market_price(self, symbols):
        end_point = '/public/transaction_history/{order_currency}_{payment_currency}?count=1'

        if type(symbols) == str:
            symbols = [symbols]

        market_price = {}

        for s in symbols:
            res = self.conn.get(self.host, end_point.format(**{'order_currency': s, 'payment_currency': 'KRW'}))

            response = res.json()

            if response['status'] != '0000':
                continue

            market_price[s] = float(response['data'][-1]['price'])

        return market_price