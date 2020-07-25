from connection.http import http
import utils.fileutils as fileutils


class Exchange:
    def __init__(self, name):
        self.name = name
        self.conn = http()

        self.valid = True
        self.access_key = None
        self.secret_key = None
        self.addresses = None

    def load_settings(self, setting_file):
        setting = fileutils.read_json_file(setting_file)

        if self.name not in setting:
            self.valid = False
            return

        exchange = setting[self.name]

        if self.name == 'wallet':
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

    def get_wallets(self):
        raise NotImplementedError

    def get_market_price(self, symbols):
        raise NotImplementedError

    def check_valid(self):
        return self.valid
