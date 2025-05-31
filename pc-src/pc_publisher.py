import os
import serial
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

import capnp
from tempfile import SpooledTemporaryFile

load_dotenv()
capnp.remove_import_hook()
ts_data_capnp = capnp.load('proto/ts_data.capnp')

new_client = []

ser = serial.Serial(
    port = input(f"Select serial port (default: {os.getenv("SERIAL_PORT")}): ") or os.getenv("SERIAL_PORT"),
    baudrate = int(os.getenv("SERIAL_BAUDRATE")),
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 10
)

print("SERIAL_PORT", os.getenv("SERIAL_PORT"))
print("SERIAL_BAUDRATE", os.getenv("SERIAL_BAUDRATE"))
print("MQTT_TOPIC", os.getenv("MQTT_TOPIC"))

FRAME_LENGTH = 144
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

    buffer = ser.read(FRAME_LENGTH)
    new_client.publish(os.getenv("MQTT_TOPIC"), buffer)

    print(" ")
    print("=== Message received and sent (%d bytes) ===" % len(buffer))
    print(buffer.hex(sep=' '))

    # DEBUG: check content
    f = SpooledTemporaryFile(256, 'wb+')
    f.write(buffer)
    f.seek(0)
    data = ts_data_capnp.TSData.read(f)
    data = data.to_dict()
    print(data)

    has_found_start = False


if __name__ == '__main__':
    # Create an MQTT client
    new_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    # Set the username and password for authentication
    new_client.username_pw_set(username=os.getenv("BROKER_USERNAME"), password=os.getenv("BROKER_PASSWORD"))
    
    # Connect to the broker
    new_client.connect(os.getenv("BROKER_ADDRESS"), port=int(os.getenv("BROKER_PORT")))

    while True:
        on_tick()
