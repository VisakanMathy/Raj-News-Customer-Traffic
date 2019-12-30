import RPi.GPIO as gpio
import time
import queue

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
def apiCall()
def makeRequest(timestamp,response,tic):
	if timestamp - tic < 300:
		return tic, response
	else:
		tic = time.time()
		response = apiCall()
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
try:
	gate = False

	while True:
		current = pulse(0.1)
		if current < 40 or current > 2000:
			timestamp = time.ctime(int(time.time()))
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
			tic,response = makeRequest(timestamp,response,tic)
			store(counter,response)
#		print(counter)
finally:
	gpio.cleanup()
	print(counter)
