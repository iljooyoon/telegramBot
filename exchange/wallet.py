import requests
import time
from bs4 import BeautifulSoup

from exchange.Exchange import Exchange


class Wallet(Exchange):
    def __init__(self, setting_file, asset_file, beta):
        super(Wallet, self).__init__(self.__class__.__name__, setting_file, asset_file)

        self.beta = beta

        if self.beta:
            self.host = 'https://zapper.fi'
            self.account_balance_url = 'https://zapper.fi/api/account-balance/{}?addresses={}'
        else:
            self.host = "https://api.ethplorer.io"

        self.market_price = {}
        self.backup_assets = {}

    def parsing_script(self, sess, scripts):
        api_key = None
        types = None

        for s in scripts:
            if s.attrs.get('src'):
                src: str = s.attrs.get('src')

                if not src.endswith('.js'):
                    continue

                js = sess.get(self.host + src)

                # get api-key
                api_key_idx = max(js.text.find('"api-key"'), js.text.find("'api-key'"))

                if api_key_idx >= 0:
                    api_key_idx += 9
                    api_key_str_idx = js.text.find('"', api_key_idx) + 1
                    api_key_end_idx = js.text.find('"', api_key_str_idx)
                    api_key = js.text[api_key_str_idx:api_key_end_idx]

                # get types
                types_idx = max(js.text.find('AAVE="aave"'), js.text.find("AAVE='aave'"))

                if types_idx >= 0:
                    types = js.text[types_idx:js.text.find("}", types_idx)].split(',')

        return api_key, types

    def get_wallets_beta(self):
        sess = requests.session()

        res = sess.get(self.host)

        soup = BeautifulSoup(res.text, 'html5lib')
        scripts = soup.find_all('script')

        api_key, types = self.parsing_script(sess, scripts)

        if not api_key or not types:
            return 0

        all_assets = self.get_all_assets(api_key, types)

        # wallet
        wallet = get_wallet(all_assets)

        # deposits
        deposits = get_deposits(all_assets)

        # investments
        investments = get_investments(all_assets)

        # liquiditypools
        liquiditypools = get_liquiditypools(all_assets)

        # farming
        farming = get_farming(all_assets)

        # options
        options = get_options(all_assets)

        # debt
        debt = get_debt(all_assets)

        # total asset : wallet + deposits + investments + liquiditypools + farming + options
        total_asset = wallet + deposits + investments + liquiditypools + farming + options
        # nettotal : total asset - debt
        nettotal = total_asset - debt

        self.asset_list = {}
        self.market_price = {}

        self.asset_list.setdefault('Total Assets', total_asset)
        self.asset_list.setdefault('Net Worth', nettotal)
        self.asset_list.setdefault('Total Debt', debt)
        self.asset_list.setdefault('Wallet', wallet)
        self.asset_list.setdefault('Deposits', deposits)
        self.asset_list.setdefault('Yield Farming', farming)
        self.asset_list.setdefault('Debt', debt)

        exchange = requests.get('https://earthquake.kr:23490/query/USDKRW').json()['USDKRW'][0]

        for key in self.asset_list.keys():
            self.market_price[key] = exchange

        return [*self.asset_list, *self.asset_data]

    def get_all_assets(self, api_key, types):
        all_assets = {}

        headers = {
            'api-key': api_key,
            'referer': 'https://zapper.fi/dashboard',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
        }

        for address in self.addresses:
            addr = address['addr'].lower()
            for t in types:
                t = t.split('=')[1].replace('"', '').replace("'", "")
                res = requests.get(self.account_balance_url.format(t, addr), headers=headers)

                try_cnt = 0

                while res.status_code != '200':
                    try_cnt += 1
                    if try_cnt > 0:
                        break
                    time.sleep(10)
                    print('retry.. {}'.format(t))
                    res = requests.get(self.account_balance_url.format(t, addr), headers=headers)

                if res.status_code == 200:
                    res_json = res.json()
                    all_assets[t] = res_json.get(addr, res_json.get(addr.lower(), res_json.get(addr.upper())))
                    self.backup_assets[t] = all_assets[t]
                else:
                    # TODO 에러처리
                    all_assets[t] = self.backup_assets[t]
                    print(t, res.status_code, res.reason, res.text)

        return all_assets

    def get_wallets(self):
        if self.beta:
            return self.get_wallets_beta()

        end_point = "/getAddressInfo/{addr}?apiKey={apiKey}"

        self.asset_list = {}
        self.market_price = {}

        for address in self.addresses:
            res = self.conn.get(self.host, end_point.format(addr=address['addr'], apiKey=address['apiKey']))

            if res.status_code == 200:
                response = res.json()

                cur = 'ETH'
                count = response['ETH']['balance']

                self.asset_list.setdefault(cur, count)

                for token in response['tokens']:
                    token_info = token['tokenInfo']
                    if 'symbol' in token_info and token_info['price'] is not False:
                        cur = token_info['symbol']
                        count = token['balance'] / 10**int(token_info['decimals'])

                        self.asset_list.setdefault(cur, count)

                        if token_info['price'] is not False and token_info['price']['currency'] == 'USD':
                            exchange = requests.get('https://earthquake.kr:23490/query/USDKRW').json()['USDKRW'][0]

                            self.market_price[cur] = token_info['price']['rate'] * exchange

        return [*self.asset_list, *self.asset_data]

    def get_market_price(self, symbols):
        return self.market_price

    def make_summary(self, summary, market_price):
        if self.beta:
            for cur, count in self.asset_list.items():
                if count == 0:
                    continue

                krw = count * market_price[cur]

                # 총 금액에 합산.
                if cur == 'Net Worth':
                    if summary.get(self.name) is None:
                        summary[self.name] = 0
                    summary[self.name] += krw

                    if summary.get('total') is None:
                        summary['total'] = 0
                    summary['total'] += krw

                if summary.get(cur) is None:
                    summary[cur] = 0

                summary[cur] += krw
        else:
            super().make_summary(summary, market_price)


