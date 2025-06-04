import os
import re
import time
import datetime
import paho.mqtt.client as mqtt
from paho.mqtt.subscribeoptions import SubscribeOptions

import flatbuffers
from proto import TSData

import capnp
from tempfile import SpooledTemporaryFile

import psycopg2

# Uncomment for local tests
from dotenv import load_dotenv
load_dotenv()

capnp.remove_import_hook()
ts_data_capnp = capnp.load('proto/ts_data.capnp')

# Define the MQTT broker parameters
broker_address = os.getenv("BROKER_ADDRESS")
broker_port = os.getenv("BROKER_PORT")
username = os.getenv("BROKER_USERNAME")
password = os.getenv("BROKER_PASSWORD")
topic = "sensors"

FRAME_SIZE = 160

def to_snake_case(name):
    """Converts a CamelCase string to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def get_curr_timestamp() -> str:
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # [:-3] to get milliseconds instead of microseconds

def on_message(client, userdata, msg):
    buffer = bytearray(msg.payload)

    print(" ")
    print(f"=== Message received - {len(buffer)} bytes - {get_curr_timestamp()} (UTC) ===")
    print(buffer.hex(sep=' '))

    if len(buffer) != FRAME_SIZE:
        print(f"Required value not reached: frame save aborted (bytes: {len(buffer)}/{FRAME_SIZE})")
        return

    # Check message parsing via Capnp
    try:
        f = SpooledTemporaryFile(1024, 'wb+')
        f.write(buffer)
        f.seek(0)
        data = ts_data_capnp.TSData.read(f)
        ts_data = data.to_dict()
        print(f"data to dict: {ts_data}")
        print(f"[Data check - Capnp] Latitude: {ts_data["gpsLatitude"]}, Longitude: {ts_data["gpsLongitude"]}")
    except Exception as err:
        print("Capnp conversion did not succeed: ", err)
        return

    # TODO Add custom columns to dictionary or remove unwanted here
    ts_data["time"] = time.time_ns() # received time

    column_names_str = '"' +  '", "'.join(ts_data) + '"'
    placeholders_str = ", ".join(["%s"] * len(ts_data))
    values = tuple(ts_data.values())

    query = (
        f"INSERT INTO measurements ({column_names_str}) "
        f"VALUES ({placeholders_str}) "
        "ON CONFLICT DO NOTHING"
    )

    print(f"Query: {query}")
    print(f"Values: {values}")

    cursor.execute(query, values)
    conn.commit()

if __name__ == '__main__':
    global cursor
    try:
        print(f"=== PROGRAM START - {get_curr_timestamp()} (UTC) ===")
        print(f'BROKER_ADDRESS: {os.getenv("BROKER_ADDRESS")}')
        print(f'BROKER_PORT: {os.getenv("BROKER_PORT")}')
        print(f'MQTT_TOPIC: {os.getenv("MQTT_TOPIC")}')
        print(f'DB_DATABASE: {os.getenv("DB_DATABASE")}')
        print(f'DB_HOST: {os.getenv("DB_HOST")}')
        print(f'DB_PORT: {os.getenv("DB_PORT")}')

        obj = time.gmtime(0)
        epoch = time.asctime(obj)
        print("Time epoch (time start):", epoch)

        conn = psycopg2.connect(
            dbname=os.getenv("DB_DATABASE"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        print("Database connection was successful")

        cursor = conn.cursor()

        # Create an MQTT client
        new_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        # Set the username and password for authentication
        new_client.username_pw_set(username=username, password=password)

        # Connect to the broker
        #new_client.tls_set()
        new_client.connect(host=broker_address, port=int(broker_port))
        print("MQTT connection was successful")

        # Subscribe to the topic
        new_client.subscribe(os.getenv("MQTT_TOPIC"), options=SubscribeOptions(qos=2))

        # Define the callback function to handle incoming messages
        new_client.on_message = on_message

        # Start the loop to receive messages
        new_client.loop_forever()


    except Exception as e:
        print("Error:", e)

    finally:
        cursor.close()
        conn.close()
        new_client.disconnect()
