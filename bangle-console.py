import sys
import asyncio
import array
from datetime import datetime
from bleak import discover
from bleak import BleakClient

address = "0DB07D6F-8F0F-4CB3-A801-0D9A868BE7CE"
UUID_NORDIC_TX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UUID_NORDIC_RX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
getFileCommand = b"\x03\x10\
Bangle.AppLog.beginSync();\n\x10\
"
deleteFileCommand = b"\x03\x10\
Bangle.AppLog.clearLog();\n\x10"

line = ""
fileName = ""
dataReceived = None
transferTimeout = 10
foundBangle = False

def uart_data_received(sender, data):
    try:
        global line
        global dataReceived
        if(data !="<!-- finished sync -->"):
            line = line + str(data, 'utf-8')
        if(data != '' and data != None and data !="<!-- finished sync -->"):
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
        global address
        global foundBangle
        for d in devices:
            if(address in str(d)):
                foundBangle = True
                print("Found Bangle")
                break
        

    finally:
        print("Done discover")

print("Connecting...")
async def getFile_coroutine(address, loop):
    async with BleakClient(address, loop=loop) as client:
        print("Connected")
        await client.start_notify(UUID_NORDIC_RX, uart_data_received)
        print("Writing command")
        c=getFileCommand
        while len(c)>0:
          await client.write_gatt_char(UUID_NORDIC_TX, bytearray(c[0:20]), True)
          c = c[20:]

        global dataReceived
        await asyncio.sleep(30.0, loop=loop) # wait for a response
        dataReceived = datetime.now()
        lastDataReceivedDelta = datetime.now() - dataReceived
        print("Data last recieved: " + str(dataReceived) + " Delta:" + str(lastDataReceivedDelta.seconds))
        while (lastDataReceivedDelta.seconds < transferTimeout):
            await asyncio.sleep(transferTimeout, loop=loop) # wait for a response
            lastDataReceivedDelta = datetime.now() - dataReceived
            print("Data last recieved: " + str(dataReceived) + " Delta:" + str(lastDataReceivedDelta.seconds))
        
        now = datetime.now()
        global fileName
        fileName = "ftclog-" + now.strftime("%Y-%m-%d-%H-%M-%S")#-%Y-%m-%d-%H-%M-%S"
        f = open(fileName + ".csv", 'w')
        f.write(line)
        #print(line)

async def deleteFile_coroutine(address, loop):
    async with BleakClient(address, loop) as client:
        print("Deleting file")
        await client.start_notify(UUID_NORDIC_RX, uart_data_received)
        c=deleteFileCommand
        while len(c)>0:
            await client.write_gatt_char(UUID_NORDIC_TX, bytearray(c[0:20]), True)
            c = c[20:]

        global dataReceived

        await asyncio.sleep(5.0, loop=loop) # wait for a response
        lastDataReceivedDelta = datetime.now() - dataReceived
        print("Data last recieved: " + str(dataReceived) + " Delta:" + str(lastDataReceivedDelta.seconds))
        while (lastDataReceivedDelta.seconds < 5):
            await asyncio.sleep(10.0, loop=loop) # wait for a response
            lastDataReceivedDelta = datetime.now() - dataReceived
            print("Data last recieved: " + str(dataReceived) + " Delta:" + str(lastDataReceivedDelta.seconds))

async def disconnect_bangle(address, loop):
    async with BleakClient(address, loop) as client:
        print("\r\n\r\nDisconnecting from Bangle !")
        await client.disconnect()
        print("\r\n\r\nDone!")
       
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(discover_coroutine())
    if(foundBangle):
        dataReceived = datetime.now()
        loop.run_until_complete(getFile_coroutine(address, loop))
        dataReceived = datetime.now()
        #loop.run_until_complete(deleteFile_coroutine(address, loop))
        loop.run_until_complete(disconnect_bangle(address, loop))

finally:
    print("Bye!")
