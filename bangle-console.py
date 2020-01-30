import sys
import asyncio
import array
from datetime import datetime
from bleak import discover
from bleak import BleakClient

address = "0DB07D6F-8F0F-4CB3-A801-0D9A868BE7CE"
UUID_NORDIC_TX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UUID_NORDIC_RX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
command = b"\x03\x10\
var f = require('Storage').open('ftclog', 'r');\n\x10\
var line = '';\n\x10\
while ((line != null && line != undefined) && (line.indexOf('\xFF') == -1)){\n\x10\
  line = f.readLine();\n\x10\
  print(line);\n\x10\
}\n\x10\
"

line = ""
fileName = ""
dataReceived = None
def uart_data_received(sender, data):
    try:
        global line
        global dataReceived
        line = line + str(data, 'utf-8')
        if(data != '' and data != None):
            dataReceived = datetime.now()

    except:
        e = sys.exc_info()[0]
        print("Error on data receieved: " + str(e) )
    finally:
        global loop

# You can scan for devices with:
async def discover_coroutine():
    try:
        devices = await discover()
        for d in devices:
            print(d)
    
    finally: 
        print("Done discover")

print("Connecting...")
async def command_coroutine(address, loop):
    async with BleakClient(address, loop=loop) as client:
        print("Connected")
        await client.start_notify(UUID_NORDIC_RX, uart_data_received)
        print("Writing command")
        c=command
        while len(c)>0:
          await client.write_gatt_char(UUID_NORDIC_TX, bytearray(c[0:20]), True)
          c = c[20:]

        global dataReceived
        await asyncio.sleep(10.0, loop=loop) # wait for a response
        lastDataReceivedDelta = datetime.now() - dataReceived
        print("Data last recieved: " + str(dataReceived) + " Delta:" + str(lastDataReceivedDelta.seconds))
        while (lastDataReceivedDelta.seconds < 10):
            await asyncio.sleep(10.0, loop=loop) # wait for a response
            lastDataReceivedDelta = datetime.now() - dataReceived
            print("Data last recieved: " + str(dataReceived) + " Delta:" + str(lastDataReceivedDelta.seconds))


        await client.disconnect()
        print("\r\n\r\nDone!")
        now = datetime.now()
        global fileName
        fileName = "ftclog-" + now.strftime("%Y-%m-%d-%H-%M-%S")#-%Y-%m-%d-%H-%M-%S" 
        f = open(fileName + ".csv", 'w')
        f.write(line)
        #print(line)

try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(discover_coroutine())
    loop.run_until_complete(command_coroutine(address, loop))
finally:
    print("finally!")
