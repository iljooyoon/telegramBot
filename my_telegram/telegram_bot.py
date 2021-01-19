import traceback

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from my_telegram.reply_markup import ReplyMarkup


class TelegramBot(Updater):
    def __init__(self, token, callback_function, use_context=False):
        super(TelegramBot, self).__init__(token, use_context=use_context)

        button_name = [cf.button_name() for cf in callback_function]
        callback_name = [cf.callback_name() for cf in callback_function]
        self.callbacks = {name: func for name, func in zip(callback_name, callback_function)}

        # 텔레그램 봇이 기본적으로 출력하는 대화형 메시지
        self.reply_markup = ReplyMarkup(button_name, callback_name).get_reply_markup()

        # default 메시지 출력
        self.dispatcher.add_handler(CommandHandler('get', self.default_reply))
        self.dispatcher.add_handler(MessageHandler(Filters.text, self.default_reply))

        # 클릭한 버튼에 대한 정보 출력
        self.dispatcher.add_handler(CallbackQueryHandler(self.callback_get))

        # 에러 처리
        self.dispatcher.add_error_handler(self.error_callback)

    # noinspection PyUnusedLocal
    def default_reply(self, update, context):
        update.message.reply_text("원하는 값을 선택하세요", reply_markup=self.reply_markup)

    # noinspection PyUnusedLocal
    @staticmethod
    def error_callback(update, context):
        print(context.error)

    def callback_get(self, update, context):
        try:
            text = self.callbacks.get(update.callback_query.data)()
        except RuntimeError as e:
            text = '{}({})'.format(e.args[0], e.args[1])
        except Exception:
            traceback.print_exc()
            text = 'unknown error'

        # 텔레그램에서 나에게(chat_id) 메시지(text)를 보낸다.
        context.bot.send_message(text=text,
                                 chat_id=update.callback_query.message.chat_id,
                                 message_id=update.callback_query.message.message_id,
                                 reply_markup=self.reply_markup)
