import requests

from . import ICallback


class ExchangeRateCallback(ICallback):
    def __init__(self, button_name, callback_name=None):
        super(ExchangeRateCallback, self).__init__(button_name, callback_name)

        self.URL = 'https://earthquake.kr:23490/query/USDKRW'

    def text(self):
        res = requests.get(self.URL)

        if res.status_code == 200:
            return "원/달러 환율: {0} 전일 대비 {1:.2f} ({2:.2f}%)".format(*res.json()['USDKRW'][0:3])
        else:
            # TODO
            return ''
