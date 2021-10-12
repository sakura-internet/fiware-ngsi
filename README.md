# fiware-ngsi

FIWARE Orion (Context Broker)へのデータ登録・更新用スクリプトです。

さくらインターネットとNECで実施中の「データ流通実証実験」の環境で使うことができます。素のFIWARE Orionの環境でももちろん使えます。

## 初期設定
sendada_for_bme280.py(あるいは_for_switchbot)内の冒頭部分で、IDやPasswordを設定してください。
FIWARESERVICEやFIWARESERVICEPATH、DATANAMEなどを変更してもよいです。

## 実行方法
あらかじめ、
# pip3 install requests
として、requestsモジュールをインストールしておきます。
その上で、

```
# python ./senddata_for_bme280.py
もしくは
# python ./senddata_for_switchbot.py
```

初期登録とデータ更新で、コード最下段にある関数呼び出し部を書き換える必要があります。

## 参考情報
実証実験については
https://www.fiware-testbed.jp
を参照してください。
