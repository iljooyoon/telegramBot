from connection.http import Http
import utils.fileutils as fileutils


class Exchange:
    def __init__(self, name, setting_file, asset_file):
        self.name = name
        self.conn = Http()

        self.valid = True
        self.access_key = None
        self.secret_key = None
        self.addresses = None
        self.asset_list = {}
        self.asset_data = {}

        self.load_settings(setting_file)
        self.load_assets(asset_file)

    def load_settings(self, setting_file):
        setting = fileutils.read_json_file(setting_file)

        if self.name not in setting:
            self.valid = False
            return

        exchange = setting[self.name]

        if self.name == 'Wallet':
            if len(exchange) == 0:
                self.valid = False
                return

            self.addresses = exchange
        else:
            if 'access_key' not in exchange or 'secret_key' not in exchange:
                self.valid = False
                return

            self.access_key = exchange['access_key']
            self.secret_key = exchange['secret_key']

            if self.access_key == "" or self.secret_key == "":
                self.valid = False
                return

    def load_assets(self, asset_file):
        asset_data = fileutils.read_json_file(asset_file)

        if self.name not in asset_data:
            return

        self.asset_data = asset_data[self.name]

    def get_wallets(self):
        raise NotImplementedError

    def get_market_price(self, symbols):
        raise NotImplementedError

    def check_valid(self):
        return self.valid

    def make_summary(self, summary, market_price):
        for cur, count in self.asset_data.items():
            if self.asset_list.get(cur):
                self.asset_list[cur] += count
            else:
                self.asset_list[cur] = count

        for cur, count in self.asset_list.items():
            if count == 0:
                continue

            if cur != 'KRW':
                if market_price.get(cur) is None:
                    if summary.get('others') is None:
                        summary['others'] = {}
                    if summary['others'].get(cur) is None:
                        summary['others'][cur] = {'count': 0}
                    summary['others'][cur]['count'] += count

                    continue

                krw = count * market_price[cur]
            else:
                krw = count

            # 소액은 제거.
            if abs(krw) < 100:
                continue

            if summary.get(self.name) is None:
                summary[self.name] = 0
            summary[self.name] += krw

            if summary.get(cur) is None:
                if cur == 'KRW':
                    summary[cur] = 0
                else:
                    summary[cur] = {'KRW': 0, 'count': 0, 'price': market_price[cur]}

            if cur == 'KRW':
                summary[cur] += krw
            else:
                summary[cur]['KRW'] += krw
                summary[cur]['count'] += count

            if summary.get('total') is None:
                summary['total'] = 0
            summary['total'] += krw
