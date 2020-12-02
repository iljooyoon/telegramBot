import traceback
import time
import math
import json
from utils import fileutils, JsonEncoder
from request import MarketRequest
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
    sorted_list = sorted(json_data.items(), key=lambda kv: 'z' if kv[0] == 'total' else 'a' if kv[0] == 'others' else kv[0])
    for data in sorted_list:
        yield format(data[0], '<{}'.format(4 if len(data[0]) <= 4 else 8))
        yield ': '
        if isinstance(data[1], dict):
            sub_dict = data[1]

            if 'KRW' in sub_dict:
                num = sub_dict['KRW']
                precision = '.0f'
                unit = '원'
                width = 12
                yield '{0:>{width}} {1}\n'.format(format(num, ',{}'.format(precision)), unit, width=width)

                num = sub_dict['count']
                if int(num) == num:
                    precision = '.0f'
                else:
                    precision = '.{}f'.format(max(6 - int(math.log(num, 10)), 0))

                price = sub_dict['price']
                if int(price) == price:
                    price = format(price, ',{}'.format('.0f'))
                else:
                    price = format(price, ',{}'.format('.2f'))

                unit = '개'
                width = 18
                yield '{0:>{width}} {1} ({2} 원)\n'.format(format(num, ',{}'.format(precision)), unit, price, width=width)
            else:
                yield '\n'
                for others_dict in sub_dict:
                    yield format(others_dict, ' <{}'.format(4 if len(others_dict) <= 4 else 8))
                    yield ': '
                    num = sub_dict[others_dict]['count']
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


def send_one_request(chat_id, update=None, context=None, bot=None):
    if update and context:
        show_markup = get_markup(update, context)

        # 텔레그램에서 나에게(chat_id) 메시지(text)를 보낸다.
        if update.callback_query.data == '자산':
            try:
                mr = MarketRequest('./settings/settings.json', './settings/asset.json')

                summary = mr.get_summary()

                text = ''.join(list(printout(summary)))
            except RuntimeError as e:
                text = '{}({})'.format(e.args[0], e.args[1])
            except Exception:
                traceback.print_exc()
                text = 'unknown error'

            # text = json.dumps(summary, sort_keys=True, indent=2, separators=(',', ': '), cls=JsonEncoder.MyEncoder)
            context.bot.send_message(text=text,
                                     chat_id=update.callback_query.message.chat_id,
                                     message_id=update.callback_query.message.message_id, reply_markup=show_markup)
        elif update.callback_query.data == '환율':
            res = requests.get('https://earthquake.kr:23490/query/USDKRW')

            if res.status_code == 200:
                context.bot.send_message(text="원/달러 환율: {0} 전일 대비 {1:.2f} ({2:.2f}%)".format(*res.json()['USDKRW'][0:3]),
                                         chat_id=update.callback_query.message.chat_id,
                                         message_id=update.callback_query.message.message_id, reply_markup=show_markup)
        elif update.callback_query.data == '유가':
            res = requests.get('https://finance.naver.com/marketindex/worldOilDetail.nhn?marketindexCd=OIL_CL')

            if res.status_code == 200:
                html = res.text
                soup = BeautifulSoup(html, 'html5lib')
                text = soup.select(".today")[0].text.replace('\t', '').replace('\n', ' ').replace('  ', ' ').\
                    replace('달러/배럴', '＄/bbl').strip()
                if '-' in text:
                    text = text.replace('전일대비  ', '📉 -')
                else:
                    text = text.replace('전일대비', '📈')
                context.bot.send_message(text=text,
                                         chat_id=update.callback_query.message.chat_id,
                                         message_id=update.callback_query.message.message_id, reply_markup=show_markup)
        elif update.callback_query.data == '증시':
            res = requests.get(
                'https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&ie=utf8&query=%EC%A3%BC%EC%9A%94%EC%A6%9D%EC%8B%9C&mra=bjY3')

            if res.status_code == 200:
                html = res.text
                soup = BeautifulSoup(html, 'html5lib')
                stock = soup.select('.dtcon_lst.wst dl')

                line = list()

                tokens = stock_tokenizer(stock[0].text)
                line.append(' '.join(tokens[1:3]))
                line.append(' '.join(tokens[0:1] + tokens[3:]))

                tokens = stock_tokenizer(stock[1].text)
                line.append(' '.join(tokens[0:1] + tokens[3:]))

                tokens = stock_tokenizer(stock[2].text)
                line.append(' '.join(tokens[1:2]))
                line.append(' '.join(tokens[0:1] + tokens[3:]))

                tokens = stock_tokenizer(stock[5].text)
                line.append(' '.join(tokens[0:1] + tokens[3:]))

                text = '\n'.join(line)

                context.bot.send_message(text=text,
                                         chat_id=update.callback_query.message.chat_id,
                                         message_id=update.callback_query.message.message_id, reply_markup=show_markup)
    else:
        mr = MarketRequest('./settings/settings.json', './settings/asset.json')

        summary = mr.get_summary()

        log_file_name = './logs/' + time.strftime('%Y.%m.%d %H %M', time.localtime(time.time())) + '.log'
        fileutils.write_json_file(log_file_name, summary, cls=JsonEncoder.MyEncoder)

        bot.send_message(chat_id=chat_id,
                         text=json.dumps(summary, sort_keys=True, indent=2, separators=(',', ': '), cls=JsonEncoder.MyEncoder))
# print(json.dumps(summary, sort_keys=True, indent=2, separators=(',', ': '), cls=JsonEncoder.MyEncoder))


def stock_tokenizer(text):
    import re
    idx = re.search('[0-9]', text).regs[0][0]
    text = text[:idx] + ' ' + text[idx:]
    return text.replace('전일대비하락', '📉 ').replace('전일대비상승', '📈 ').strip().split()


if __name__ == "__main__":
    # import logging
    # default_logger = logging.getLogger()
    # default_logger.setLevel(logging.DEBUG)
    # import sys
    # handler = logging.StreamHandler(sys.stdout)
    # default_logger.addHandler(handler)
    tele_json = fileutils.read_json_file('./settings/telegram.json')

    my_token = tele_json['token']
    chat_id = tele_json['chat_id']

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
            if chat_id != update.effective_user.id or chat_id != update.effective_chat.id:
                print(update)
            send_one_request(chat_id, update, context)

        updater.dispatcher.add_handler(CallbackQueryHandler(callback_get))

        updater.start_polling(read_latency=0.001, clean=True)
        updater.idle()

    else:
        bot = telegram.Bot(my_token)

        send_one_request(chat_id, bot=bot)
