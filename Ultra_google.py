import RPi.GPIO as gpio
import time
import requests
import json
import datetime
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
    if entries > 1000:
        entries, wks = initGoogleSheet(sheetname,sheet + 1)
    return entries, wks
def updateSheet(entries,worksheet,data):
    for i in range(len(data)):
        if isinstance(data[i],list):
            worksheet.update_cell(entries,i+1, ' '.join(data[i]))
        else:
            worksheet.update_cell(entries,i+1,data[i])
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
	gpio.output(trig,True)
	time.sleep(0.00001)
	gpio.output(trig,False)

	while gpio.input(echo) == 0:
		pulse_start = time.time()

	while gpio.input(echo) == 1:
		pulse_end = time.time()

	pulse_duration = pulse_end - pulse_start
	distance = round(pulse_duration * 17150, 2)
	time.sleep(delay)
#	print(distance)
	return distance

def trafficRequest(store):
    responseTo = requests.get("https://api.tfl.gov.uk/StopPoint/490008978N2/Arrivals").json()
    responseFrom = requests.get("https://api.tfl.gov.uk/StopPoint/490008978N1/Arrivals").json()
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
data_entries, data_gs = initGoogleSheet('SIOT_data',0)
bus_entries, bus_gs = initGoogleSheet('Buses',0)
try:
    gate = False
    tic = 0
    response = {}
    while True:
        time.sleep(20)
        while datetime.datetime.today().hour < 23 and  datetime.datetime.today().hour > 6:
            if time.time() - traffic_poll > 40:
                store = trafficRequest(store)
                traffic_poll = time.time()
            todelete = []
            for i in store.keys():
                if time.time() - store[i][2]  > 120:
                    current_bus = [i,store[i][0],store[i][1],store[i][2],store[i][3]]
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
                current_data = [timestamp, sectionCounter, main, description, feels_like, temp, clouds,wind_speed,recentbuses,mostrecent]
                if data_entries > 1000:
                    data_entries, data_gs = initGoogleSheet('SIOT_data',0)                 
                data_entries = updateSheet(data_entries,data_gs,current_data)
                with open('data.csv','a',newline='') as data_file:
                    data_writer = csv.writer(data_file, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    data_writer.writerow(current_data)
	#			store(counter,response)
	#		print(counter)
finally:
	if buses_file != None:
		buses_file.close()
	if data_file != None:
		data_file.close()
	gpio.cleanup()
	print(counter)
