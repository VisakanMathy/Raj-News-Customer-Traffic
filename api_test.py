#response = requests.get("https://transportapi.com/v3/uk/bus/stop/490008978N1/live.json?app_id=5529b185&app_key=2f1123321c2c691ce8decde8c5076a95&group=no&limit=5&nextbuses=yes")
import requests
import time
import datetime

def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()
def timeConverter(timestamp,timeToStation):
    if len(timestamp) == 28:    
        timestamp = timestamp[0:25]+timestamp[27]
    a = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(seconds = timeToStation)
    return time.ctime(int(unix_time(a))), unix_time(a)

store = {}
def trafficRequest(store):
    responseTo = requests.get("https://api.tfl.gov.uk/StopPoint/490008978N2/Arrivals").json()
    responseFrom = requests.get("https://api.tfl.gov.uk/StopPoint/490008978N1/Arrivals").json()
    #print(json.dumps(response.json()[0], sort_keys=True, indent=4))
    for i in range(len(responseTo)):
        responseItem = responseTo[i]
        if responseItem['timeToStation'] < 200:
            print(responseItem['lineId'], ":  ",responseItem['timeToStation'])
            timestamp = responseItem['timestamp']
            timeToStation = responseItem['timeToStation']
            print(timestamp)
            timestamp, ts = timeConverter(timestamp,timeToStation)
            store[responseItem['id']] = [responseItem['lineId'], timestamp, ts,'to']
    for i in range(len(responseFrom)):
        responseItem = responseFrom[i]
        if responseItem['timeToStation'] < 200:
            print(responseItem['lineId'], ":  ",responseItem['timeToStation'])
            timestamp = responseItem['timestamp']
            print(timestamp)
            timeToStation = responseItem['timeToStation']
            timestamp, ts = timeConverter(timestamp,timeToStation)
            store[responseItem['id']] = [responseItem['lineId'], timestamp, ts,'from']
    for i in store.keys():
        if time.time() - store[i][2] > 300:
            print(store[i])
            del store[i]
    return store
while True:
    store = trafficRequest(store)
    time.sleep(60)
    
