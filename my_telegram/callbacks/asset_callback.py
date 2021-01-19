import math

from request import MarketRequest
from . import ICallback


class AssetCallback(ICallback):
    def __init__(self, button_name, callback_name=None):
        super(AssetCallback, self).__init__(button_name, callback_name)

        self.mr = MarketRequest('./settings/settings.json', './settings/asset.json')

    def text(self):
        summary = self.mr.get_summary()

        text = ''.join(list(self.printout(summary)))

        return text

    @staticmethod
    def printout(json_data):
        sorted_list = sorted(json_data.items(),
                             key=lambda kv: 'z' if kv[0] == 'total' else
                                            'yx0' if kv[0] == 'Wallet' else
                                            'yx1' if kv[0] == 'Upbit' else
                                            'yx2' if kv[0] == 'Bithumb' else
                                            'yx3' if kv[0] == 'Bitfinex' else kv[0]
                             )

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
                    yield '{0:>{width}} {1} ({2} 원)\n'.format(format(num, ',{}'.format(precision)),
                                                              unit,
                                                              price,
                                                              width=width)
                else:
                    yield '\n'
                    for others_dict in sub_dict:
                        yield format(others_dict, ' <{}'.format(4 if len(others_dict) <= 4 else 8))
                        yield ': '
                        num = sub_dict[others_dict]['count']
                        precision = '.{}f'.format(max(6 - int(math.log(abs(num), 10)), 0))
                        unit = '개'
                        width = 18
                        yield '{0:>{width}} {1}\n'.format(format(num, ',{}'.format(precision)), unit, width=width)
            else:
                num = data[1]
                precision = '.0f'
                unit = '원'
                width = 12
                yield '{0:>{width}} {1}\n'.format(format(num, ',{}'.format(precision)), unit, width=width)
