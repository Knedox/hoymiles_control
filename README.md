# RaspberryPi based python script to control Hoymiles HM-* inverters
This script allows you to receive and control commands and data from your Hoymiles inverter with RaspberryPi

__WORK IN PROGRESS__

## How to use
- Get RaspberryPi with nRF24L01+ board
- pip3 install circuitpython-nrf24l01 Adafruit-Blinka crcmod
- Modify _inverter_ser_ to your inverters serial number 
- Optional: modify _nrf.channel_ to one of _[3,23,40,61,75]_ if you dont get a response to the time package

## What works
- Receive Packages from Hoymiles
- Send Control Packages
  - Power Limit (non + persistent)
  - On/OFF
- Send request data packages
- Assemble multiple packages into one data package
- Re-request missing packages
- Check CRC's

## Limitations
- Currently you can send/receive just to/from one inverter at a time
- Data received back from the inverter is checked and assembled but not really parsed yet

## Examples
__setPowerLimit(inverter_serial, 50)__ -> limit power to 50 watt non-persistently

__setPowerLimit(inverter_serial, 50, True)__ -> limit power to 50% of max power non-persistently

__setPowerLimit(inverter_serial, 50, True, True)__ -> limit power to 50% of max power persistently


__sendControl(inverter_serial, CMD.OFF)__ -> inverter turns off

__sendControl(inverter_serial, CMD.ON)__ -> inverter turns on


__sendTime(inverter_ser)__ -> inverter responds with a complete data package

## Supported inverters
All inverters of the HM-* series should be supported
- HM-1500
- HM-1200
- HM-800
- HM-600
- HM-300 ?

## Hardware
For this script to work you need a RaspberryPi with nRF24L01+ board attached to pins 15-24


![image](/doc/nRF24L01_board.jpg)

The Board design can be found here https://oshwlab.com/kned/nrf24l01
you can [Order it here for 2$](https://cart.jlcpcb.com/quote?edaOrderUrl=https%3A%2F%2Feasyeda.com%2Forder&uuid=5e372097f60a4c3f8a8444d01f0f9e50&electropolishingOnlyNo=no&achieveDate=72&eadLink=2&fileId=3b8cb339fffe45deb827d48908847318&fromOrder=yes) or use your own manufacturer with gerber files in the repo

Additionally you need a nRF24L01+ SMD board (Ebay, Aliexpress...) and one 100uF 16V Capacitor

For the pinout see https://circuitpython-nrf24l01.readthedocs.io/en/latest/#pinout (SpiDev mode is used)


## Special thanks to
https://github.com/lumapu/ahoy

https://github.com/tbnobody/OpenDTU

and https://www.mikrocontroller.net/
