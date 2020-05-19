import requests
import base64
import time
import json
requests.packages.urllib3.disable_warnings()

class BaiduOCR():
    __accessTokenUrl = 'https://aip.baidubce.com/oauth/2.0/token'
    __accurateUrl = 'https://aip.baidubce.com/rest/2.0/ocr/v1/accurate'

    def __init__(self, apiKey, secretKey):
        self._apiKey = apiKey
        self._secretKey = secretKey
        self._authObj = {}
        self.__client = requests
        self.__connectTimeout = 60.0
        self.__socketTimeout = 60.0
        self._proxies = {}

    def accurate(self, image):
        data = {}
        data['image'] = base64.b64encode(image).decode()
        return self._request(self.__accurateUrl, data)

    def _request(self, url, data, headers=None):
        try:
            authObj = self._auth()
            params = {}
            params['access_token'] = authObj['access_token']
            response = self.__client.post(url, data=data, params=params, headers=headers,
                                          verify=False, timeout=(self.__connectTimeout,
                                                                 self.__socketTimeout,),
                                          proxies=self._proxies
                                          )
            obj = json.loads(response.content)
            if obj.get('error_code', '') == 110:
                authObj = self._auth(True)
                params['access_token'] = authObj['access_token']
                response = self.__client.post(url, data=data, params=params, headers=headers,
                                              verify=False, timeout=(self.__connectTimeout,
                                                                     self.__socketTimeout,),
                                              proxies=self._proxies
                                              )
                obj = json.loads(response.content)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as e:
            return {
                'error_msg': 'connection or read data timeout',
            }
        return obj

    def _auth(self, refresh=False):
        if not refresh:
            tm = self._authObj.get('time', 0) - 30
            if tm > int(time.time()):
                return self._authObj

        obj = self.__client.get(self.__accessTokenUrl, verify=False, params={
            'grant_type': 'client_credentials',
            'client_id': self._apiKey,
            'client_secret': self._secretKey,
        }, timeout=(
            self.__connectTimeout,
            self.__socketTimeout,
        ), proxies=self._proxies).json()

        obj['time'] = int(time.time())
        self._authObj = obj
        return obj


if __name__ == '__main__':
    ocr = BaiduOCR(apiKey='hhkcKD0CTP40VD6vxW92FOPt',
                   secretKey='gx59LaFgRwMu0g31rilZeG4VnkCIFM9H'
                   )

    imgpath = '../static/standard_images/个人独资企业营业执照.png'
    with open(imgpath, 'rb') as fs:
        image = fs.read()
        result = ocr.accurate(image)
        print('\n'.join([item['words'] for item in result['words_result']]))