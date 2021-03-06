import RPi.GPIO as gpio
import time
import requests
import json
import datetime
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import urllib.request
from urllib.request import urlopen

gpio.setmode(gpio.BCM)

trig = 23
echo = 24
maxsize = 5
store = {}
counter = 0
traffic_poll = 0
buses_file = None
data_file = None

print("Distance Measurement in Progress")

gpio.setup(trig,gpio.OUT)
gpio.setup(echo,gpio.IN)

gpio.output(trig,False)
print("Waiting for Sensor to Settle")
time.sleep(2)
def initGoogleSheet(sheetname,sheet):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('SIOT-bbab5a9d0c4f.json', scope)
    gc = gspread.authorize(credentials)
    wks = gc.open(sheetname).get_worksheet(sheet)
    entries = len(wks.col_values(1)) + 1
    print('initiate sheet')
    return entries, wks
def updateSheet(entries,worksheet,data):
    print('updatingSheet')
    worksheet.append_row(data)
    print('updatedSheet')
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
def weatherRequest(response, tic):
    if time.time()-tic > 300 or response == {}:
        response = requests.get("http://api.openweathermap.org/data/2.5/weather?lat=51.474520&lon=-0.13234&APPID=6be8e1e50dafc734a74f13e0360e68df")
        tic = time.time()
    main = response.json()['weather'][0]['main']
    description = response.json()['weather'][0]['description']
    feels_like = response.json()['main']['feels_like']
    temp = response.json()['main']['temp']
    clouds = response.json()['clouds']['all']
    wind_speed = response.json()['wind']['speed']
    return response, main, description, feels_like, temp, clouds,wind_speed, tic
def pulse(delay):
    pulse_start = 0
    pulse_end = 0
    gpio.output(trig,True)
    time.sleep(0.00001)
    gpio.output(trig,False)
    now = time.time()
    while gpio.input(echo) == 0:
        pulse_start = time.time()
        if time.time() - now > 60:
            pulse_start = 0
            break
    while gpio.input(echo) == 1:
        pulse_end = time.time()
        if time.time() - now > 60:
            pulse_end = 0
            break
    
    if pulse_start == pulse_end:
        time.sleep(60)
        
    pulse_duration = pulse_end - pulse_start
    distance = round(pulse_duration * 17150, 2)
    time.sleep(delay)
    return distance

def trafficRequest(store):
    responseTo = requests.get("https://api.tfl.gov.uk/StopPoint/490008978N2/Arrivals")
    if responseTo.status_code == 200:
        responseTo = responseTo.json()
    else:
        return store
    responseFrom = requests.get("https://api.tfl.gov.uk/StopPoint/490008978N1/Arrivals")
    if responseFrom.status_code == 200:
        responseFrom = responseFrom.json()
    else:
        return store
    for i in range(len(responseTo)):
        responseItem = responseTo[i]
        if responseItem['timeToStation'] < 200:
            timestamp = responseItem['timestamp']
            timeToStation = responseItem['timeToStation']
            timestamp, ts = timeConverter(timestamp,timeToStation)
            store[responseItem['id']] = [responseItem['lineId'], timestamp, ts,'to']
    for i in range(len(responseFrom)):
        responseItem = responseFrom[i]
        if responseItem['timeToStation'] < 200:
            timestamp = responseItem['timestamp']
            timeToStation = responseItem['timeToStation']
            timestamp, ts = timeConverter(timestamp,timeToStation)
            store[responseItem['id']] = [responseItem['lineId'], timestamp, ts,'from']
    return store


try:
    gate = False
    tic = 0
    response = {}
    while True:
        time.sleep(20)
        print('sleeping')
        while datetime.datetime.today().hour < 23 and  datetime.datetime.today().hour > 5:
            if time.time() - traffic_poll > 40:
                store = trafficRequest(store)
                traffic_poll = time.time()
            todelete = []
            for i in store.keys():
                if time.time() - store[i][2]  > 120:
                    current_bus = [i,store[i][0],store[i][1],store[i][2],store[i][3]]
                    bus_entries, bus_gs = initGoogleSheet('Buses',0)
                    if bus_entries > 1000:
                        bus_entries, bus_gs = initGoogleSheet('Buses',0)
                    bus_entries = updateSheet(bus_entries,bus_gs,current_bus)
                    with open('buses.csv','a',newline='') as buses_file:
                        buses_writer = csv.writer(buses_file, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        buses_writer.writerow(current_bus)
                    todelete.append(i)
            for i in todelete:
                del(store[i])
            current = pulse(0.1)
            if current < 40 or current > 2000:
                timestampI = time.time()
                timestamp = time.ctime(int(timestampI))
                response, main, description, feels_like, temp, clouds,wind_speed, tic = weatherRequest(response,tic)
                now = time.time()
                sectionCounter = 0
                while time.time() - now < 5:
                    current = pulse(0.1)
                    if current < 40 or current > 2000:
                        now = time.time()
                        if gate == False:
                            counter += 1
                            sectionCounter += 1
                            gate = True
                            print(sectionCounter)
                    elif current > 50 and current < 100:
                        gate = False
                recentbuses = []
                mostrecent = None
                for i in store.keys():
                    if time.time()-store[i][2] > 0:
                        if mostrecent == None:
                            mostrecent = i
                        else:
                            if store[i][2] > store[mostrecent][2]:
                                mostrecent = i
                        recentbuses.append(i)
                current_data = [timestamp, sectionCounter, main, description, feels_like, temp, clouds,wind_speed, ' '.join(recentbuses) , mostrecent]
                data_entries, data_gs = initGoogleSheet('SIOT_data',0)
                if data_entries > 1000:
                    data_entries, data_gs = initGoogleSheet('SIOT_data',0)                 
                data_entries = updateSheet(data_entries,data_gs,current_data)
                with open('data.csv','a',newline='') as data_file:
                    data_writer = csv.writer(data_file, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    data_writer.writerow(current_data)
                urllib.request.urlopen("https://api.thingspeak.com/update?api_key=M47T7FFSVW26V7CR&field2=0"+str(sectionCounter))
                time.sleep(20)
finally:
    if buses_file != None:
        buses_file.close()
    if data_file != None:
        data_file.close()
    gpio.cleanup()
    print(counter)
