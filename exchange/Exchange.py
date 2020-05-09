from connection.http import http
import utils.fileutils as fileutils


class Exchange:
    def __init__(self, name):
        self.name = name
        self.conn = http()

        self.valid = True
        self.access_key = None
        self.secret_key = None

    def load_settings(self, setting_file):
        try:
            setting = fileutils.read_json_file(setting_file)

            self.access_key = setting[self.name]['access_key']
            self.secret_key = setting[self.name]['secret_key']
        except KeyError:
            self.valid = False

    def get_wallets(self):
        raise NotImplementedError

    def get_market_price(self, symbols):
        raise NotImplementedError

    def check_valid(self):
        return self.valid
