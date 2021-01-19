import requests
from bs4 import BeautifulSoup

from . import ICallback


class OilPriceCallback(ICallback):
    def __init__(self, button_name, callback_name=None):
        super(OilPriceCallback, self).__init__(button_name, callback_name)

        self.URL = 'https://finance.naver.com/marketindex/worldOilDetail.nhn?marketindexCd=OIL_CL'

    def text(self):
        res = requests.get(self.URL)

        if res.status_code == 200:
            html = res.text
            soup = BeautifulSoup(html, 'html5lib')
            text = soup.select(".today")[0].text.replace('\t', '').replace('\n', ' ').replace('  ', ' '). \
                replace('달러/배럴', '＄/bbl').strip()
            if '-' in text:
                text = text.replace('전일대비  ', '📉 -')
            else:
                text = text.replace('전일대비', '📈')

            return text
        else:
            # TODO
            return ''
