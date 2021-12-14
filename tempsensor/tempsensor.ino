#include <M5Stack.h>
#include "Seeed_BME280.h"
#include <WiFi.h>
#include <SSLClient.h>
#include "trust_anchors.h"
#include <ArduinoJson.h>

#define WIFI_SSID "YOURWIFI_AP"
#define WIFI_PASS "AP_PASS"

#define USERID "user0XX@fiware-testbed.jp"
#define PASSWD "YYYYYYYYYYY"
#define HOST "orion.fiware-testbed.jp"
#define FIWARESERVICE "Sakura"
#define FIWARESERVICEPATH "/tokyo_office"
#define DATATYPE "WeatherObserved"
#define DATAID "test004"

#define TIMEOUTVAL 5000
#define INTERVAL 60 * 1000
#define MARGIN 1 * 60 * 1000         // トークン有効期限が1分切っていたら再取得する
 
unsigned long prev, current;         // 前回データを送信した時刻を記憶しておく

WiFiClient wifi_client;
SSLClient client(wifi_client, TAs, (size_t)TAs_NUM, 2);

String access_token = "";
unsigned long expires_in = 0;       // トークン有効期限（秒）
unsigned long token_issue_time;     // トークンを発行した時刻

BME280 bme280;

void setup() {
  // put your setup code here, to run once:
  M5.begin();
  M5.Power.begin();
  M5.Lcd.fillScreen(BLACK);

  // シリアルモニタに接続
  Serial.begin(115200);
  while(!Serial);
  Serial.println("プログラム開始");

  // BME280センサを初期化
  if(!bme280.init()){
    M5.Lcd.println("BME280 Sensor not connected!");
    Serial.println("BME280 Sensor not connected!");
    while(true);
  }
  M5.Lcd.println("BME280 Sensor initialized!");
  Serial.println("BME280 Sensor initialized!");

  // WiFiに接続
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  M5.Lcd.print("WiFi connecting.");
  Serial.print("WiFi connecting.");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    M5.Lcd.print(".");
    Serial.print(".");
  }
  M5.Lcd.println("done.");
  M5.Lcd.print("IP address = ");
  M5.Lcd.println(WiFi.localIP());
  Serial.println("done.");
  Serial.print("IP Address = ");
  Serial.println(WiFi.localIP());

  // 起動時のみ手動でデータを送信する(失敗したら終了)
  pushSensorValue();
  
  // 時間を記録しておく
  prev = millis();
}

String getAccessToken(){

  if(expires_in == 0 || access_token == ""){
    Serial.println("初実行チェック、トークン取得する");    
  }
  else{
    // トークン発行時点からの経過時間を算出
    unsigned long elapsed_time = millis() - token_issue_time;
    // トークンの有効期限をチェックする
    if((expires_in * 1000 - MARGIN) > elapsed_time){
      // 有効期限内であれば、そのまま終了
      return("OK");
    }
  }
  // トークンがないか有効期限が切れる場合は(再)取得
  Serial.println("Start Server Access (Phase1) ");

  // ====== アクセストークンを取得する ========
  String message = "{\"username\" : \"";
  message += USERID;
  message += "\",";
  message += "\"password\" : \"";
  message += PASSWD;
  message += "\"}";
  
  client.connect(HOST, 443);
  client.println("POST /token HTTP/1.1");
  client.println("Host: " + String(HOST));
  client.println("Content-Type: application/json");
  client.println("Fiware-Service: " + String(FIWARESERVICE));
  client.println("Fiware-ServicePath: " + String(FIWARESERVICEPATH));
  client.print("Content-Length: ");
  client.print(strlen(message.c_str()));
  client.print("\r\n\r\n");
  client.print(message.c_str());

  // サーバアクセス失敗か、タイムアウト判定
  unsigned long timeout = millis();
  while (!client.available()){
    if(millis() - timeout > TIMEOUTVAL){
      M5.Lcd.println("Timeout!");
      Serial.println("Timeout!");
      client.stop();
      return("Error");
    }
    delay(10);
  }
  Serial.println("done.");

  // サーバからの値を読む
  String line;
  boolean bodyStart = false;
  String buffer= "";

  while(client.available()){
    line = client.readStringUntil('\r');
    line.trim();
    //Serial.println(line);
    if(line==""){
      //Serial.println("空行");
      bodyStart = true;
      continue;
    }
    if(bodyStart){
      buffer.concat(line);
    }
  }
  Serial.println(buffer);
  client.stop();
  
  // 受信データからトークンを取り出す
  StaticJsonDocument<2000> token;
  deserializeJson(token, buffer);
  
  access_token = (const char*)token["access_token"];
  expires_in = token["expires_in"];
  
  token_issue_time = millis();
  
  Serial.println("Access_token: " + access_token);
  Serial.println("Expires_in:" + (String)expires_in);
  return("OK");
}

