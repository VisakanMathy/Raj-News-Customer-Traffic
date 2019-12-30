import requests
import json

def jprint(obj):
	text = json.dumps(obj,sort_keys=True, indent = 4)
	print(text)
response = requests.get("http://api.openweathermap.org/data/2.5/weather?lat=51.474520&lon=-0.13234&APPID=6be8e1e50dafc734a74f13e0360e68df")
jprint(response.json())
