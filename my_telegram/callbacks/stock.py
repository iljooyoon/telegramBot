import re
import requests
from bs4 import BeautifulSoup

from . import ICallback


class StockCallback(ICallback):
    def __init__(self, button_name, callback_name=None):
        super(StockCallback, self).__init__(button_name, callback_name)

        self.URL = 'https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&ie=utf8&query=주요증시&mra=bjY3'

    def text(self):
        res = requests.get(self.URL)

        if res.status_code == 200:
            html = res.text
            soup = BeautifulSoup(html, 'html5lib')
            stock = soup.select('.dtcon_lst.wst dl')

            line = list()

            tokens = self.stock_tokenizer(stock[0].text)
            line.append(' '.join(tokens[1:3]))
            line.append(' '.join(tokens[0:1] + tokens[3:]))

            tokens = self.stock_tokenizer(stock[1].text)
            line.append(' '.join(tokens[0:1] + tokens[3:]))

            tokens = self.stock_tokenizer(stock[2].text)
            line.append(' '.join(tokens[1:2]))
            line.append(' '.join(tokens[0:1] + tokens[3:]))

            tokens = self.stock_tokenizer(stock[5].text)
            line.append(' '.join(tokens[0:1] + tokens[3:]))

            return '\n'.join(line)

    @staticmethod
    def stock_tokenizer(text):
        idx = re.search('[0-9]', text).regs[0][0]
        text = text[:idx] + ' ' + text[idx:]
        return text.replace('전일대비하락', '📉 ').replace('전일대비상승', '📈 ').strip().split()
