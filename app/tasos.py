from machine import Pin, UART

import wifimgr
from umqttsimple import MQTTClient
#Import utime library to implement delay
import utime, time
import json
import machine
#import struct
from ublox import UBlox
from machine import WDT

#GPS Module UART Connection
#global realm, asset_id, pass1, latitude, longitude, satellites, gpsTime

#Used to Store NMEA Sentences
buff = bytearray(255)

TIMEOUT = False

#store the status of satellite is fixed or not
FIX_STATUS = False

realm="master"
asset_id="56dUTOPjL5eCPbiHGgbBdT"
pass1="0ItMPMpWHP4svaL8VujjfRw5GQdCh1Tz"

client_id='maria_client_1'
mqtt_server = '79.131.103.193'

gps_module = UART(2, baudrate=9600, tx=17, rx=16)

wdt = WDT(timeout=600000)  # enable it with a timeout of 10 min.

 #Store GPS Coordinates
latitude = ""
longitude = ""
satellites = ""
gpsTime = ""


ind=0

def init():
#  realm="master"
#  asset_id="56dUTOPjL5eCPbiHGgbBdT"
#  pass1="0ItMPMpWHP4svaL8VujjfRw5GQdCh1Tz"

#  client_id='maria_client_1'
#  mqtt_server = '79.131.103.193'

#  gps_module = UART(2, baudrate=9600, tx=17, rx=16)

#  wdt = WDT(timeout=600000)  # enable it with a timeout of 10 min.


 ind=0

#print gps module connection details
 print(gps_module)






def deep (duration):
    for y in range(0,10):
      try:
        import machine
        #print('Going to Deep Sleep now...')
        machine.deepsleep(duration) #milliseconds
      except:
        utime.sleep_ms(500) 

def Internetime():
     try:
        settime()
        print("Time Set")
        utime.sleep_ms(2000)
     except:
        print("No Internet, Time not Set")
        deep(30000)

def connectwifi():
     wlan = wifimgr.get_connection()
     if wlan is None:
          print("Could not initialize the network connection.")
          deep(60000)

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  utime.sleep_ms(10000)
  machine.reset()

def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  user1=realm+":mqttuser"
  client = MQTTClient(client_id, mqtt_server, port=8883, user=user1, password=pass1, ssl=True)  
  #def __init__(self, client_id, server, port=0, user=None, password=None, keepalive=0, ssl=False, ssl_params={}):
  #client.set_callback(sub_cb)
  print("Opening connection.....")
  client.connect()
  #client.subscribe(topic_sub)
  print("USER: ", user1)
  print('Connected to %s MQTT broker' % (mqtt_server))
  return client

#function to get gps Coordinates
def getPositionData(gps_module):
    global FIX_STATUS, TIMEOUT, latitude, longitude, satellites, gpsTime
    
    #run while loop to get gps data
    #or terminate while loop after 2 seconds timeout
    timeout = time.time() + 1   # 2 seconds from now
            
    while True:
        #gps_module.readline()
    #buff = str(gps_module.readline())
        # print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        # print ("UART data is: ", buff)
        # print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        #parse $GPGGA term
        #b'$GPGGA,094840.000,2941.8543,N,07232.5745,E,1,09,0.9,102.1,M,0.0,M,,*6C\r\n'
        #print(buff)
        parts = buff.split(',')
        
        #if no gps displayed remove "and len(parts) == 15" from below if condition
        if (parts[0] == "b'$GNGGA" and len(parts) == 15):
            if(parts[1] and parts[2] and parts[3] and parts[4] and parts[5] and parts[6] and parts[7]):
                print(buff)
                #print("Message ID  : " + parts[0])
                #print("UTC time    : " + parts[1])
                #print("Latitude    : " + parts[2])
                #print("N/S         : " + parts[3])
                #print("Longitude   : " + parts[4])
                #print("E/W         : " + parts[5])
                #print("Position Fix: " + parts[6])
                #print("n sat       : " + parts[7])
                
                latitude = convertToDigree(parts[2])
                # parts[3] contain 'N' or 'S'
                if (parts[3] == 'S'):
                    latitude = -latitude
                longitude = convertToDigree(parts[4])
                # parts[5] contain 'E' or 'W'
                if (parts[5] == 'W'):
                    longitude = -longitude
                satellites = parts[7]
                gpsTime = parts[1][0:2] + ":" + parts[1][2:4] + ":" + parts[1][4:6]
                FIX_STATUS = True
                break
        else:
            break
            #print("Data read is: ",parts[0])     
              
        # if (time.time() > timeout):
        #     TIMEOUT = True
        #     break
        # utime.sleep_ms(500)
        
