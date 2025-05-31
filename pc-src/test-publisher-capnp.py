import os
import time
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

import capnp
from tempfile import SpooledTemporaryFile

load_dotenv()
capnp.remove_import_hook()
ts_data_capnp = capnp.load('proto/ts_data.capnp')

print("MQTT_TOPIC", os.getenv("MQTT_TOPIC"))

new_client = []

FRAME_LENGTH = 144

def on_tick():
    f = SpooledTemporaryFile(1024, 'wb+')
    ts_data = ts_data_capnp.TSData.new_message()
    ts_data.fuelCellOutputVoltage = 2137
    ts_data.gpsLatitude = 52.111
    ts_data.write(f)
    f.seek(0)

    buffer = bytearray(f.read(512))
    buffer += bytearray(FRAME_LENGTH - len(buffer)) # Fill missing zeros

    new_client.publish(os.getenv("MQTT_TOPIC"), buffer)

    print(" ")
    print(f"=== Message sent (frame len: {FRAME_LENGTH}, buffer len: {len(buffer)}) ===")
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