#!/usr/bin/env python
import time
import board
import struct
import crcmod
import sys
import threading
import enum
from digitalio import DigitalInOut

# if running this on a ATSAMD21 M0 based board
# from circuitpython_nrf24l01.rf24_lite import RF24
from circuitpython_nrf24l01.rf24 import RF24

# invalid default values for scoping
SPI_BUS, CSN_PIN, CE_PIN = (None, None, None)

import spidev

SPI_BUS = spidev.SpiDev()  # for a faster interface on linux
CSN_PIN = 0  # use CE0 on default bus (even faster than using any pin)
CE_PIN = DigitalInOut(board.D22)  # using pin gpio22 (BCM numbering)


nrf = RF24(SPI_BUS, CSN_PIN, CE_PIN)


nrf.data_rate = 250
nrf.channel=23 #
nrf.auto_ack = True
nrf.set_auto_retries(3,15)
nrf.crc = 2
nrf.dynamic_payloads = True
nrf.pa_level = -18 # -18 ... 0
nrf.address_length=5


channels = [3,23,40,61,75]

dtu_ser = 99978563001
inverter_ser = 116180215597

nrf.open_rx_pipe(1, b'\01' + bytearray.fromhex(str(dtu_ser)[-8:]))



f_crc_m = crcmod.predefined.mkPredefinedCrcFun('modbus')
f_crc8 = crcmod.mkCrcFun(0x101, initCrc=0, xorOut=0)

class CMD:
    ON = 0
    OFF = 1
    RElastAction = 2
    LOCK = 3
    UNLOCK = 4
    ACTIVE_POWER_LIMIT = 11
    REACTIVE_POWER_LIMIT = 12
    POWER_FACTOR = 13
    LOCK_AND_ALARM = 20
    SELF_INSPECT = 40

class PacketType:
    TX_REQ_INFO = 0x15
    TX_REQ_DEVCONTROL = 0x51

# 0x100 -> persistent
# 0x1 -> relative (%)    
def setPowerLimit(dst, limit, relative = False, persist = False):
    mod = persist * 0x100
    mod+= relative 
    sendControl(dst, CMD.ACTIVE_POWER_LIMIT, limit * 20, mod)


def sendControl(dst, cmd, data = None, mod = 0):
    payload = bytearray(2)
    payload[0] = cmd
    if data is not None:
        payload+= data.to_bytes(2, 'big')
        payload+= mod.to_bytes(2, 'big')
        
    sendPacket(dst, PacketType.TX_REQ_DEVCONTROL, payload)
    
  
def sendTime(dst):
    payload = bytearray(13)
    payload[0] = 0x0B
    payload[2:5] = struct.pack('>L', int(time.time()))  
    payload[9] = 0x05

    sendPacket(dst, PacketType.TX_REQ_INFO, payload)


def sendPacket(dst, type, payload, frame_id = 0):
    packet = bytes([type])
    packet += bytearray.fromhex(str(dst)[-8:])
    packet += bytearray.fromhex(str(dtu_ser)[-8:])
    packet += int(0x80 + frame_id).to_bytes(1, 'big')

    packet += payload
    
    if len(payload) > 0:
        packet += struct.pack('>H', f_crc_m(payload)) 
    packet += struct.pack('B', f_crc8(packet))

    transmitPackage(packet) 


    
mutex = threading.Lock()

def transmitPackage(package):
    
    inv_esb_addr = b'\01' + package[1:5]
    
    mutex.acquire()
    nrf.listen = False
    nrf.open_tx_pipe(inv_esb_addr)
    nrf.auto_ack = True
    #print("sending",package[0:1].hex(), package[1:5].hex(),"->",package[5:9].hex(),package[9:10].hex(), ":",package[10:].hex())
    result = nrf.send(package)
    nrf.auto_ack = False
    nrf.listen = True 
    mutex.release()

    
def reRequest(dst, frame_id):
    print("request", frame_id)
    sendPacket(dst, PacketType.TX_REQ_INFO, b'', frame_id)
    
def parsePacket(packet):
    #print("got package: ", packet.hex())
    #print("modbus crc: ", packet[:-2].hex(), " ", struct.pack('>H',f_crc_m(packet[:-2])).hex(), " ", packet[-2:].hex())
    if struct.pack('>H',f_crc_m(packet[:-2])) != packet[-2:]: # crc check
        return
    offset = 50
    print("read:", int.from_bytes(packet[offset:offset + 2], byteorder='big', signed=False))  

    
def receive_loop():
    packetbuffer = [0] * 16
    maxPacketId = 0
    retry = 0
    lastAction = 0
    
    while True:
        mutex.acquire()
        if nrf.available():
            buffer = nrf.read()

            # drop on crc error
            if not f_crc8(buffer[0:-1]) == buffer[-1:][0]: 
                continue
            
            lastAction = time.time()
            
            # reset counter if this is first package
            if maxPacketId == 0: 
                packetbuffer=[0] * 16
                retry = 0
                print()
            
            print("received",buffer[0:1].hex(), buffer[1:5].hex(),"->",buffer[5:9].hex(),buffer[9:10].hex(), ":",buffer[10:].hex())
            
            packetId = buffer[9] & 0x7F
            
            packetbuffer[packetId] = buffer
            
            # try to find packet count
            if packetId >= maxPacketId:
                maxPacketId = packetId
                if buffer[9] & 0x80 == 0: # in this case there is more
                    maxPacketId+=1
                    
            # try to assemble full package
            packet = bytearray()
            for i in range(1,maxPacketId + 1):
                if packetbuffer[i] == 0:
                    packet = False
                    break
                packet += packetbuffer[i][10:-1]
            
            # if package is ok then parse it
            if packet:
                parsePacket(packet)
                maxPacketId = 0

        mutex.release()
        
        # re-request missing packages
        if maxPacketId > 0 and time.time() - lastAction > 0.1:
            retry+=1
 
            for i in range(1,maxPacketId + 1):
                if packetbuffer[i] == 0:
                    lastAction = time.time()
                    reRequest(inverter_ser, i)
                    break # can request just one package at a time
        
          
        if retry > 5:
            maxPacketId = 0 # drop package
            

         #   print("")
        
        
        time.sleep(0.005)

def master(count=5): 
    while True:
        # use struct.pack to structure your data
        # into a usable payload

        buffer = sendTime(inverter_ser) 

        
        time.sleep(5)
        nrf.print_details()


        

receive_thread = threading.Thread(target=receive_loop)
receive_thread.daemon = True
receive_thread.start()
 
nrf.print_details()

setPowerLimit(inverter_ser, 25)

master()