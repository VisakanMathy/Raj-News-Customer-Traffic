#response = requests.get("https://transportapi.com/v3/uk/bus/stop/490008978N1/live.json?app_id=5529b185&app_key=2f1123321c2c691ce8decde8c5076a95&group=no&limit=5&nextbuses=yes")
import requests
import time
import datetime
def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()
def timeConverter(timestamp,timeToStation):
    timestamp = timestamp[0:25]+timestamp[27]
    a = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(seconds = timeToStation)
    return time.ctime(int(unix_time(a))), unix_time(a)

lastresponse = {}
store = {}
while True:
    response = requests.get("https://api.tfl.gov.uk/StopPoint/490008978N2/Arrivals")
    #print(json.dumps(response.json()[0], sort_keys=True, indent=4))
    for i in range(len(response.json())):
        if response.json()[i]['timeToStation'] < 200:
            print(response.json()[i]['lineId'], ":  ",response.json()[i]['timeToStation'])
            timestamp = response.json()[i]['timestamp']
            timeToStation = response.json()[i]['timeToStation']
            timestamp, ts = timeConverter(timestamp,timeToStation)
            store[response.json()[i]['id']] = [response.json()[i]['lineId'], timestamp, ts]
    print(store)
    lastresponse = response
    time.sleep(40)
    
