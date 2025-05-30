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

    required_bytes = 128

    if len(buffer) != required_bytes:
        print(f"Required value not reached: frame save aborted (bytes: {len(buffer)}/{required_bytes})")
        return

    # Check message parsing via Flatbuffers
    try:
        ts_data_flatbuffers = TSData.TSData.GetRootAs(buffer)
        print(f"[Data check - FlatBuffers] Latitude: {ts_data_flatbuffers.GpsLatitude()}, Longitude: {ts_data_flatbuffers.GpsLongitude()}")
    except Exception as err:
        print("Flatbuffers conversion did not succeed: ", err)

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

    # TODO use dynamic column names retrieval in future (values, column_names_str variables)
    snake_case_data = {to_snake_case(key): value for key, value in ts_data.items()}
    snake_case_data["time"] = time.time() # received time

    column_names_str = ", ".join(snake_case_data) # TODO use
    placeholders_str = ", ".join(["%s"] * len(snake_case_data)) # Todo use

    column_names = [
        "time", "vehicle_type", "fc_voltage", "fc_current", "fc_temperature", "sc_motor_voltage", "sc_current",
        "motor_current", "motor_speed", "motor_pwm", "vehicle_speed", "h2_pressure", "h2_leak_level", "fan_rpm",
        "gps_latitude", "gps_longitude", "gps_altitude", "gps_speed", "lap_number"
    ] # TODO remove
    column_names_str = ', '.join(column_names) # TODO remove
    placeholders_str = ", ".join(["%s"] * len(column_names)) # TODO remove

    #values = [snake_case_data[key] for key in column_names_str] # TODO use

    values = tuple([
        time.time(), '0', ts_data["fcVoltage"], ts_data["fcCurrent"], ts_data["fuelCellTemperature"], ts_data["scVoltage"],
        ts_data["fcScCurrent"], ts_data["motorCurrent"], ts_data["motorSpeed"], ts_data["motorPwm"], ts_data["vehicleSpeed"],
        ts_data["hydrogenPressure"], '2', ts_data["fanRpm"], ts_data["gpsLatitude"], ts_data["gpsLongitude"],
        ts_data["gpsAltitude"], ts_data["gpsSpeed"], ts_data["lapNumber"]
    ]) # TODO remove

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
