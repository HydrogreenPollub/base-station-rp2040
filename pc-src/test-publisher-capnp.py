import os
import time
import math
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

import capnp
from tempfile import SpooledTemporaryFile

load_dotenv()
capnp.remove_import_hook()
ts_data_capnp = capnp.load('proto/ts_data.capnp')

print("MQTT_TOPIC", os.getenv("MQTT_TOPIC"))
script_start_time = time.time()
elapsed_time_since_start = 0

new_client = []
FRAME_LENGTH = 160

def sin(offset, amplitude, t, period):
    return offset + amplitude * math.sin((2 * math.pi) / period * t)

def generate_data(frame):
    frame.time = (time.time_ns())
    frame.timeBeforeTransmit = (time.time_ns() - 2137)

    frame.accessoryBatteryVoltage = (sin(21.37, 3, elapsed_time_since_start, 20))
    frame.accessoryBatteryCurrent = (sin(2.137, 0.5, elapsed_time_since_start, 20))

    frame.fuelCellOutputVoltage = (sin(21.37, 4, elapsed_time_since_start, 20))
    frame.fuelCellOutputCurrent = (sin(2.137, 1, elapsed_time_since_start, 20))

    frame.supercapacitorVoltage = (sin(2*21.37, 4, elapsed_time_since_start, 20))
    frame.supercapacitorCurrent = (sin(2*2.137, 1, elapsed_time_since_start, 20))

    frame.motorControllerSupplyVoltage = (sin(2*20.37, 3, elapsed_time_since_start, 20))
    frame.motorControllerSupplyCurrent = (sin(2*2.037, 3, elapsed_time_since_start, 20))

    frame.fuelCellEnergyAccumulated = (sin(21370, 3, elapsed_time_since_start, 20))

    frame.h2PressureLow = (sin(0.537, 0.2, elapsed_time_since_start, 20))
    frame.h2PressureFuelCell = (sin(0.5, 0.2, elapsed_time_since_start, 20))
    frame.h2PressureHigh = (sin(200, 3, elapsed_time_since_start, 20))
    frame.h2LeakageSensorVoltage = (sin(3.3, 0.1, elapsed_time_since_start, 20))

    frame.fanDutyCycle = (sin(50, 10, elapsed_time_since_start, 20))
    frame.blowerDutyCycle = (sin(55, 3, elapsed_time_since_start, 20))

    frame.temperatureFuelCellLocation1 = (sin(40, 3, elapsed_time_since_start, 20))
    frame.temperatureFuelCellLocation2 = (sin(60, 3, elapsed_time_since_start, 20))

    frame.accelPedalVoltage = (sin(3.3, 0.1, elapsed_time_since_start, 20))
    frame.brakePedalVoltage = (sin(3.2, 0.2, elapsed_time_since_start, 20))
    frame.accelOutputVoltage = (sin(3.3, 0.3, elapsed_time_since_start, 20))
    frame.brakeOutputVoltage = (sin(3.1, 0.01, elapsed_time_since_start, 20))

    frame.buttonsMasterMask = 2
    frame.buttonsSteeringWheelMask = 5

    frame.sensorRpm = (sin(2137, 3, elapsed_time_since_start, 20))
    frame.sensorSpeed = (sin(21.37, 3, elapsed_time_since_start, 20))

    frame.lapNumber = 2
    frame.lapTime = 10000000000

    frame.gpsAltitude = (sin(51, 3, elapsed_time_since_start, 20))
    frame.gpsLatitude = (sin(51.250559, 0.005, elapsed_time_since_start, 20))
    frame.gpsLongitude = (sin(22.570102, 0.005, elapsed_time_since_start, 20))
    frame.gpsSpeed = (sin(21.37, 3, elapsed_time_since_start, 20))

    frame.masterState = 'running'
    frame.protiumState = 'running'

    frame.mainValveEnableOutput = True
    frame.motorControllerEnableOutput = True

def on_tick():
    global elapsed_time_since_start
    elapsed_time_since_start = time.time() - script_start_time

    f = SpooledTemporaryFile(1024, 'wb+')
    ts_data = ts_data_capnp.TSData.new_message()
    generate_data(ts_data)
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