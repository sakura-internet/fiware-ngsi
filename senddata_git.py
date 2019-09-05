#!/usr/bin/python
#-*-coding: utf-8-*-

import fiwareorion
import requests
import json
import datetime
import logging

import bme280_custom

### センサーデータを取得 ###
sensor_data = bme280_custom.readData()

### アクセス先およびデータ定義 ###
USERNAME="user00X@fiware-testbed.jp"
PASSWORD="password"
CBHOST="https://orion.fiware-testbed.jp"
FIWARESERVICE="Sakura"
FIWARESERVICEPATH="/dummy_office"
DATATYPE="WeatherObserved"
DATANAME="test001"
TOKENFILE=".token"
LAT=35.12345
LNG=139.12345
noauthflag = False
'''
USERNAME="dummyuser"
PASSWORD="dummypass"
CBHOST="http://localhost:1026"
FIWARESERVICE="YourCompany"
FIWARESERVICEPATH="/your_branch"
DATATYPE="WeatherObserved"
DATANAME="Tokyo001"
TOKENFILE=".token"
LAT=35.69438888
LNG=139.69555555
noauthflag = True
'''
### fiwareorionインスタンスを生成 ###
orion = fiwareorion.FiwareOrion(USERNAME, PASSWORD, FIWARESERVICE, FIWARESERVICEPATH, CBHOST, DATATYPE, DATANAME, TOKENFILE, noauthflag)

### 送信データを定義 ###
# 現在時刻を得る
utcnow = datetime.datetime.utcnow()
utcnowstr = utcnow.strftime('%Y-%m-%dT%H:%M:%S') + utcnow.strftime('.%f')[:4] + 'Z'

# data_idを定義
data_id = 'urn:ngsi-ld:' + DATATYPE + ':' + DATANAME

# URLやBODYを整形
data = {
    'id':data_id,
    'type':DATATYPE,
    'dateModified':{
        'type':'DateTime',
        'value': utcnowstr
    },
    'location': {
        'type': 'geo:json',
        'value': {
            'type': 'Point',
            'coordinates': [
                LNG,
                LAT
            ]
        }
    },
    'dateObserved':{
        'type':'DataTime',
        'value': utcnowstr
    },
    'atmosphericPressure':{
        'type':'Number',
        'value':1000.00
    },
    'temperature':{
        'type':'Number',
        'value':20.0
    },
    'relativeHumidity':{
        'type':'Number',
        'value':0.5
    }
}
body = json.dumps(data)
#logging.debug('request body : %s' % body)

datapart = {
    'dateObserved':{
        'type':'DateTime',
        'value': utcnowstr
    },
    'atmosphericPressure':{
        'type':'Number',
        'value': float(sensor_data['pressure'])
    },
    'temperature':{
        'type':'Number',
        'value': float(sensor_data['temperature'])
    },
    'relativeHumidity':{
        'type':'Number',
        'value': format(float(sensor_data["humidity"])/100.0, '.4f')
    }
}
bodypart = json .dumps(datapart)

### リクエスト送信パート ###
try:
    #ret_fi1 = orion.registerEntities(body)
    #ret_fi2 = orion.updateEntities(bodypart)

    #ret_fi3 = orion.deleteEntities(data_id)

    ret_fi4 = orion.getEntities()

    #ret_fi5 = orion.getTargetEntity(data_id)

except requests.exceptions.RequestException as e:
    print('request failed(fiware): ', e)