#function to convert raw Latitude and Longitude
#to actual Latitude and Longitude
def convertToDigree(RawDegrees):

    RawAsFloat = float(RawDegrees)
    firstdigits = int(RawAsFloat/100) #degrees
    nexttwodigits = RawAsFloat - float(firstdigits*100) #minutes
    
    Converted = float(firstdigits + nexttwodigits/60.0)
    Converted = '{0:.6f}'.format(Converted) # to 6 decimal places
    return str(Converted)

def checksum(data):
        '''return a checksum tuple for a message'''
        # if data is None:
        #     data = buf[2:-2]
        cs = 0
        ck_a = 0
        ck_b = 0
        for i in data:
            if type(i) is str:
               
                ck_a = (ck_a + ord(i)) & 0xFF
            else:
                ck_a = (ck_a + i) & 0xFF
            ck_b = (ck_b + ck_a) & 0xFF
        return (ck_a, ck_b)

def send_message(gps_module, msg_class, msg_id, payload):
        '''send a ublox message with class, id and payload'''
        import struct
        buf=[]
        s1=0xb5
        s2=0x62
        buf = struct.pack('BBBBH', s1, s2, msg_class, msg_id, len(payload))
        print("Data sent without payload", buf, "Payload length: ", len(payload))
        buf = buf+payload 

        (ck_a, ck_b) = checksum(buf[2:])
        
        buf += struct.pack('<BB', ck_a, ck_b)
        dn=gps_module.write(buf)    
        print("Data sent is: ", buf, "CKA: ", ck_a, "CKB: ", ck_b, "Number of bytes: ", dn)


