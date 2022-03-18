#!/usr/bin/python3
# -*-coding: utf-8-*-

import json
from urllib import request
from urllib.request import Request, urlopen
import urllib.error
import time
import datetime
from dateutil.parser import parse

USERNAME = "user0XX@fiware-testbed.jp"
PASSWORD = "yourPassword"
CBHOST = "https://orion.fiware-testbed.jp"

FIWARESERVICE = "sakura"
FIWARESERVICEPATH = "/test"

IGNORELIST = []


class FiwareOrion:
    username = ""
    password = ""
    fiwareservice = ""
    fiwareservicepath = ""
    cb_host = ""
    token = ""

    def __init__(self, username, password, fiwareservice, fiwareservicepath, cb_host):
        self.username = username
        self.password = password
        self.cb_host = cb_host
        self.fiwareservice = fiwareservice
        self.fiwareservicepath = fiwareservicepath

    def mySendRequest(self, request):
        # requestを発行
        try:
            response = urllib.request.urlopen(request)
        except Exception as e:
            print(e)
            raise Exception(e)
        # except urllib.error.HTTPError as e:
        #    print('Error code : %s' % e.code)
        #    print('Error code : %s' % e.read())
        # except urllib.error.URLError as e:
        #    print('Error reason : %s' % e.reason)
        else:
            try:
                #print('Response header :\n%s' % response.info())
                return response.read()
            except Exception as e:
                print(e)
                raise Exception(e)
                # pass

    def createHeaders(self):

        headers = {
            'Fiware-Service': self.fiwareservice,
            'Fiware-ServicePath': self.fiwareservicepath
        }
        # トークンを取得する
        self.getAccessToken()
        # トークンヘッダを追加
        headers['X-Auth-Token'] = self.token['access_token']

        #logging.debug('Headers : %s' % headers)
        return headers

    def updateEntity(self, dataid, body):
        try:
            headers = self.createHeaders()
        except Exception as e:
            print(e)
            raise Exception(e)
            # return
        headers['Content-Type'] = 'application/json'

        url = self.cb_host + "/v2/entities" + "/" + dataid + "/" + "attrs"
        # print(url)

        try:
            request = urllib.request.Request(
                url, json.dumps(body).encode("utf-8"), headers)
            response = self.mySendRequest(request)
        except Exception as e:
            raise Exception(e)
        else:
            return(response)

    def getEntitiesByType(self, datatype):
        try:
            headers = self.createHeaders()
        except Exception as e:
            print(e)
            raise Exception(e)

        url = self.cb_host + "/v2/entities" + "?" + "type=" + datatype
        # print(url)

        try:
            request = urllib.request.Request(url, None, headers)
            response = self.mySendRequest(request)
        except Exception as e:
            raise Exception(e)
        else:
            return(response)

    def registerSubscription(self, subscription_body):

        try:
            headers = self.createHeaders()
        except Exception:
            #logging.debug('Create Headers error.')
            return
        headers['Content-Type'] = 'application/json'

        url = self.cb_host + "/v2/subscriptions"
        # logging.debug(url)
        # logging.debug(subscription_body)
        # logging.debug(headers)
        request = urllib.request.Request(url, json.dumps(
            subscription_body).encode("utf-8"), headers)
        return(self.mySendRequest(request))

    def getSubscriptions(self):
        url = self.cb_host + "/v2/subscriptions"
        headers = self.createHeaders()

        request = urllib.request.Request(url, None, headers)
        return(self.mySendRequest(request))

    def getSubscriptionCount(self, count, offset):
        url = self.cb_host + "/v2/subscriptions?offset=" + \
            str(offset) + "&limit=" + str(count) + "&options=count"
        headers = self.createHeaders()

        request = urllib.request.Request(url, None, headers)
        return(self.mySendRequest(request))

    def deleteSubscription(self, subscription_data):

        headers = self.createHeaders()

        subscriptionids = self.getSubscriptions()
        for id in subscriptionids:
            if id['notification']['http']['url'] == subscription_data['notification']['http']['url']:
                url = self.cb_host + "/v2/subscriptions" + "/" + id['id']
                request = urllib.request.Request(url, None, headers)
                request.get_method = lambda: 'DELETE'

                self.mySendRequest(request)
                return

    def deleteSubscriptionById(self, id):

        headers = self.createHeaders()

        url = self.cb_host + "/v2/subscriptions" + "/" + id
        print("=========")
        print(url)
        request = urllib.request.Request(url, None, headers)
        request.get_method = lambda: 'DELETE'

        return(self.mySendRequest(request))

    def getVersion(self):

        url = self.cb_host + "/version"
        headers = self.createHeaders()

        request = urllib.request.Request(url, None, headers)
        return (self.mySendRequest(request))

    def getAccessToken(self):

        if len(self.token) != 0:
            # print("token is not null")
            # print(self.token)
            return

        header = {'Content-Type': 'application/json'}
        data = {
            'username': self.username,
            'password': self.password
        }

        body = json.dumps(data).encode()

        url = self.cb_host + "/token"

        request = urllib.request.Request(url, body, header)
        self.token = json.loads(self.mySendRequest(request))

        #logging.debug('Acquired Token : %s' % self.token)
        #print('Acquired Token : %s' % self.token)


def send_message_to_slack(msg):
    # make slack message body
    send_data = {
        "channel": "target channel",
        "username": "sensor data checker",
        "text": msg
    }
    payload = "payload=" + json.dumps(send_data)
    request = Request(
        # target channel 
        "https://hooks.slack.com/services/XXXXX/YYYYYY/ZZZZZZZZZZZZZZZZZZZ",
        data=payload.encode("utf-8"),
        method="POST"
    )
    with urlopen(request) as response:
        response_body = response.read().decode("utf-8")


# ここより main
if __name__ == '__main__':

    # 全センサーから最新データを取得
    orion = FiwareOrion(USERNAME, PASSWORD, FIWARESERVICE,
                        FIWARESERVICEPATH, CBHOST)

    response = orion.getEntitiesByType('WeatherObserved')
    # print(response)

    # デバイスごとに、データ取得時間を確認
    for device in json.loads(response):

        # デバイスIDから数字の部分だけ抽出
        fullid = device['id']
        idnum = fullid[28:]
        # 無視リストに登録されているか確認
        if int(idnum) in IGNORELIST:
            # 何もしないで終了
            continue

        #print(device['id'] + ' ' + device['dateObserved']['value'])

        # 更新時間を取得
        lastdate = parse(device['dateObservedJST']['value'])
        # 現在時刻と比較
        dt = datetime.datetime.now() - lastdate

        # if dt > datetime.timedelta(minutes=5):

        # 1時間以上の差分がある場合は出力
        if dt > datetime.timedelta(hours=1):
            msg = "デバイス \"" + device['name']['value'] + "\" は1時間以上データ更新がありません."
            # print(msg)
            #print(device['id'] + ' ' + str(dt))
            send_message_to_slack(msg)
