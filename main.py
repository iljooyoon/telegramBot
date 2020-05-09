import time
import json
import JsonEncoder
import fileutils
from request import MargetRequest
import argparse
import telegram
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import requests
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(description='마켓 자산 현황 조회')

parser.add_argument("--serverMode", help='listen message when True', type=bool, default=True)

args = parser.parse_args()


def printout(json_data):
    sorted_list = sorted(json_data.items(), key=lambda kv: 'z' if kv[0] == 'total' else kv[0])
    for data in sorted_list:
        yield format(data[0], '<{}'.format(4 if len(data[0]) <= 4 else 8))
        yield ': '
        if isinstance(data[1], dict):
            sub_dict = data[1]

            num = sub_dict['KRW']
            precision = '.0f'
            unit = '원'
            width = 12
            yield '{0:>{width}} {1}\n'.format(format(num, ',{}'.format(precision)), unit, width=width)

            num = sub_dict['count']
            import math
            precision = '.{}f'.format(max(6 - int(math.log(num, 10)), 0))
            unit = '개'
            width = 18
            yield '{0:>{width}} {1}\n'.format(format(num, ',{}'.format(precision)), unit, width=width)
        else:
            num = data[1]
            precision = '.0f'
            unit = '원'
            width = 12
            yield '{0:>{width}} {1}\n'.format(format(num, ',{}'.format(precision)), unit, width=width)


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def get_markup(update, context):
    show_list = list()

    show_list.append(InlineKeyboardButton("자산", callback_data="자산"))
    show_list.append(InlineKeyboardButton("환율", callback_data="환율"))
    show_list.append(InlineKeyboardButton("유가", callback_data="유가"))
    show_list.append(InlineKeyboardButton("증시", callback_data="증시"))
    show_markup = InlineKeyboardMarkup(build_menu(show_list, n_cols=2))  # make markup

    return show_markup


def send_one_request(update=None, context=None, bot=None):
    if update and context:
        show_markup = get_markup(update, context)

        # 텔레그램에서 나에게(chat_id) 메시지(text)를 보낸다.
        if update.callback_query.data == '자산':
            mr = MargetRequest('./settings.json', './asset.json')

            mr.get_exchange_rate()

            mr.get_market_assets()

            summary = mr.get_summary()

            text = ''.join(list(printout(summary)))
            # text = json.dumps(summary, sort_keys=True, indent=2, separators=(',', ': '), cls=JsonEncoder.MyEncoder)
            context.bot.send_message(text=text,
                                     chat_id=update.callback_query.message.chat_id,
                                     message_id=update.callback_query.message.message_id, reply_markup=show_markup)
        elif update.callback_query.data == '환율':
            res = requests.get('https://earthquake.kr:23490/query/USDKRW')

            if res.status_code == 200:
                context.bot.send_message(text=res.json()['USDKRW'][0],
                                         chat_id=update.callback_query.message.chat_id,
                                         message_id=update.callback_query.message.message_id, reply_markup=show_markup)
        elif update.callback_query.data == '유가':
            res = requests.get('https://finance.naver.com/marketindex/worldOilDetail.nhn?marketindexCd=OIL_CL')

            if res.status_code == 200:
                html = res.text
                soup = BeautifulSoup(html, 'html5lib')
                context.bot.send_message(text=soup.select(".today")[0].text.replace('\t', '').replace('\n', ' ').strip(),
                                         chat_id=update.callback_query.message.chat_id,
                                         message_id=update.callback_query.message.message_id, reply_markup=show_markup)
        elif update.callback_query.data == '증시':
            res = requests.get('https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&ie=utf8&query=%EC%A3%BC%EC%9A%94%EC%A6%9D%EC%8B%9C&mra=bjY3')

            if res.status_code == 200:
                html = res.text
                soup = BeautifulSoup(html, 'html5lib')
                stock = soup.select('.dtcon_lst.wst dl')
                text = stock[0].text.rstrip() + "\n" + stock[1].text.rstrip() + "\n" + stock[2].text.rstrip() + "\n" + stock[5].text.rstrip()
                context.bot.send_message(text=text,
                                         chat_id=update.callback_query.message.chat_id,
                                         message_id=update.callback_query.message.message_id, reply_markup=show_markup)
    else:
        mr = MargetRequest('./settings.json', './asset.json')

        mr.get_exchange_rate()

        mr.get_market_assets()

        summary = mr.get_summary()

        log_file_name = './logs/' + time.strftime('%Y.%m.%d %H %M', time.localtime(time.time())) + '.log'
        fileutils.write_json_file(log_file_name, summary, cls=JsonEncoder.MyEncoder)

        bot.send_message(chat_id=399560770,
            text=json.dumps(summary, sort_keys=True, indent=2, separators=(',', ': '), cls=JsonEncoder.MyEncoder))
# print(json.dumps(summary, sort_keys=True, indent=2, separators=(',', ': '), cls=JsonEncoder.MyEncoder))


if __name__ == "__main__":
    # import logging
    # default_logger = logging.getLogger()
    # default_logger.setLevel(logging.DEBUG)
    # import sys
    # handler = logging.StreamHandler(sys.stdout)
    # default_logger.addHandler(handler)
    my_token = '949243689:AAERKkrSP-tTA23TnEVFluVW9lhjjZ6ugjE'

    if args.serverMode:
        updater = Updater(my_token, use_context=True)

        def get_command(update, context):
            show_markup = get_markup(update, context)
            update.message.reply_text("원하는 값을 선택하세요", reply_markup=show_markup)

        updater.dispatcher.add_handler(CommandHandler('get', get_command))

        def get_message(update, context):
            show_markup = get_markup(update, context)
            update.message.reply_text("원하는 값을 선택하세요", reply_markup=show_markup)

        updater.dispatcher.add_handler(MessageHandler(Filters.text, get_message))

        def error_callback(update, context):
            print(context.error)

        updater.dispatcher.add_error_handler(error_callback)

        def callback_get(update, context):
            send_one_request(update, context)

        updater.dispatcher.add_handler(CallbackQueryHandler(callback_get))

        updater.start_polling(read_latency=0.001, clean=True)
        updater.idle()

    else:
        bot = telegram.Bot(my_token)

        send_one_request(bot=bot)
