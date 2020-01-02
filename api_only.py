import time
import requests
import json
import datetime
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def initGoogleSheet(sheetname,sheet):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('SIOT-bbab5a9d0c4f.json', scope)
    gc = gspread.authorize(credentials)
    wks = gc.open(sheetname).get_worksheet(sheet)
    entries = len(wks.col_values(1)) + 1
    if entries > 1000:
        entries, wks = initGoogleSheet(sheetname,sheet + 1)
    return entries, wks
def updateSheet(entries,worksheet,data):
    print('updatingSheet')
    worksheet.append_row(data)
    entries += 1
    return entries
def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()
def timeConverter(timestamp,timeToStation):
    if len(timestamp) == 28:    
        timestamp = timestamp[0:25]+timestamp[27]
    a = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(seconds = timeToStation)
    return time.ctime(int(unix_time(a))), unix_time(a)
def weatherRequest(response):
    repeat = False
    new_response = requests.get("http://api.openweathermap.org/data/2.5/weather?lat=51.474520&lon=-0.13234&APPID=6be8e1e50dafc734a74f13e0360e68df")
    print('weatherRequested')
    if response != {}:
        if response.json()['dt'] == new_response.json()['dt']:
            repeat = True  
    main = new_response.json()['weather'][0]['main']
    description = new_response.json()['weather'][0]['description']
    feels_like = new_response.json()['main']['feels_like']
    temp = new_response.json()['main']['temp']
    clouds = new_response.json()['clouds']['all']
    wind_speed = new_response.json()['wind']['speed']
    dt = new_response.json()['dt']
    return new_response, main, description, feels_like, temp, clouds,wind_speed, repeat, dt
def trafficRequest(store):
    responseTo = requests.get("https://api.tfl.gov.uk/StopPoint/490008978N2/Arrivals").json()
    responseFrom = requests.get("https://api.tfl.gov.uk/StopPoint/490008978N1/Arrivals").json()
    print("trafficRequested")
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
    return store
traffic_poll = 0
weather_poll = 0
store = {}
response = {}
while True:
    while datetime.datetime.today().hour < 23 and  datetime.datetime.today().hour > 6 or True:
        time.sleep(5)
        if time.time() - weather_poll > 200:
            weather_poll = time.time()
            response, main, description, feels_like, temp, clouds,wind_speed, repeat, dt = weatherRequest(response)
            if repeat == False:
                weather_entries, weather_gs = initGoogleSheet('Weather',0)
                if weather_entries > 1000:
                   weather_entries, weather_gs = initGoogleSheet('Weather',0)
                weather_entries = updateSheet(weather_entries,weather_gs,[main, description, feels_like, temp, clouds,wind_speed,dt]) 
        
        if time.time() - traffic_poll > 40:
            store = trafficRequest(store)
            traffic_poll = time.time()
        todelete = []
        
        for i in store.keys():
            if time.time() - store[i][2]  > 120:
                current_bus = [i,store[i][0],store[i][1],store[i][2],store[i][3]]
                bus_entries, bus_gs = initGoogleSheet('Buses2',0)
                if bus_entries > 1000:
                    bus_entries, bus_gs = initGoogleSheet('Buses2',0)
                bus_entries = updateSheet(bus_entries,bus_gs,current_bus)
                todelete.append(i)
        for i in todelete:
            del(store[i])