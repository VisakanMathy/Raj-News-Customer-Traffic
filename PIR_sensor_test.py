import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
PIR_PIN = 9
LED_PIN = 7
PIR_PIN2 = 8

GPIO.setup(PIR_PIN,GPIO.IN)
GPIO.setup(LED_PIN,GPIO.OUT)
GPIO.setup(PIR_PIN2,GPIO.IN)

print "PIR Module Test (CTRL+C to exit)"

time.sleep(2)
print "Ready"

while True:
	#if GPIO.input(PIR_PIN):
	#	print "Motion Detected!"
	time.sleep(0.1)
	m1 =   GPIO.input(PIR_PIN)
	m2 = GPIO.input(PIR_PIN)
	print m1,m2
	if m1 and  m2:
		GPIO.output(LED_PIN,1)
	else:
		GPIO.output(LED_PIN,0)
