import json
import requests

def readData():
  header = {"Authorization": "AccessToken"}
  
  response = requests.get("https://api.switch-bot.com/v1.0/devices", headers=header)
  devices  = json.loads(response.text)
  #print(devices)
  bots_id  = [device["deviceId"] for device in devices['body']['deviceList'] if "Meter" == device["deviceType"]]
  
  #for bot_id in bots_id:
  
  response = requests.get("https://api.switch-bot.com/v1.0/devices/" + bots_id[0] + "/status", headers=header)
  bot      = json.loads(response.text)
  #print(bot)
  
  temperature    = bot['body']['temperature']
  humidity = bot['body']['humidity']
  
  value = {"temperature": temperature, "humidity":humidity}
  return(value)
  #print("bot id (" + bot_id + ") power : " + power)

if __name__ == '__main__':
  print(readData())


