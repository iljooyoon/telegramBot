import time
import hmac
import hashlib
import json

from exchange.Exchange import Exchange


class Bitfinex(Exchange):
    def __init__(self, setting_file, asset_file):
        super(Bitfinex, self).__init__(self.__class__.__name__, setting_file, asset_file)

        self.host = "https://api.bitfinex.com"

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

        self.asset_list = {}

        if res.status_code == 200:
            response = res.json()

            for currency in response:
                cur = currency[1]
                count = float(currency[2])

                self.asset_list[cur] = self.asset_list.get(cur, 0) + count
        else:
            print(self.name, res.status_code)

        return [*self.asset_list, *self.asset_data]

    def get_market_price(self, symbols):
        return {}
