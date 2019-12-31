import RPi.GPIO as gpio
import time
import requests
import json
import datetime
import csv

gpio.setmode(gpio.BCM)

trig = 23
echo = 24
maxsize = 5
store = {}
counter = 0
traffic_poll = 0
buses_file = None

print("Distance Measurement in Progress")

gpio.setup(trig,gpio.OUT)
gpio.setup(echo,gpio.IN)

gpio.output(trig,False)
print("Waiting for Sensor to Settle")
time.sleep(2)

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
	return distance

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
    return store
	
try:
	gate = False
	tic = 0
	response = {}
	while True:
		if time.time() - traffic_poll > 40:
			store = trafficRequest(store)
			traffic_poll = time.time()
		todelete = []
		for i in store.keys():
			if time.time() - store[i][2]  > 120:
				print(store[i])
				with open('buses.csv','a',newline='') as buses_file:
					buses_writer = csv.writer(buses_file, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
					buses_writer.writerow([i,store[i][0],store[i][1],store[i][2],store[i][3]])
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
			while time.time() - now < 1:
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
			print(timestamp, main, description, feels_like, temp, clouds,wind_speed, store.keys())
		
#			store(counter,response)
#		print(counter)
finally:
	if buses_file != None:
		buses_file.close()
	gpio.cleanup()
	print(counter)