def loop_serial(gps_module, substring, substring1):
    start = time.ticks_ms()
    while True:
        buff=[ ]
        if gps_module.any():   
                utime.sleep(0.3)
                buff = str(gps_module.readline()) 
                print("DATA RECEIVED is: ", buff)
                if substring in buff:
                    print("ACK or NACK RECEIVED: ", buff, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                elif substring1 in buff:
                    getPositionData(gps_module,buff)
                    pass
                    #break
                print(time.ticks_diff(time.ticks_ms(), start))
        
        if time.ticks_diff(time.ticks_ms(), start)>120000:
            # start = time.ticks_ms()
            # send_message(gps_module,msg_class, msg_id, msg_payload)
            break
def loop_ack(gps_module, substring, substring1):
    
    #buffer = bytearray(255)
    start = time.ticks_ms()
    while True:
        buffer=bytearray(255)
        if gps_module.any():   
                utime.sleep(0.3)
                gps_module.readinto(buffer) 
                #buff=str(buff)
                #print("DATA RECEIVED is: ", buffer)
                temp=str(buffer)
                if substring in temp:
                    print("-------------------------------------------------------------")
                    print("")
                    print("ACK or NACK RECEIVED: ", temp, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    print("-------------------------------------------------------------")
                    print("")
                    print(time.ticks_diff(time.ticks_ms(), start))
                    if time.ticks_diff(time.ticks_ms(), start)>10000:
                       break
        
        if time.ticks_diff(time.ticks_ms(), start)>20000:
            # start = time.ticks_ms()
            # send_message(gps_module,msg_class, msg_id, msg_payload)
            break


def startup():
    cnt=0
    err=0
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ POWER @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    substring ="b5b"
    substring1="GNGGA" #or "$GAGGA"
    #-----------------------UBX-CFG-PM2
    msg_class=0x06
    msg_id=0x3B
    #msg_payload_int=[0x01, 0x06, 0x00, 0x00, 0x0E, 0x94, 0x40, 0x01, 0x00, 0x7D, 0x00, 0x00, 0x20, 0x4E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x2C, 0x01, 0x00, 0x00, 0x4F, 0xC1, 0x03, 0x00, 0x87, 0x02, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x64, 0x40, 0x01, 0x00]
    msg_payload_int=[0x01, 0x06, 0x00, 0x00, 0x0E, 0x94, 0x40, 0x01, 0x40, 0x77, 0x1B, 0x00, 0xC0, 0xD4, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x2C, 0x01, 0x00, 0x00, 0x4F, 0xC1,  0x03, 0x00, 0x87, 0x02, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x64, 0x40, 0x01, 0x00]  

    msg_payload=bytearray(msg_payload_int)
    # for x in range(1):
    #   send_message(gps_module,msg_class, msg_id, msg_payload)
    #   #utime.sleep(0.1)
    #   loop_ack(gps_module, substring, substring1)
    #   utime.sleep(3)
    # send_message(gps_module,msg_class, msg_id, msg_payload)
    # utime.sleep(0.1)
    # loop_serial(gps_module, substring, substring1)

    #   --------------------UBX-CFG-GNSS
    msg_class=0x06
    msg_id=0x3E
    #msg_id=0x01
    #msg_payload_int=[0x00, 0x00, 0x08, 0x07, 0x00, 0x08, 0x10, 0x00, 0x00, 0x00, 0x01, 0x01, 0x01, 0x01, 0x03, 0x00, 0x00, 0x00, 0x01, 0x01, 0x02, 0x04, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01, 0x03, 0x08, 0x10, 0x00, 0x00, 0x00, 0x01, 0x01, 0x04, 0x00, 0x08, 0x00, 0x00, 0x00, 0x01, 0x01, 0x05, 0x00, 0x03, 0x00, 0x00, 0x00, 0x01, 0x01, 0x06, 0x08, 0x0E, 0x00, 0x00, 0x00, 0x01, 0x01]  #GALILEO ONLY   #GALILEO E5b
    #msg_payload_int=[0x00, 0x00, 0xFF, 0x01, 0x00, 0x04, 0x04, 0x00, 0x01, 0x00, 0x00, 0x01]    #GPS L1C/A
    msg_payload_int=[0x00, 0x00, 0x20, 0x07, 0x00, 0x08, 0x10, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0x01, 0x03, 0x00, 0x00, 0x00, 0x01, 0x01, 0x02, 0x04, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01, 0x03, 0x08, 0x10, 0x00, 0x00, 0x00, 0x01, 0x01, 0x04, 0x00, 0x08, 0x00, 0x00, 0x00, 0x01, 0x01, 0x05, 0x04, 0x08, 0x00, 0x00, 0x00, 0x01, 0x01, 0x06, 0x08, 0x0E, 0x00, 0x00, 0x00, 0x01, 0x01]
    msg_payload=bytearray(msg_payload_int)
    for x in range(1):
        send_message(gps_module,msg_class, msg_id, msg_payload)
        #utime.sleep(0.1)
        loop_ack(gps_module, substring, substring1)
        loop_serial(gps_module, substring, substring1)
        #-----------------------UBX-CFG-CFG
        msg_class=0x06
        msg_id=0x09
        msg_payload_int=[0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01]
        msg_payload=bytearray(msg_payload_int)
        send_message(gps_module,msg_class, msg_id, msg_payload)
        #loop_serial(gps_module, substring, substring1)
        utime.sleep(1)
    
    msg_class=0x0A
    msg_id=0x28
    #msg_payload_int=[0x00, 0x00, 0x00, 0x03, 0x00, 0x04, 0x0A, 0x00, 0x01, 0x00, 0x00, 0x01, 0x02, 0x04, 0x0A, 0x00, 0x01, 0x00, 0x00, 0x01, 0x05, 0x05, 0x0A, 0x00, 0x01, 0x00, 0x00, 0x01]
    #msg_payload_int=[0x00, 0x00, 0x05, 0x01, 0x00, 0x05, 0x0F, 0x00, 0x01, 0x00, 0x00, 0x01]
    msg_payload_int=[]
    msg_payload=bytearray(msg_payload_int)
    for x in range(3):
        send_message(gps_module,msg_class, msg_id, msg_payload)
        #utime.sleep(0.1)
        loop_ack(gps_module, substring, substring1)
        utime.sleep(1)

    #-----------------------UBX-CFG-CFG
    msg_class=0x06
    msg_id=0x09
    msg_payload_int=[0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01]
    msg_payload=bytearray(msg_payload_int)
    # send_message(gps_module,msg_class, msg_id, msg_payload)
    # utime.sleep(0.1)
    # loop_serial(gps_module, substring, substring1)
    #SEND RESET

    #-----------------------UBX-LOG-CREATE
    msg_class=0x21
    msg_id=0x04
    msg_payload_int=[0x01]
    msg_payload=bytearray(msg_payload_int)

    if(FIX_STATUS == True):
        print("-----------------------")
        print("fix......")
        print("Latitude: ",latitude)
        print("Longtitude: ", longitude)
        print("No. of Stellites: ", satellites)
        print("GPS Time: ", gpsTime)
        print("-----------------------")
        
        try:
        
            client = connect_and_subscribe()
            topic=realm+"/maria_client_1/writeattributevalue/location/"+asset_id
            print("TOPIC: ", topic)
            topic_pub=bytes(topic, 'utf-8')
            #topic_pub=b'master/maria_client_1/writeattributevalue/location/56dUTOPjL5eCPbiHGgbBdT'
            coordinates1=[longitude,latitude]
            a_location =  { "type": "Point", "coordinates": coordinates1}
            #a_location = { "type": "Point", "coordinates": [21.08434664081000,38.491930602423736] }
            #client.publish(topic_pub, a_location)
            print("COORDINATES: ", a_location)
            print("**************************")
            client.publish(topic_pub, json.dumps(a_location))
            print ("Location SENT!")
            client.disconnect()
            print("Connection Closed.")
            utime.sleep_ms(10000)
            
            
        except OSError as e:
            print("Error Sending Message: ", e)
            utime.sleep_ms(10000)
            restart_and_reconnect()


        FIX_STATUS = False
        #utime.sleep_ms(300000)

    deep(1000)
    wdt.feed()
    print("Watchdog Reset")
        


