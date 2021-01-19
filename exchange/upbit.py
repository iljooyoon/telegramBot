import uuid
import jwt

from exchange.Exchange import Exchange


class Upbit(Exchange):
    def __init__(self, setting_file, asset_file):
        super(Upbit, self).__init__(self.__class__.__name__, setting_file, asset_file)

        self.host = "https://api.upbit.com"

    def get_wallets(self):
        end_point = "/v1/accounts"

        """
        파라메터가 존재할 경우 다음과 같이 해야함.

        # query는 dict 타입입니다.
        m = hashlib.sha512()
        m.update(urlencode(query).encode())
        query_hash = m.hexdigest()

        payload = {
            'access_key': '발급받은 Access Key',
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
        """
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }

        jwt_token = jwt.encode(payload, self.secret_key).decode('utf-8')
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = self.conn.get(self.host, end_point, headers=headers)

        response = res.json()

        if res.status_code == 200:
            self.asset_list = {}

            for currency in response:
                cur = currency['currency']
                count = float(currency['balance']) + float(currency['locked'])

                self.asset_list.setdefault(cur, count)

            return [*self.asset_list, *self.asset_data]
        elif 'error' in response:
            raise RuntimeError(response['error']['message'], self.name, response['error'])

    def get_all_market_symbol(self):
        end_point = '/v1/market/all?isDetails=false'
        res = self.conn.get(self.host, end_point)

        response = []

        if res.status_code == 200:
            response = res.json()

        return response

    def get_market_price(self, symbols):
        end_point = '/v1/ticker'

        if type(symbols) == str:
            symbols = [symbols]

        all_market_symbol = self.get_all_market_symbol()

        target_symbols = []

        for exist_symbol in all_market_symbol:
            if exist_symbol['market'].split('-')[0] == 'KRW' and exist_symbol['market'].split('-')[1] in symbols:
                target_symbols.append(exist_symbol['market'])

        markets = ','.join(target_symbols)

        res = self.conn.get(self.host, end_point, params={"markets": markets})

        market_price = {}

        if res.status_code == 200:
            response = res.json()

            for market in response:
                market_price[market['market'].split('-')[1]] = market['trade_price']

        return market_price
