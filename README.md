# fiware-ngsi

FIWARE Orion (Context Broker)へのデータ登録・更新用スクリプトです。

さくらインターネットとNECで実施中の「データ流通実証実験」の環境で使うことができます。素のFIWARE Orionの環境でももちろん使えます。

## 初期設定
sendada.py内の冒頭部分で、IDやPassword、ContextBrokerのアドレス情報を設定してください。
また、登録したいデータモデルをコード中程で定義してください。

## 実行方法
```
# python ./sendada.py
```

初期登録とデータ更新で、コード最下段にある関数呼び出し部を書き換える必要があります。

## 参考情報
実証実験については
https://www.fiware-testbed.jp
を参照してください。
