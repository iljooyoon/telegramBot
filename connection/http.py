import requests


class Http:
    def get(self, host, end_point, headers=None, params=None, **kwargs):
        return self.request('get', host, end_point, headers, params, **kwargs)

    def post(self, host, end_point, headers=None, body=None, **kwargs):
        return self.request('post', host, end_point, headers, body=body, **kwargs)

    @staticmethod
    def request(method, host, end_point, headers=None, params=None, body=None, **kwargs):
        url = host + end_point
        return requests.request(method=method, url=url, headers=headers, params=params, data=body, **kwargs)
