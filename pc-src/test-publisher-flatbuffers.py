import os
import time
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

import flatbuffers
from proto import TSData

load_dotenv()

def on_tick():
    builder = flatbuffers.Builder(1024)
    TSData.Start(builder)
    TSData.TSDataAddFcVoltage(builder, 2137)
    data = TSData.End(builder)
    builder.Finish(data)

    buffer = builder.Output()

    TSData.TSData.GetRootAs(buffer, 0)
    buffer += bytearray(128 - len(buffer)) # Fill missing zeros

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

    new_client.publish(os.getenv("MQTT_TOPIC"), buffer)

    print(" ")
    print("=== Message sent (%d bytes) ===" % len(buffer))
    print(buffer.hex(sep=' '))

if __name__ == '__main__':
    # Create an MQTT client
    new_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    # Set the username and password for authentication
    new_client.username_pw_set(username=os.getenv("BROKER_USERNAME"), password=os.getenv("BROKER_PASSWORD"))

    # Connect to the broker
    new_client.connect(os.getenv("BROKER_ADDRESS"), port=int(os.getenv("BROKER_PORT")))

    while True:
        on_tick()
        time.sleep(2.5)