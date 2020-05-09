import requests
import json
import uuid
import jwt
import time
import base64
import urllib.parse as url_parse
import hmac
import hashlib
import fileutils


class MargetRequest:
    def __init__(self, setting_json_file_name, asset_json_file_name):
        data = fileutils.read_json_file(setting_json_file_name)
        asset_data = fileutils.read_json_file(asset_json_file_name)

        self.setting_data = data
        self.asset_data = asset_data
        self.minus_list = {}
        self.summary = {}
        self.market_price = {}

    def get_exchange_rate(self):
        for asset in self.asset_data['info']:
            if self.minus_list.get(asset['exchange']) is None:
                self.minus_list[asset['exchange']] = {}

            for ml in asset['minus_list']:
                for k in ml.keys():
                    self.minus_list[asset['exchange']][k] = ml[k]

            if asset['type'] == 0:
                res = requests.request(asset['method'], asset['URI'], params={"markets": asset['markets']})

                if res.status_code == 200:
                    response = res.json()

                    for market in response:
                        self.market_price[market['market']] = market['trade_price']

            elif asset['type'] == 1:
                for m_list in asset['market_list']:
                    res = requests.request(asset['method'], asset['URI'].format(**m_list))

                    response = res.json()

                    if response['status'] != '0000':
                        continue

                    self.market_price[m_list['payment_currency'] + '-' + m_list['order_currency']] = float(
                        response['data'][-1]['price'])

        # print(self.market_price)

    def get_market_assets(self):
        asset_list = []

        for exchange, attr in self.setting_data.items():
            access_key = attr['access_key']
            secret_key = attr['secret_key']
            server_url = attr['server_url']
            end_point = attr['end_point']

            if exchange == 'upbit':
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
                    'access_key': access_key,
                    'nonce': str(uuid.uuid4()),
                }

                jwt_token = jwt.encode(payload, secret_key).decode('utf-8')
                authorize_token = 'Bearer {}'.format(jwt_token)
                headers = {"Authorization": authorize_token}

                res = requests.get(server_url + end_point, headers=headers)

                response = res.json()

                for currency in response:
                    cur = currency['currency']
                    count = float(currency['balance']) + float(currency['locked'])

                    asset_list.append([exchange, cur, count])

            elif exchange == 'bithumb':
                data = {"currency": "ALL"}
                nonce = str(int(time.time() * 1000))
                query_string = end_point + chr(0) + url_parse.urlencode(data) + chr(0) + nonce
                h = hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha512)
                api_sign = base64.b64encode(h.hexdigest().encode('utf-8'))

                headers = {
                    "Api-Key": access_key.encode('utf-8'),
                    "Api-Sign": api_sign,
                    "Api-Nonce": nonce
                }

                res = requests.post(server_url + end_point, data=data, headers=headers)

                response = res.json()

                for key in response['data'].keys():
                    if not key.startswith('total_'):
                        continue

                    cur = key.split('_')[1].upper()
                    count = float(response['data'][key])

                    asset_list.append([exchange, cur, count])

            elif exchange == 'bitfinex':
                nonce = str(int(round(time.time() * 1000)))
                body = {}
                raw_body = json.dumps(body)
                signature = '/api' + end_point + nonce + raw_body
                h = hmac.new(secret_key.encode('utf8'), signature.encode('utf8'), hashlib.sha384)
                signature = h.hexdigest()
                headers = {
                    "bfx-nonce": nonce,
                    "bfx-apikey": access_key,
                    "bfx-signature": signature,
                    "content-type": "application/json"
                }

                res = requests.post(server_url + end_point, headers=headers, data=raw_body, verify=True)

                if res.status_code == 200:
                    response = res.json()

                    for currency in response:
                        cur = currency[1]
                        count = float(currency[2])

                        asset_list.append([exchange, cur, count])
                else:
                    print(exchange, res.status_code)
                    continue

        for exchange, cur, count in asset_list:
            if self.minus_list.get(exchange) is not None and self.minus_list[exchange].get(cur) is not None:
                count -= self.minus_list[exchange][cur]

            self.add_summary(exchange, cur, count)

    def add_summary(self, exchange, cur, count):
        if count <= 0:
            return

        if cur != 'KRW':
            if self.market_price.get('KRW-' + cur) is None:
                asset_data = fileutils.read_json_file('./asset.json')

                found = False

                for i, asset in enumerate(asset_data['info']):
                    if asset['type'] == 0:
                        res = requests.request(asset['method'], asset['URI'], params={"markets": 'KRW-' + cur})

                        if res.status_code == 200:
                            found = True
                            response = res.json()

                            for market in response:
                                self.market_price[market['market']] = market['trade_price']

                            asset_data['info'][i]['markets'] += ',KRW-' + cur

                            fileutils.write_json_file('./asset.json', asset_data)

                            break

                    elif asset['type'] == 1:
                        m_list = {
                            "order_currency": cur,
                            "payment_currency": "KRW"
                        }
                        res = requests.request(asset['method'], asset['URI'].format(**m_list))

                        if res.status_code == 200:
                            response = res.json()

                            if response['status'] != '0000':
                                continue

                            found = True

                            self.market_price['KRW-' + m_list['order_currency']] = float(response['data'][-1]['price'])

                            asset_data['info'][i]['market_list'].append(m_list)

                            fileutils.write_json_file('./asset.json', asset_data)

                            break

                if not found:
                    if self.summary.get('others') is None:
                        self.summary['others'] = {}
                    if self.summary['others'].get(cur) is None:
                        self.summary['others'][cur] = {'count': 0}
                    self.summary['others'][cur]['count'] += count

                    return

            krw = count * self.market_price['KRW-' + cur]
        else:
            krw = count

        if krw < 100:
            return

        if self.summary.get(exchange) is None:
            self.summary[exchange] = 0
        self.summary[exchange] += krw

        if self.summary.get(cur) is None:
            if cur == 'KRW':
                self.summary[cur] = 0
            else:
                self.summary[cur] = {'KRW': 0, 'count': 0}

        if cur == 'KRW':
            self.summary[cur] += krw
        else:
            self.summary[cur]['KRW'] += krw
            self.summary[cur]['count'] += count

        if self.summary.get('total') is None:
            self.summary['total'] = 0
        self.summary['total'] += krw

    def get_summary(self):
        return self.summary

"""
[
 {"market":"KRW-BTC","trade_date_kst":"20200123","trade_time_kst":"222413","trade_price":9659000.0}
,{"market":"KRW-ETH","trade_date_kst":"20200123","trade_time_kst":"222400","trade_price":187000.0}
,{"market":"KRW-XRP","trade_date_kst":"20200123","trade_time_kst":"222413","trade_price":261.0}
]
"""