def get_wallet(all_assets):
    wallet = []

    # synthetix
    wallet.extend([s['balanceUSD'] for s in all_assets['synthetix']['synths']])

    wallet.append(all_assets['synthetix']['unlockedSnx'] * all_assets['synthetix']['usdToSnxPrice'])

    # tokens
    wallet.extend([t['balanceUSD'] for t in all_assets['tokens'] if not t['isStaked'] and not t['hide']])

    # bitcoin
    wallet.extend([b['balanceUSD'] for b in all_assets['bitcoin']])

    return sum(filter(lambda d: d >= 0.01, wallet))


def get_debt(all_assets):
    # debt
    debt = []
    # aave
    for a in all_assets['aave']['tokens']:
        debt.append(a['borrowBalanceUSD'])
    # aave-v2
    for a in all_assets['aave-v2']:
        debt.append(a['borrowBalanceUSD'])
    # compound
    for c in all_assets['compound']['borrowed']:
        debt.append(c['balanceUSD'])
    # cream
    for c in all_assets['cream']['borrowed']:
        debt.append(c['balanceUSD'])
    # dydx
    for c in all_assets['dydx']['borrowed']:
        debt.append(c['balanceUSD'])
    # maker
    for m in all_assets['maker']:
        debt.append(m['debtValue'])
    # synthetix
    debt.append(all_assets['synthetix']['debtBalance'])

    return sum(filter(lambda d: d >= 0.01, debt))


def get_deposits(all_assets):
    deposits = list()

    # synthetix
    deposits.append(
        {
            'balanceUSD': all_assets['synthetix']['usdToSnxPrice'] *
                   (all_assets['synthetix']['collateral'] - all_assets['synthetix']['unlockedSnx'])
        }
    )
    deposits.append(all_assets['synthetix']['iETHReward'])

    # dodo
    deposits.append({'balanceUSD': all_assets['dodo']['premineBalanceUSD']})
    deposits.extend(all_assets['dodo']['pools'])

    # esd
    deposits.extend(all_assets['esd']['wallet'])

    # dsd
    deposits.extend(all_assets['dsd']['wallet'])

    # dydx
    deposits.extend(all_assets['dydx']['supplied'])

    # compound
    deposits.extend(all_assets['compound']['supplied'])

    # aave
    deposits.extend(all_assets['aave']['tokens'])

    # idle
    deposits.extend(all_assets['idle'])

    # harvest
    deposits.extend(all_assets['harvest'])

    # yearn
    deposits.extend(all_assets['yearn'])

    # aave-v2
    deposits.extend(all_assets['aave-v2'])

    # badger
    deposits.extend(all_assets['badger']['deposits'])

    # bancor
    deposits.extend(all_assets['bancor']['deposits'])

    # barnbridge
    deposits.extend(all_assets['barnbridge'])

    # defisaver
    deposits.extend(all_assets['defisaver'])

    # cover
    deposits.extend(all_assets['cover']['deposits'])

    # cream
    deposits.extend(all_assets['cream']['staked'])
    deposits.extend(all_assets['cream']['supplied'])

    # other
    deposits.extend(all_assets['other'])

    # tokens
    deposits.extend(filter(lambda t: t['isStaked'], all_assets['tokens']))

    # filter
    def filter_cond(d):
        return d['balanceUSD'] >= 0.01 or ('label' in d and (d['label'] == 'Locked CRV' or d['label'] == 'Vesting YAM'))
    return sum(map(lambda d: d['balanceUSD'], filter(filter_cond, deposits)))


def get_investments(all_assets):
    return 0


def get_liquiditypools(all_assets):
    liquiditypools = []

    # curve
    liquiditypools.extend(all_assets['curve'])
    # mooniswap
    liquiditypools.extend(all_assets['mooniswap'])
    # uniswap
    liquiditypools.extend(all_assets['uniswap']['pools'])
    # uniswap_v2
    liquiditypools.extend(all_assets['uniswap-v2'])

    # filter balanceUSD >= .01
    liquiditypools = filter(lambda l: l['balanceUSD'] >= 0.01, liquiditypools)

    # sum balanceUSD
    return sum(map(lambda l: l['balanceUSD'], liquiditypools))


def get_farming(all_assets):
    farming = list()

    # compound
    farming.append(all_assets['compound']['rewards']['compBalanceUSD'])
    # cream
    farming.append(all_assets['cream']['rewards']['creamBalanceUSD'])
    # tokens
    for t in all_assets['tokens']:
        if t['isStaked'] and t['rewardToken'] == 'Y Curve':
            farming.append(t['balanceUSD'])

    return sum(farming)


def get_options(all_assets):
    return 0