void pushSensorValue(){

  // トークンをチェック
  if(getAccessToken() != "OK"){
    Serial.println("Token Error");
    M5.Lcd.println("Token Error");
    return;
  }
  
  //M5.Lcd.print("Start Server Access (Phase2) ");

  // センサからデータを取得
  uint32_t pressure = bme280.getPressure();
  uint32_t humidity = bme280.getHumidity();
  uint32_t temperature = bme280.getTemperature();

  // 画面に出力
  /*
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextSize(1);
  M5.Lcd.setCursor(0, 100);
  //M5.Lcd.println(message);
  M5.Lcd.println("Temp: " +  String((float)temperature,1));
  M5.Lcd.printf("Humidity: %5d %%\n", humidity);
  M5.Lcd.printf("Pressure: %5d hPa\n", pressure/100);
  */
  M5.Lcd.fillScreen(BLACK);
  
  M5.Lcd.setTextSize(1);
  M5.Lcd.setTextFont(8);
  M5.Lcd.setTextColor(M5.Lcd.color565(220,240,255));
  M5.Lcd.setCursor(60,10);
  M5.Lcd.print(String((float)temperature,1));

  M5.Lcd.setTextSize(2);
  M5.Lcd.setTextFont(4);
  M5.Lcd.setCursor(90,120);
  M5.Lcd.print(String((float)humidity,1) + "%");
  M5.Lcd.setCursor(40,180);
  M5.Lcd.print(String((float)pressure/100,1) + "hPa");

  // 送信データ(JSON)をつくる
  String message = "{";
  message += "\"atmosphericPressure\" : {";
  message += "\"type\" : \"Number\",";
  message += "\"value\" : " + String((float)pressure/100.0,1);
  message += "},";
  message += "\"temperature\" : {";
  message += "\"type\" : \"Number\",";
  message += "\"value\" : " + String((float)temperature,1);
  message += "},";
  message += "\"relativeHumidity\" : {";
  message += "\"type\" : \"Number\",";
  message += "\"value\" : " + String((float)humidity/100.0,2);
  message += "}";
  message += "}";

  Serial.println(message);
  
  // ========= データを送信 =========
  client.connect(HOST, 443);
  client.println("POST /v2/entities/urn:ngsi-ld:" + String(DATATYPE) + ":" + String(DATAID) +"/attrs HTTP/1.1");
  client.println("Host: " + String(HOST));
  client.println("Content-Type: application/json");
  client.println("Fiware-Service: " + String(FIWARESERVICE));
  client.println("Fiware-ServicePath: " + String(FIWARESERVICEPATH));
  client.println("X-Auth-Token: " + access_token); 
  client.print("Content-Length: ");
  client.print(strlen(message.c_str()));
  client.print("\r\n\r\n");
  client.print(message.c_str());

  // サーバアクセス失敗か、タイムアウト判定
  unsigned long timeout = millis();
  while (!client.available()){
    if(millis() - timeout > TIMEOUTVAL){
      M5.Lcd.println("Timeout!");
      Serial.println("Timeout!");
      client.stop();
      return;
    }
    delay(10);
  }
  
  client.stop();
}

void loop() {
  // put your main code here, to run repeatedly:

  //経過時間を確認し、インターバル時間より長く経過していたらデータを取得する
  current = millis();
  if((current - prev) > INTERVAL){
    pushSensorValue();
    prev = current;
  }
}
