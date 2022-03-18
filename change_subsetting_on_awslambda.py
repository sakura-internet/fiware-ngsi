import json
from urllib.request import Request, urlopen
import urllib.error
import datetime

USERNAME="user0XX@fiware-sakura.jp"
PASSWORD="yourPassword"
CBHOST="https://orion.fiware-sakura.jp"

FIWARESERVICE="sakura"
FIWARESERVICEPATH="/sensors"

THRESHOLD = 1000

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
        except urllib.error.HTTPError as e:
            print('Error code : %s' % e.code)
            print('Error code : %s' % e.read())
            raise Exception('send request error.')
        except urllib.error.URLError as e:
            print('Error reason : %s' % e.reason)
            raise Exception('send request error.')
        else:
            # responseを出力
            try:
                response_body_json = json.loads(response.read())
                #logging.debug('Response header :\n%s' % response.info())
                #logging.debug('Response body :\n%s' % response_body_json)
                return response_body_json
            except Exception:
                pass
    
    def createHeaders(self):

        headers = {
            'Fiware-Service':self.fiwareservice,
            'Fiware-ServicePath':self.fiwareservicepath
        }
        # トークンを取得する
        self.getAccessToken()
        # トークンヘッダを追加
        headers['X-Auth-Token'] = self.token['access_token']

        #logging.debug('Headers : %s' % headers)
        return headers

    def registerSubscription(self, subscription_body):

        try:
            headers = self.createHeaders()
        except Exception:
            #logging.debug('Create Headers error.')
            return
        headers['Content-Type'] = 'application/json'

        url = self.cb_host + "/v2/subscriptions"
        #logging.debug(url)
        #logging.debug(subscription_body)
        #logging.debug(headers)
        request = urllib.request.Request(url, json.dumps(subscription_body).encode("utf-8"), headers)
        return(self.mySendRequest(request))

    def getSubscriptions(self):
        url = self.cb_host + "/v2/subscriptions"
        headers = self.createHeaders()

        request = urllib.request.Request(url, None, headers)
        return(self.mySendRequest(request))

    def getSubscriptionCount(self, count, offset):
        url = self.cb_host + "/v2/subscriptions?offset=" + str(offset) + "&limit=" + str(count) + "&options=count"
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
                request.get_method = lambda:'DELETE'

                self.mySendRequest(request)
                return

    def deleteSubscriptionById(self, id):

        headers = self.createHeaders()

        url = self.cb_host + "/v2/subscriptions" + "/" + id
        print("=========")
        print(url)
        request = urllib.request.Request(url, None, headers)
        request.get_method = lambda:'DELETE'

        return(self.mySendRequest(request))


    def getVersion(self):

        url = self.cb_host + "/version"
        headers = self.createHeaders()

        request = urllib.request.Request(url, None, headers)
        return (self.mySendRequest(request))


    def getAccessToken(self):
        header = {'Content-Type':'application/json'}
        data = {
            'username' : self.username,
            'password' : self.password
        }

        body = json.dumps(data).encode()

        url = self.cb_host + "/token"

        request = urllib.request.Request(url, body, header)
        self.token = self.mySendRequest(request)

        #logging.debug('Acquired Token : %s' % self.token)
        
def lambda_handler(event, context):
    # get subscriptionId
    sub_id = json.loads(json.dumps(event['subscriptionId']))
    # get targetId
    #target_id = json.dumps(event['contextResponses'][0]['contextElement']['id'])
    target_id = event['contextResponses'][0]['contextElement']['id']
    # check threshold
    count = json.dumps(event['contextResponses'][0]['contextElement']['attributes'][0]['value'])
    # get name(room)
    room = json.dumps(event['contextResponses'][0]['contextElement']['attributes'][1]['value'],ensure_ascii=False)

    #previousvalue = json.dumps(event['contextResponses'][0]['contextElement']['attributes'][0]['metadatas'][0]['value'])
    print(sub_id)
    print(target_id)
    print(count)
    print(room)
    
    orion = FiwareOrion(USERNAME, PASSWORD, FIWARESERVICE, FIWARESERVICEPATH, CBHOST)

    orion.deleteSubscriptionById(sub_id)
    
    # 現在時刻を得る
    #utcnow = datetime.datetime.utcnow()
    #utcnowstr = utcnow.strftime('%Y-%m-%dT%H:%M:%S') + utcnow.strftime('.%f')[:4] + 'Z'

    if int(count) >= int(THRESHOLD):
        msg = room + "のCO2値が" + count + "ppmになりました."
        send_message(msg)
        
        under10_subscription ={
            "description": "CO2 down alarm notification to slack",
            "subject":{
                "entities": [
                    {
                        "idPattern": target_id,
                        "type": "WeatherObserved"
                    }
                ],
                "condition": {
                    "attrs":[
                        "CO2"
                    ],
                    "expression":{
                        "q": "CO2<"+ str(THRESHOLD)
                    }
                }
            },
            "notification":{
                "http": {
                    "url": "https://XXXXXXX.execute-api.ap-northeast-1.amazonaws.com/dev"
                },
                "attrs": [
                    "CO2",
                    "name"
                ],
                "attrsFormat": "legacy"
            },
            "expires": "2023-03-31T14:59:59.00Z"
        }

        orion.registerSubscription(under10_subscription)
        
    elif int(count) < int(THRESHOLD):
        msg = room + "のCO2値が下がりました(" + count + "ppm)."
        send_message(msg)

        over10_subscription ={
            "description": "CO2 up alarm notification to slack",
            "subject":{
                "entities": [
                    {
                        "idPattern": target_id,
                        "type": "WeatherObserved"
                    }
                ],
                "condition": {
                    "attrs":[
                        "CO2"
                    ],
                    "expression":{
                        "q": "CO2>" + str(THRESHOLD)
                    }
                }
            },
            "notification":{
                "http": {
                    "url": "https://XXXXXXXXX.execute-api.ap-northeast-1.amazonaws.com/dev"
                },
                "attrs": [
                    "CO2",
                    "name"
                ],
                "attrsFormat": "legacy"
            },
            "expires": "2023-03-31T14:59:59.00Z"
        }
        
        orion.registerSubscription(over10_subscription)

    #print(orion.getVersion())


def send_message(msg):
    # make slack message body
    send_data = {
        "channel" : "target channel",
        "username": "sensor-notification",
        "text": msg
    }
    payload = "payload=" + json.dumps(send_data)
    request = Request(
        # iot-sensors
        "https://hooks.slack.com/services/XXXXXX/YYYYYY/ZZZZZZZZZZZZZ",
        data=payload.encode("utf-8"),
        method="POST"
        )
    with urlopen(request) as response:
        response_body = response.read().decode("utf-8")
