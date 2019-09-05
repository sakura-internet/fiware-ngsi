#!/usr/bin/python
#-*-coding: utf-8-*-

import urllib
import urllib2
#import urllib.request, urllib.error
import json
import time
import datetime
import logging
import pickle

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

class FiwareOrion:

    TOKEN_EXPIRE_MERGIN = 5*60  #sec, 残り何秒になったらupdateするか
    #TOKEN_EXPIRE_MERGIN = 60*60-30  #sec

    username = ""
    password = ""
    fiwareservice = ""
    fiwareservicepath = ""
    cb_host = ""
    data_type = ""
    data_name = ""
    data_id = ""
    token = ""
    token_issued_time = ""
    tokenfilename = ""
    noauthflag = ""

    def __init__(self, username, password, fiwareservice, fiwareservicepath, cb_host, data_type, data_name, tokenfilename, noauthflag):
        self.username = username
        self.password = password
        self.cb_host = cb_host
        self.data_type = data_type
        self.data_name = data_name
        self.data_id = 'urn:ngsi-ld:' + data_type + ':' + data_name
        self.fiwareservice = fiwareservice
        self.fiwareservicepath = fiwareservicepath
        self.tokenfilename = tokenfilename
        self.noauthflag = noauthflag

    def mySendRequest(self, request):
        # requestを発行
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            logging.error('Error code : %s' % e.code)
            raise Exception('send request error.')
        except urllib2.URLError as e:
            logging.error('Error reason : %s' % e.reason)
            raise Exception('send request error.')
        else:
            # responseを出力
            try:
                response_json = json.loads(response.read())
                logging.info('Response : %s' % response_json)
                return response_json
            except Exception:
                pass

    def isTokenExpired(self):
        delta = datetime.datetime.now() - self.token_issued_time
        logging.debug('Elapsed Time : %s' % delta)
        if (self.token['expires_in'] - delta.total_seconds()) < self.TOKEN_EXPIRE_MERGIN :
            logging.debug('isTokenExpired: true')
            return True
        else:
            logging.debug('isTokenExpired: false')
            return False

    def updateToken(self):
        url = self.cb_host + "/token"
        header = {'Content-Type':'application/json'}
        data = {
            'refresh' : self.token['refresh_token']
        }

        body = json.dumps(data)
        request = urllib2.Request(url, body, header)

        try:
            result = self.mySendRequest(request)
        except Exception:
            # トークン更新に失敗している場合は、トークン取得からやり直す
            logging.debug('token update failed')
            try:
                self.getAccessToken()
            except Exception:
                logging.debug('get access token error.')
                return
        else:
            if result == None:
                logging.debug('token update failed')
                try:
                    self.getAccessToken()
                except Exception:
                    logging.debug('get access token error.')
                    return

            # トークン更新に成功の場合
            self.token = result
            self.token_issued_time = datetime.datetime.now()

        logging.debug('Refreshed Token : %s' % self.token)
        logging.debug('Token Issued Time : %s' % self.token_issued_time)

        # トークンと更新時間をファイルに書き込む
        with open(self.tokenfilename, "wb") as tokenfile:
            pickle.dump(self.token, tokenfile)
            pickle.dump(self.token_issued_time, tokenfile)

        logging.debug('Updated Token : %s' % self.token)
        logging.debug('Token Issued Time : %s' % self.token_issued_time)

    def createHeaders(self):

        headers = {
            'Fiware-Service':self.fiwareservice,
            'Fiware-ServicePath':self.fiwareservicepath
        }
        # 認証必要な系の場合には、トークンを付与する
        if self.noauthflag == False:
            # トークンを、トークン保存ファイルから取得する
            try:
                with open(self.tokenfilename, "rb") as tokenfile:
                    self.token = pickle.load(tokenfile)
                    self.token_issued_time = pickle.load(tokenfile)
            except:
                # ファイルオープンに失敗(=トークン保存ファイルがない)場合は、トークン取得からやり直す
                logging.debug('token file could not open.')
                try:
                    self.getAccessToken()
                except Exception:
                    logging.debug('get access token error.')
                    raise Exception('createHeaders Error.')
                    return

            # トークン内容をチェック、トークン内容がNoneの場合はトークン取得からやり直す
            if self.token == None:
                logging.debug('token file is not correct.')
                try:
                    self.getAccessToken()
                except Exception:
                    logging.debug('get access token error.')
                    raise Exception('createHeaders Error.')
                    return

            # トークン内容をチェック、トークンが壊れている場合はやはりトークン取得からやり直す
            if 'expires_in' not in self.token:
                logging.debug('token file is not correct.')
                try:
                    self.getAccessToken()
                except Exception:
                    logging.debug('get access token error.')
                    raise Exception('createHeaders Error.')
                    return

            # トークン有効期限をチェックし、必要ならupdateする
            if self.isTokenExpired():
                self.updateToken()

            # トークンヘッダを追加
            headers['X-Auth-Token'] = self.token['access_token']

        logging.debug('Headers : %s' % headers)
        return headers

    def createHeaders_noauth(self):
        headers = {
            'Fiware-Service':self.fiwareservice,
            'Fiware-ServicePath':self.fiwareservicepath
        }

        logging.debug('Headers : %s' % headers)

        return headers

    #def updateEntities(self, firecount, powerstate):
    def updateEntities(self, bodypart):

        try:
            headers = self.createHeaders()
        except Exception:
            logging.debug('Create Headers error.')
            return

        headers['Content-Type'] = 'application/json'
        #headers['Accept'] = 'application/json'

        # URLを生成
        url = self.cb_host + "/v2/entities" + "/" +self.data_id + "/" + "attrs"

        request = urllib2.Request(url, bodypart, headers)

        #return
        self.mySendRequest(request)

    def registerEntities(self, body):

        # すでに登録されているか調べ、登録されている場合は何もしない
        #if self.getTargetEntity() != None:
        #    logging.debug('Already Registered!')
        #    return

        try:
            headers = self.createHeaders()
        except Exception:
            logging.debug('Create Headers error.')
            return
        headers['Content-Type'] = 'application/json'

        url = self.cb_host + "/v2/entities"

        request = urllib2.Request(url, body, headers)
        return(self.mySendRequest(request))

    def registerSubscription(self, subscription_body):

        try:
            headers = self.createHeaders()
        except Exception:
            logging.debug('Create Headers error.')
            return
        headers['Content-Type'] = 'application/json'

        url = self.cb_host + "/v2/subscriptions"

        request = urllib2.Request(url, subscription_body, headers)
        return(self.mySendRequest(request))

    def getEntities(self):
        url = self.cb_host + "/v2/entities"
        headers = self.createHeaders()

        request = urllib2.Request(url, None, headers)
        return(self.mySendRequest(request))

    def getTargetEntity(self, id):
        url = self.cb_host + "/v2/entities" + "/" + id
        logging.debug('url is %s' % url)
        headers = self.createHeaders()

        request = urllib2.Request(url, None, headers)
        return(self.mySendRequest(request))

    def getSubscriptions(self):
        url = self.cb_host + "/v2/subscriptions"
        headers = self.createHeaders()

        request = urllib2.Request(url, None, headers)
        return(self.mySendRequest(request))

    def deleteEntities(self, id):
        # 登録されているか調べ、登録されていなければ何もしない
        #if self.getTargetEntity() == None:
        #    return

        url = self.cb_host + "/v2/entities" + "/" + id
        headers = self.createHeaders()

        request = urllib2.Request(url, None, headers)
        request.get_method = lambda:'DELETE'
        return(self.mySendRequest(request))

    def deleteAllSubscriptions(self):

        subscriptions = self.getSubscriptions(noauth)

        for subsc in subscriptions:
            logging.debug('subscription : %s' % subsc)
            self.deleteSubscription(subsc, noauth)

        return

    def deleteSubscription(self, subscription_data):

        headers = self.createHeaders()

        subscriptionids = self.getSubscriptions()
        for id in subscriptionids:
            if id['notification']['http']['url'] == subscription_data['notification']['http']['url']:
                url = self.cb_host + "/v2/subscriptions" + "/" + id['id']
                request = urllib2.Request(url, None, headers)
                request.get_method = lambda:'DELETE'

                self.mySendRequest(request)
                return

    def getAccessToken(self):
        header = {'Content-Type':'application/json'}
        data = {
            'username' : self.username,
            'password' : self.password
        }

        body = json.dumps(data)

        url = self.cb_host + "/token"

        request = urllib2.Request(url, body, header)

        try:
            self.token = self.mySendRequest(request)
        except Exception:
            logging.debug('get new token error.')
            return

        self.token_issued_time = datetime.datetime.now()

        # トークンと更新時間をファイルに書き込む
        with open(self.tokenfilename, "wb") as tokenfile:
            pickle.dump(self.token, tokenfile)
            pickle.dump(self.token_issued_time, tokenfile)

        logging.debug('Acquired Token : %s' % self.token)
        logging.debug('Token Issued Time : %s' % self.token_issued_time)
