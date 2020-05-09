import time
import hmac
import hashlib
import json

from exchange.Exchange import Exchange


class bitfinex(Exchange):
    def __init__(self, setting_file):
        super(bitfinex, self).__init__('bitfinex')

        self.host = "https://api.bitfinex.com"

        self.load_settings(setting_file)

    def get_wallets(self):
        end_point = "/v2/auth/r/wallets"

        nonce = str(int(round(time.time() * 1000)))
        body = {}
        raw_body = json.dumps(body)
        signature = '/api' + end_point + nonce + raw_body
        h = hmac.new(self.secret_key.encode('utf8'), signature.encode('utf8'), hashlib.sha384)
        signature = h.hexdigest()
        headers = {
            "bfx-nonce": nonce,
            "bfx-apikey": self.access_key,
            "bfx-signature": signature,
            "content-type": "application/json"
        }

        res = self.conn.post(self.host, end_point, headers=headers, body=raw_body, verify=True)

        asset_list = []

        if res.status_code == 200:
            response = res.json()

            for currency in response:
                cur = currency[1]
                count = float(currency[2])

                asset_list.append([self.name, cur, count])
        else:
            print(self.name, res.status_code)

        return asset_list

    def get_market_price(self, symbols):
        return {}
