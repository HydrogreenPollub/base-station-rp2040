import flatbuffers
import TSData

import capnp
import ts_data_capnp

import time
import paho.mqtt.client as mqtt

import serial

from tempfile import SpooledTemporaryFile
capnp.remove_import_hook()

import os
from dotenv import load_dotenv

load_dotenv()

new_client = []

ser = serial.Serial(
    port = os.getenv("SERIAL_PORT"),
    baudrate = int(os.getenv("SERIAL_BAUDRATE")),
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 5
)

has_found_start = False

def on_tick():
    global has_found_start

    ### Generate buffer
    #buffer = bytearray(128)
    #builder = flatbuffers.Builder(128)
    #TSData.Start(builder)

    #TSData.TSDataAddFcVoltage(builder, 2137)

    #data = TSData.End(builder)
    #builder.Finish(data)
    #buf = builder.Output()
    #buffer[:len(buf)] = buf
    #TSData.TSData.GetRootAs(buffer, 0)

    byte = ser.read(1)
    if not has_found_start:
        if byte == b'\xff':
            print("B: ", byte)
            has_found_start = True
        else:
            return

    buffer = ser.read(128)

    print(" ")
    print("=== Message sent (%d bytes) ===" % len(buffer))
    print(buffer.hex(sep=' '))

    f = SpooledTemporaryFile(256, 'wb+')
    f.write(buffer)
    f.seek(0)
    data = ts_data_capnp.TSData.read(f)
    data = data.to_dict()
    print(data)

    new_client.publish(os.getenv("MQTT_TOPIC"), buffer)

    has_found_start = False


if __name__ == '__main__':
    # Create an MQTT client
    new_client = mqtt.Client()

    # Set the username and password for authentication
    new_client.username_pw_set(username=os.getenv("BROKER_USERNAME"), password=os.getenv("BROKER_PASSWORD"))
    
    # Connect to the broker
    new_client.connect(os.getenv("BROKER_ADDRESS"), port=os.getenv("BROKER_PORT"))
    
    # Start the loop to receive messages
    #new_client.loop_forever()

    while (True):
        on_tick()

    ser.close()
