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
def weatherRequest():
	response = requests.get("http://api.openweathermap.org/data/2.5/weather?lat=51.474520&lon=-0.13234&APPID=6be8e1e50dafc734a74f13e0360e68df")
	text = json.dumps(response.json(), sort_keys=True, indent=4)
	print(text)
	return text
def makeRequest(timestamp,response,tic):
	if timestamp - tic < 300:
		return tic, response
	else:
		tic = time.time()
		response = weatherRequest()
		return tic, response
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

	while True:
		current = pulse(0.1)
		if current < 40 or current > 2000:
			timestampI = time.time()
			timestamp = time.ctime(int(timestampI))
			now = time.time()
			while time.time() - now < 1:
				current = pulse(0.1)
				if current < 40 or current > 2000:
					now = time.time()
					if gate == False:
						counter += 1
						gate = True
						print(timestamp)
						print(counter)
				elif current > 50 and current < 100:
					gate = False
				print("Distance: ", current , "cm")
		if time.time() - traffic_poll > 40:
			store = trafficRequest(store)
			traffic_poll = time.time()
		todelete = []
		for i in store.keys():
			if time.time() - store[i][2] > 10:
				print(store[i])
				with open('buses.csv','a',newline='') as buses_file:
					buses_writer = csv.writer(buses_file, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
					buses_writer.writerow([i,store[i]])
				todelete.append(i)
		for i in todelete:
			del(store[i])
#			store(counter,response)
#		print(counter)
finally:
	gpio.cleanup()
	print(counter)
