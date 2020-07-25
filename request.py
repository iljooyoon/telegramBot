from utils import fileutils
from exchange.bithumb import bithumb
from exchange.upbit import upbit
from exchange.bitfinex import bitfinex
from exchange.wallet import wallet


class MargetRequest:
    def __init__(self, setting_json_file_name, asset_json_file_name):
        data = fileutils.read_json_file(asset_json_file_name)
        self.asset_data = [[key, k, v] for key in data.keys() for k, v in zip(data[key].keys(), data[key].values())]
        self.summary = {}
        self.my_market = [upbit(setting_json_file_name),
                          bithumb(setting_json_file_name),
                          bitfinex(setting_json_file_name),
                          wallet(setting_json_file_name)]

    def get_market_assets(self):
        asset_list = []

        for m in self.my_market:
            if m.check_valid():
                asset_list.extend(m.get_wallets())

        asset_list = self.add_manual_asset(asset_list)

        asset_list = list(filter(lambda asset: asset[2] > 0, asset_list))

        return asset_list

    def add_manual_asset(self, asset_list):
        for manual_asset in self.asset_data:
            found = False
            for asset in asset_list:
                if asset[0] == manual_asset[0] and asset[1] == manual_asset[1]:
                    asset[2] += manual_asset[2]
                    found = True
                    break
            if not found:
                asset_list.append(manual_asset)

        return asset_list

    def get_market_price(self, asset_list):
        symbols = set([symbol for _, symbol, _ in asset_list])

        symbols.difference_update('KRW')

        market_price = {}

        for m in self.my_market:
            mp = m.get_market_price(symbols)

            market_price.update(mp)

            symbols.difference_update(set(mp.keys()))

        return market_price

    def add_summary(self, exchange, cur, count, market_price):
        if count == 0:
            return

        if cur != 'KRW':
            if market_price.get(cur) is None:
                if self.summary.get('others') is None:
                    self.summary['others'] = {}
                if self.summary['others'].get(cur) is None:
                    self.summary['others'][cur] = {'count': 0}
                self.summary['others'][cur]['count'] += count

                return

            krw = count * market_price[cur]
        else:
            krw = count

        if abs(krw) < 100:
            return

        if self.summary.get(exchange) is None:
            self.summary[exchange] = 0
        self.summary[exchange] += krw

        if self.summary.get(cur) is None:
            if cur == 'KRW':
                self.summary[cur] = 0
            else:
                self.summary[cur] = {'KRW': 0, 'count': 0, 'price': market_price[cur]}

        if cur == 'KRW':
            self.summary[cur] += krw
        else:
            self.summary[cur]['KRW'] += krw
            self.summary[cur]['count'] += count

        if self.summary.get('total') is None:
            self.summary['total'] = 0
        self.summary['total'] += krw

    def get_summary(self):
        asset_list = self.get_market_assets()

        market_price = self.get_market_price(asset_list)

        for exchange, cur, count in asset_list:
            self.add_summary(exchange, cur, count, market_price)

        return self.summary

"""
[
 {"market":"KRW-BTC","trade_date_kst":"20200123","trade_time_kst":"222413","trade_price":9659000.0}
,{"market":"KRW-ETH","trade_date_kst":"20200123","trade_time_kst":"222400","trade_price":187000.0}
,{"market":"KRW-XRP","trade_date_kst":"20200123","trade_time_kst":"222413","trade_price":261.0}
]
"""
