import json
import requests


class KAKAO:
    def __init__(self):
        self.host = 'kapi.kakao.com'
        self.auth_host = 'kauth.kakao.com'

        with open('KAKAO_settings.json', 'r') as setting_file:
            settings = json.load(setting_file)

        self.client_id = settings['client_id']
        self.token_info = settings['token_info']

    def _build_url(self, end_point, protocol='https', auth=False):
        return protocol + '://' + (self.auth_host if auth else self.host) + end_point

    def _token_update(self, token):
        self.token_info.update(token)
        with open('KAKAO_settings.json', 'w') as setting:
            json.dump({
                'client_id': self.client_id,
                'token_info': self.token_info
            }, setting, indent=2)

    def get_access_token_info(self):
        end_point = '/v1/user/access_token_info'
        headers = {
            'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        return self._get(self._build_url(end_point), True, headers)

    def refresh_token(self):
        end_point = '/oauth/token'
        headers = {
            'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'
        }

        body = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'refresh_token': self.token_info['refresh_token']
        }

        token = self._post(self._build_url(end_point, auth=True), use_authorization=False, headers=headers, body=body)

        self._token_update(token)

    def send_to_me_text(self, message):
        end_point = '/v2/api/talk/memo/default/send'

        template_object = {
            'object_type': 'text',
            'text': message,
            'link': {
                'web_url': 'https://www.naver.com'
            }
        }

        template_object = json.dumps(template_object)

        body = {
            'template_object': template_object
        }

        self._post(self._build_url(end_point), use_authorization=True, body=body)

    def get_friends_list(self):
        end_point = '/v1/api/talk/friends'
        params = {
            'secure_resource': False,
            'offset': 0,
            'limit': 10,
            'order': 'asc',
            'friend_order': 'favorite'
        }

        return self._get(self._build_url(end_point), use_authorization=True, params=params)

    def send_to_friends_text(self, message):
        end_point = '/v1/api/talk/friends/message/default/send'

        template_object = {
            'object_type': 'text',
            'text': message,
            'link': {
                'web_url': 'https://www.naver.com'
            }
        }

        template_object = json.dumps(template_object)

        body = {
            # 친구 목록 API를 통해 얻은 사용자 uuid 값, 최대 5개
            'receiver_uuids': [''],
            'template_object': template_object
        }
        return self._post(self._build_url(end_point), use_authorization=True, body=body)

    def _get(self, url, use_authorization, headers=None, params=None, body=None):
        return self._send('get', url, use_authorization, headers, params, body)

    def _post(self, url, use_authorization, headers=None, params=None, body=None):
        return self._send('post', url, use_authorization, headers, params, body)

    def _send(self, method, url, use_authorization, headers=None, params=None, body=None):
        if use_authorization:
            if headers is None:
                headers = dict()

            headers.update({'Authorization': '{} {}'.format(self.token_info['token_type'],
                                                            self.token_info['access_token'])})

        res = requests.request(method=method, url=url, headers=headers, params=params, data=body)

        text = json.loads(res.text)
        if res.status_code != 200:
            print("status_code: {}\nerror_msg: {}\nerror_code: {}".format(res.status_code, text.msg, text.code))
            exit(0)

        return text


def main():
    messenger = KAKAO()
    info = messenger.get_access_token_info()
    print(info)
    # messenger.refresh_token()
    # messenger.send_to_me_text("아무말이나 보내볼까?")
    res = messenger.get_friends_list()
    print(res)
    # send_to_friends_text("아무말이나 보내볼까?")


if __name__ == "__main__":
    main()
