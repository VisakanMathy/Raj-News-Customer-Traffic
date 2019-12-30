import RPi.GPIO as gpio
import time
import requests
import json

gpio.setmode(gpio.BCM)

trig = 23
echo = 24
maxsize = 5
l = []

print("Distance Measurement in Progress")

gpio.setup(trig,gpio.OUT)
gpio.setup(echo,gpio.IN)

gpio.output(trig,False)
print("Waiting for Sensor to Settle")
time.sleep(2)
counter = 0
tic = 0
def weatherRequest():
	response = requests.get("http://api.openweathermap.org/data/2.5/weather?lat=51.474520&lon=-0.13234&APPID=6be8e1e50dafc734a74f13e0360e68df")
	text = json.dumps(response.json(), sort_keys=True, indent=4)
	print(text)
	return text
def trafficRequest():
	print('pending')
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
response = weatherRequest()
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
			tic,response = makeRequest(timestampI,response,tic)
#			store(counter,response)
#		print(counter)
finally:
	gpio.cleanup()
	print(counter)
