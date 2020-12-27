import requests

from exchange.bithumb import bithumb
from exchange.upbit import upbit
from exchange.bitfinex import bitfinex
from exchange.wallet import wallet


class MarketRequest:
    def __init__(self, setting_json_file_name, asset_json_file_name, beta=False):
        self.my_market = [upbit(setting_json_file_name, asset_json_file_name),
                          bithumb(setting_json_file_name, asset_json_file_name),
                          bitfinex(setting_json_file_name, asset_json_file_name),
                          wallet(setting_json_file_name, asset_json_file_name, beta)]

    def get_market_assets(self):
        asset_list = []

        for m in self.my_market:
            if m.check_valid():
                asset_list.extend(m.get_wallets())

        return asset_list

    def get_market_price(self, asset_list):
        symbols = set(asset_list)

        symbols.difference_update(['KRW'])

        market_price = {}

        for m in self.my_market:
            mp = m.get_market_price(symbols)

            market_price.update(mp)

            symbols.difference_update(set(mp.keys()))

        for symbol in symbols:
            q = symbol + 'KRW'
            res_json = requests.get('https://earthquake.kr:23490/query/{}'.format(q)).json()

            if q in res_json:
                exchange = res_json[q][0]

                market_price.update({symbol: exchange})

        return market_price

    def get_summary(self):
        asset_list = self.get_market_assets()

        market_price = self.get_market_price(asset_list)

        summary = {}
        for m in self.my_market:
            m.make_summary(summary, market_price)

        return summary

"""
[
 {"market":"KRW-BTC","trade_date_kst":"20200123","trade_time_kst":"222413","trade_price":9659000.0}
,{"market":"KRW-ETH","trade_date_kst":"20200123","trade_time_kst":"222400","trade_price":187000.0}
,{"market":"KRW-XRP","trade_date_kst":"20200123","trade_time_kst":"222413","trade_price":261.0}
]
"""
