from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class ReplyMarkup:
    def __init__(self, button_name, callback_name=None, n_cols=2, header_buttons=None, footer_buttons=None):
        self.n_cols = n_cols
        self.header_buttons = header_buttons
        self.footer_buttons = footer_buttons

        button_callbacks = zip(button_name, callback_name) if callback_name else zip(button_name, button_name)

        buttons = [InlineKeyboardButton(bn, callback_data=cn) for bn, cn in button_callbacks]
        self.reply_markup = self.build_menu(buttons)

    def build_menu(self, buttons):
        menu = [buttons[i:i + self.n_cols] for i in range(0, len(buttons), self.n_cols)]
        if self.header_buttons:
            menu.insert(0, self.header_buttons)
        if self.footer_buttons:
            menu.append(self.footer_buttons)
        return InlineKeyboardMarkup(menu)

    def get_reply_markup(self):
        return self.reply_markup
