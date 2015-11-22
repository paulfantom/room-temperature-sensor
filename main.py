#!/usr/bin/env python

from sys import exit
import paho.mqtt.client as mqtt
from time import sleep, strftime

SERVER_IP = 'localhost'

ALTITUDE = 211
USE_APPARENT = False
PRESSURE = None
REAL_TEMP = None
HUMIDITY = None
BUS = 1
SAMPLES = 1 

def apparent_temperature(temp,humidity):
    if humidity is None:
        return temp
    ''' http://www.engineeringtoolbox.com/water-vapor-saturation-pressure-air-d_689.html '''
    T = float(temp)+273.15
    e = 2.71828
    pw = e**(77.345+0.0057*T-7235/T) / T**8.2
    ''' Steadman, R.G., 1984: A universal scale of apparent temperature. '''
    at = -1.3 + 0.92*float(temp) + 2.2*(float(humidity)/100)*(pw/1000)
    return round(at,3)

def read_temp():
  temp = 0
  hum = 0
  try:
    import core.sht21 as sht21
    sht = sht21.SHT21(BUS)
    for i in range(SAMPLES):
      temp += sht.read_temperature()
      hum += sht.read_humidity()
#      if(i < SAMPLES):
#        delay(5s)
    
    temp /= SAMPLES
    hum /= SAMPLES
  except Exception as e:
    print "Cannot read temperature; exiting"
    print e
    exit(127)
  return (temp,hum)

def read_press(read_temp=False):
  temp = 0
  press = 0
  try:
    import core.bmp085 as bmp085
    pres_sensor = bmp085.BMP085(busnum=BUS, mode=bmp085.BMP085_HIGHRES)
    
    if read_temp:
      for i in range(SAMPLES):
        temp += pres_sensor.read_temperature()
      temp /= SAMPLES
    
    for i in range(SAMPLES):
      press += pres_sensor.read_pressure()
   
    press = float(press)
    press /= SAMPLES
    press /= 100  # convert Pa to hPa
  except Exception as e:
    print("Cannot connect to pressure sensor")
    print(e)
    pass
  
  return (press,temp)

def pressure_to_sealevel(press,temp,altitude):
    try:
      a = 0.0065 * float(altitude)
    except TypeError:
      return press
    b = a / (float(temp) + a + 273.15)
    p = press / (1 - b)**(5.257)

    return p

def moving_avg(last,new):
    new = 2*last + new
    return new / 3
    
def get_data(last_temperature=None,last_humidity=None,last_pressure=None):
    (temperature, humidity) = read_temp();
    (pressure,t) = read_press(True);
    pressure = pressure_to_sealevel(pressure,t,ALTITUDE);
    temperature = round(temperature,1)
    
    if last_pressure is not None:
        pressure = moving_avg(last_pressure,pressure)
    if last_temperature is not None:
        temperature = moving_avg(last_temperature,temperature) 
        temperature = round(temperature,1)
    if last_humidity is not None:
        humidity = moving_avg(last_humidity,humidity)

    apparent = round(apparent_temperature(temperature,humidity),1)
    humidity = round(humidity,1)
    pressure = round(pressure,1)
    
    if USE_APPARENT: current = apparent
    else: current = temperature 
    print strftime("%m-%d %H:%M")+" >>> H:"+str(humidity), "P:"+str(pressure), "T:"+str(temperature), "A:"+str(apparent), "C:"+str(current)

    return [{'topic':"room/1/temp_real", 'payload':str(temperature), 'retain':True},
            {'topic':"room/1/temp_feel", 'payload':str(apparent), 'retain':True},
            {'topic':"room/1/humidity", 'payload':str(humidity), 'retain':True},
            {'topic':"room/1/pressure", 'payload':str(pressure), 'retain':True},
            {'topic':"room/1/temp_current", 'payload':str(current), 'retain':True}]

def check(client):
    print strftime("%m-%d %H:%M")+" PRV H:"+str(HUMIDITY)+" P:"+str(PRESSURE)+" T:"+str(REAL_TEMP)
    msgs = get_data(REAL_TEMP,HUMIDITY,PRESSURE)
    for data in msgs:
        client.publish(**data) 

def on_connect(client, userdata, flags, rc):
    client.subscribe("room/1/use_apparent")
    client.subscribe("room/1/temp_real")
    client.subscribe("room/1/humidity")
    client.subscribe("room/1/pressure")

def on_message(client, userdata, msg):
    if(msg.topic == 'room/1/use_apparent'):
        global USE_APPARENT
        USE_APPARENT = bool(int(msg.payload))
    if(msg.topic == 'room/1/temp_real'):
        global REAL_TEMP
        REAL_TEMP = float(msg.payload)
    if(msg.topic == 'room/1/humidity'):
        global HUMIDITY
        HUMIDITY = float(msg.payload)
    if(msg.topic == 'room/1/pressure'):
        global PRESSURE
        PRESSURE = float(msg.payload)

if __name__ == '__main__':
    #print(get_data()) 
    client = mqtt.Client('Room 1')
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(SERVER_IP, 1883, 60)
    client.loop_start()
    # delay to parse incoming msgs
    sleep(2)
    while True:
        check(client)
        sleep(60)
