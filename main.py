import os
import sys
sys.path.append("app")
from ota_updater import OTAUpdater
import utime, ubinascii, math   #add urequests from google sheets
from machine import I2C, ADC, Pin

from time import sleep
import tasos


def download_and_install_update_if_available():
     
     try:
          tasos.connectwifi()
     except:
          tasos.deep(60000)
     o = OTAUpdater('https://github.com/nrovatsou/GPS_OTA')
     print("-------------------------------")
     print("GitHub Repo", o.github_repo)
     print("Main dir: ", o.main_dir)
     print("New version dir: ", o.new_version_dir)
     print("----------------------------------------")
     o.check_for_update_to_install_during_next_reboot()
     o.install_update_if_available_after_boot('COSMOTE-179663', 'DYR7K3QY7HDU469A')  #SSID and PASSWORD are OBSOLETE

def start():
     # your custom code goes here. Something like this: ...
     # from main.x import YourProject
     # project = YourProject()
     # ...
    import tasos 

    print("Starting R2....")
    
    tasos.Internetime()
    tasos.init()
    #STARTUP FUNCTIONALITY, COPY FROM EXISTING MAIN
    #Connect WIFI
    #PROVIDE MQTT CREDENTIALS
    #SEND MESSAGES
    #KEEP CHECKING RESPONSES AND TAKE ACTION ACCORDINGLY.  GO TO DEEPSLEEP AFTER A WHILE?
    tasos.startup()
   


def boot():
     download_and_install_update_if_available()
     start()


boot()     
