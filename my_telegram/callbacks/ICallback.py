from abc import abstractmethod


class ICallback:
    def __init__(self, button_name, callback_name=None):
        self.btn_name = button_name
        self.cb_name = callback_name if callback_name else button_name

    def __call__(self):
        return self.text()

    @abstractmethod
    def text(self):
        pass

    def button_name(self):
        return self.btn_name

    def callback_name(self):
        return self.cb_name
