import requests
import json
import base64
import configparser
import click

HARDED_CODE_SECRET = "uyjD5MjLGYHKvwrt"
CONFIG_FILE = "settings.ini"
proxy = {
#'http' : 'http://localhost:8080',
#'https' : 'http://localhost:8080'
}

class Persistency:
    KEY_BOOTSTRAP = "bootstrap"
    KEY_TOKEN = "token"
    KEY_DEVICES = "devices"

    def __init__(self):
        self.parser = configparser.ConfigParser()
        self.parser.read(CONFIG_FILE)
        if (not self.parser.has_section(self.KEY_BOOTSTRAP)) :
            self.parser[self.KEY_BOOTSTRAP] = {}
        
        if (not self.parser.has_section(self.KEY_TOKEN)) :
            self.parser[self.KEY_TOKEN] = {}
        
        if (not self.parser.has_section(self.KEY_DEVICES)) :
            self.parser[self.KEY_DEVICES] = {}
        
    def save(self):
        with open(CONFIG_FILE, 'w') as configfile:
            self.parser.write(configfile)


def bootstrap(persistency) : 
    print ("Conecting to bootstrap")
    url="https://bootstrap.nos.pt/bootstrap/nosremote_android_v1.json"
    headers = {}
    headers["Host"] = "bootstrap.nos.pt"
    headers["Connection"] = "Keep-Alive"
    headers["Accept-Encoding"] = "gzip"
    headers["User-Agent"] = "okhttp/3.10.0"
    r =requests.get(url, headers=headers, proxies=proxy, verify=False)
    bootstrap = json.loads(r.text)
    appClient = bootstrap["app.client.id"]
    authUrl = bootstrap["oauth2"]["token.url"]
    for service in bootstrap["services"] : 
        if (service["name"] == "remote") :
            remote = service["url"]
        if (service["name"] == "mage") :
            mage = service["url"]
        


    message_bytes = (appClient+":"+HARDED_CODE_SECRET).encode('ascii')
    authorization = base64.b64encode(message_bytes)

    print("appclient:" + appClient)
    print("remote:"+ remote)
    print("mage:"+ mage)
    print("authorization:" + authorization.decode("utf-8"))
    print("authentication_url:" + authUrl)
    persistency.parser[Persistency.KEY_BOOTSTRAP]["appclient"] = appClient
    persistency.parser[Persistency.KEY_BOOTSTRAP]["remote"] = remote
    persistency.parser[Persistency.KEY_BOOTSTRAP]["mage"] = mage
    persistency.parser[Persistency.KEY_BOOTSTRAP]["authorization"] = authorization.decode("utf-8")
    persistency.parser[Persistency.KEY_BOOTSTRAP]["authUrl"] = authUrl
    persistency.save()
    return True

def getToken(persistency):
    headers = {}
    headers["Host"] = "tyr-prod.apigee.net"
    headers["Accept"] = "application/json"
    headers["Authorization"] = "Basic " + persistency.parser[Persistency.KEY_BOOTSTRAP]["authorization"]

    headers["Connection"] = "Keep-Alive"
    headers["Content-type"] = "application/x-www-form-urlencoded"
    headers["User-Agent"] = "Dalvik/2.1.0 (Linux; U; Android 11; sdk_gphone_x86_arm Build/RSR1.201013.001)"
    headers["Accept-Encoding"] = "gzip"

    params = {"client_id": persistency.parser[Persistency.KEY_BOOTSTRAP]["appclient"]}
    data={'grant_type': 'home_gateway', 'scope': 'user_profile'}

    r =requests.post(persistency.parser[Persistency.KEY_BOOTSTRAP]["authUrl"], headers=headers, params=params, data=data, proxies=proxy, verify=False)
    
    authRequest = json.loads(r.text)
    if ("ErrorCode" in authRequest):
        print(authRequest["ErrorCode"])
        return False
    accessToken = authRequest["access_token"]
    token_type = authRequest["token_type"]

    persistency.parser[Persistency.KEY_TOKEN]["token"] = accessToken
    persistency.parser[Persistency.KEY_TOKEN]["token_type"] = token_type
    persistency.save()
    return True

def getAuth(persistency):
    return persistency.parser[Persistency.KEY_TOKEN]["token_type"] + " " + persistency.parser[Persistency.KEY_TOKEN]["token"]

