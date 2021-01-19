from utils import fileutils
import argparse

from my_telegram.telegram_bot import TelegramBot
from my_telegram.callbacks import *

parser = argparse.ArgumentParser(description='마켓 자산 현황 조회')

parser.add_argument("--serverMode", help='listen message when True', type=bool, default=True)

args = parser.parse_args()


if __name__ == "__main__":
    # import logging
    # default_logger = logging.getLogger()
    # default_logger.setLevel(logging.DEBUG)
    # import sys
    # handler = logging.StreamHandler(sys.stdout)
    # default_logger.addHandler(handler)
    tele_json = fileutils.read_json_file('./settings/telegram.json')

    my_token = tele_json['token']

    callback_function = [
        AssetCallback('자산'),
        AssetCallbackBeta('자산(beta)'),
        ExchangeRateCallback('환율'),
        OilPriceCallback('유가'),
        StockCallback('증시')
    ]

    bot = TelegramBot(token=my_token, callback_function=callback_function, use_context=True)
    bot.start_polling(read_latency=0.001, clean=True)
    bot.idle()