def getDevices(persistency):
    headers = {}
    headers["Host"] = "tyr-prod.apigee.net"
    headers["X-Core-DeviceId"] = "02:00:00:00:00:00-Google-sdk_gphone_x86_arm-unknown"
    headers["Authorization"] = getAuth(persistency)
    headers["Connection"] = "Keep-Alive"
    headers["x-apikey"] = persistency.parser[Persistency.KEY_BOOTSTRAP]["appclient"]
    headers["User-Agent"] = "okhttp/3.10.0"
    headers["Accept-Encoding"] = "identity"

    data={'grant_type': 'home_gateway', 'scope': 'user_profile'}

    r =requests.get(persistency.parser[Persistency.KEY_BOOTSTRAP]["remote"]+"devices" , headers=headers, data=data, proxies=proxy, verify=False)

    devicesRequest = json.loads(r.text)
    i = 0
    for device in devicesRequest:
        print(str(i) + ":" +device["DeviceId"])
        if (not persistency.parser.has_section(device["DeviceId"])) :
            persistency.parser[device["DeviceId"]] = {}

        persistency.parser[device["DeviceId"]]["DeviceFamily"] = str(device["DeviceFamily"])
        persistency.parser[device["DeviceId"]]["FriendlyName"] = device["FriendlyName"]
        i+=1
    persistency.save()

def getDeviceDetails(persistency, deviceId):
    return persistency.parser[deviceId]

def keypressRequest(persistency, device, key):
    devicePer = getDeviceDetails(persistency, device) 
    headers = {}
    headers["Host"] = "tyr-prod.apigee.net"
    headers["X-Core-DeviceId"] = "02:00:00:00:00:00-Google-sdk_gphone_x86_arm-unknown"
    headers["X-Core-DeviceProductType"] = devicePer["DeviceFamily"]
    headers["Content-type"] = "application/json; charset=UTF-8"
    headers["Authorization"] = getAuth(persistency)
    headers["Connection"] = "Keep-Alive"
    headers["x-apikey"] = persistency.parser[Persistency.KEY_BOOTSTRAP]["appclient"]
    headers["User-Agent"] = "okhttp/3.10.0"
    headers["Accept-Encoding"] = "identity"

    data='{"Keycode": '+key+'}'

    r =requests.post(persistency.parser[Persistency.KEY_BOOTSTRAP]["remote"]+"/devices/"+device+"/keypress" , headers=headers, data=data, proxies=proxy, verify=False)

    print(r.text)
  
    

def volumeRequest(persistency, device,action):
    devicePer = getDeviceDetails(persistency, device) 
    headers = {}
    headers["Host"] = "tyr-prod.apigee.net"
    headers["X-Core-DeviceId"] = "02:00:00:00:00:00-Google-sdk_gphone_x86_arm-unknown"
    headers["X-Core-DeviceProductType"] = devicePer["DeviceFamily"]
    headers["Content-type"] = "application/json; charset=UTF-8"
    headers["Authorization"] = getAuth(persistency)
    headers["Connection"] = "Keep-Alive"
    headers["x-apikey"] = persistency.parser[Persistency.KEY_BOOTSTRAP]["appclient"]
    headers["User-Agent"] = "okhttp/3.10.0"
    headers["Accept-Encoding"] = "identity"

    data='{"Action": "'+action+'"}'

    r =requests.post(persistency.parser[Persistency.KEY_BOOTSTRAP]["remote"]+"/devices/"+device+"/volume" , headers=headers, data=data, proxies=proxy, verify=False)

    print(r.text)

def channelsRequest(persistency, device):
    headers = {}
    headers["Host"] = "tyr-prod.apigee.net"
    headers["X-Core-DeviceId"] = "02:00:00:00:00:00-Google-sdk_gphone_x86_arm-unknown"
    headers["Authorization"] = getAuth(persistency)
    headers["Connection"] = "Keep-Alive"
    headers["x-apikey"] = persistency.parser[Persistency.KEY_BOOTSTRAP]["appclient"]
    headers["User-Agent"] = "okhttp/3.10.0"
    headers["Accept-Encoding"] = "identity"

    params = {"client_id": persistency.parser[Persistency.KEY_BOOTSTRAP]["appclient"]}
    data={'grant_type': 'home_gateway', 'scope': 'user_profile'}

    r =requests.get(persistency.parser[Persistency.KEY_BOOTSTRAP]["remote"]+"devices" , headers=headers, data=data, proxies=proxy, verify=False)

    devicesRequest = json.loads(r.text)
    i = 0
    for device in devicesRequest:
        print(i + ":" +device["DeviceId"])
        i+=1

def requestChangeChannel(persistency, device, channel):
    headers = {}
    headers["Host"] = "tyr-prod.apigee.net"
    headers["X-Core-DeviceId"] = "02:00:00:00:00:00-Google-sdk_gphone_x86_arm-unknown"
    headers["Authorization"] = getAuth(persistency)
    headers["Connection"] = "Keep-Alive"
    headers["x-apikey"] = persistency.parser[Persistency.KEY_BOOTSTRAP]["appclient"]
    headers["User-Agent"] = "okhttp/3.10.0"
    headers["Accept-Encoding"] = "identity"

    params = {"client_id": persistency.parser[Persistency.KEY_BOOTSTRAP]["appclient"]}
    data={'grant_type': 'home_gateway', 'scope': 'user_profile'}

    r =requests.get(persistency.parser[Persistency.KEY_BOOTSTRAP]["remote"]+"devices" , headers=headers, data=data, proxies=proxy, verify=False)

    devicesRequest = json.loads(r.text)
    i = 0
    for device in devicesRequest:
        print(i + ":" +device["DeviceId"])
        i+=1


@click.group()
def main():
    pass

persistency = Persistency()

@main.command()
def keys():
    print ("Keys:")
    print ("up:38")
    print ("down:40")
    print ("left:39")
    print ("right:37")
    print ("ok:13")
    print ("channel up:81")
    print ("channel down:90")
    print ("back:76")
    print ("info:73")
    print ("menu:121")
    print ("power:320")
    print ("play:80")
    print ("back:66")
    print ("foward:70")
    print ("1:49")
    print ("2:50")
    print ("3:51")
    print ("4:52")
    print ("5:53")
    print ("6:54")
    print ("7:55")
    print ("8:56")
    print ("9:57")
    print ("0:48")
    print ("clean:37")
    


@main.command()
@click.argument('device')
@click.argument('key')
def keypress(device, key):
    if (not persistency.parser.has_option(Persistency.KEY_BOOTSTRAP, "authorization")):
        if (not bootstrap(persistency)) :
            return False
    if (not persistency.parser.has_option(Persistency.KEY_TOKEN, "token")):
        if (not getToken(persistency)):
            return False

    keypressRequest(persistency, device, key)

@main.command()
@click.argument('device')
def channels(device):
    if (not persistency.parser.has_option(Persistency.KEY_BOOTSTRAP, "authorization")):
        if (not bootstrap(persistency)) :
            return False
    if (not persistency.parser.has_option(Persistency.KEY_TOKEN, "token")):
        if (not getToken(persistency)):
            return False

    channelsRequest(persistency, device)


@main.command()
@click.argument('device')
@click.argument('action', type=click.Choice(['up', 'down', 'mute']), required = True)
def volume(device, action):
    if (not persistency.parser.has_option(Persistency.KEY_BOOTSTRAP, "authorization")):
        if (not bootstrap(persistency)) :
            return False
    if (not persistency.parser.has_option(Persistency.KEY_TOKEN, "token")):
        if (not getToken(persistency)):
            return False

    volumeRequest(persistency, device, action)

@main.command()
@click.argument('device')
@click.argument('channel')
def changechannel(device, channel):
    if (not persistency.parser.has_option(Persistency.KEY_BOOTSTRAP, "authorization")):
        if (not bootstrap(persistency)) :
            return False
    if (not persistency.parser.has_option(Persistency.KEY_TOKEN, "token")):
        if (not getToken(persistency)):
            return False

    requestChangeChannel(persistency, device, channel)
    

@main.command()
def devices():
    if (not persistency.parser.has_option(Persistency.KEY_BOOTSTRAP, "authorization")):
        if (not bootstrap(persistency)) :
            return False
    if (not persistency.parser.has_option(Persistency.KEY_TOKEN, "token")):
        if (not getToken(persistency)):
            return False

    getDevices(persistency)

@main.command()
def clean():
    bootstrap(persistency)
    getToken(persistency)

if __name__ == "__main__":
    main()

    
