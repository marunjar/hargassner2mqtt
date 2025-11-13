#!/usr/bin/env python3
"""mqtt_serial_bridge.py
Command-line utility to connect a serial-port device with a remote MQTT server.
Please note: the Configuration settings must be customized before us.
"""

################################################################
# Configuration

# The following variables must be customized to set up the network and serial
# port settings.

# IDeATe MQTT server name.
mqtt_hostname = "homeassistant.home.arpa"

# IDeATe MQTT server port, specific to each course.
# Please see https://mqtt.ideate.cmu.edu for details.
mqtt_portnum  = 1883   # 16-376

# Username and password, provided by instructor for each course.
mqtt_username = '<mqtt_username>'
mqtt_password = '<mqtt_password>'

# MQTT publication topic.
mqtt_topic = 'hargassner/hsv30/hsv30/sensor'

# MQTT receive subscription.
mqtt_subscription = 'none'

# Serial port device to bridge to the network (e.g. Arduino).
# On Windows, this will usually be similar to 'COM5'.
# On macOS, this will usually be similar to '/dev/cu.usbmodem333101'
serial_portname = '/dev/ttyS0'

################################################################
# Import standard Python libraries.
import sys, time, signal, datetime, json, logging

# Import the MQTT client library.
# documentation: https://www.eclipse.org/paho/clients/python/docs/
import paho.mqtt.client as mqtt

# Import the pySerial library.
# documentation: https://pyserial.readthedocs.io/en/latest/
import serial

# import arduino stuff
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

# import hargassner2mqtt stuff
from h2mHelper import h2m_helper, h2m_data, FieldType
from h2mSerialParser import h2m_serial_parser
from h2mVoltageParser import h2m_voltage_parser

################################################################
# Global script variables.

serial_port = None
client = None
h2m = None
h2msp = None
h2mvp = None
tick = 0

loglevel = logging.INFO

################################################################
if mqtt_username == '' or mqtt_password == '' or mqtt_topic == '' or serial_portname == '':
    print("""\
This script must be customized before it can be used.  Please edit the file with
a Python or text editor and set the variables appropriately in the Configuration
section at the top of the file.
""")
    if serial_portname == '':
        import serial.tools.list_ports
        print("All available serial ports:")
        for p in serial.tools.list_ports.comports():
            print(" ", p.device)
    sys.exit(0)

################################################################
# Attach a handler to the keyboard interrupt (control-C).
def _sigint_handler(signal, frame):
    logging.info("Keyboard interrupt caught, closing down...")
    if serial_port is not None:
        serial_port.close()

    if client is not None:
        client.loop_stop()

    sys.exit(0)

signal.signal(signal.SIGINT, _sigint_handler)
################################################################
# MQTT networking functions.

def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
    # Be careful, the reason_code_list is only present in MQTTv5.
    # In MQTTv3 it will always be empty
    if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
        logging.debug("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
    else:
        logging.debug(f"Broker replied with failure: {reason_code_list[0]}")
    client.disconnect()
    h2m = h2m_helper(data_transmit, loglevel)

#----------------------------------------------------------------
# The callback for when the broker responds to our connection request.
def on_connect(client, userdata, flags, rc, properties):
    logging.info(f"MQTT connected with flags: {flags}, result code: {rc}, properties: {properties}")

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    # The hash mark is a multi-level wildcard, so this will subscribe to all subtopics of 16223
    client.subscribe(mqtt_subscription)
    return

#----------------------------------------------------------------
# The callback for when a message has been received on a topic to which this
# client is subscribed.  The message variable is a MQTTMessage that describes
# all of the message parameters.

# Some useful MQTTMessage fields: topic, payload, qos, retain, mid, properties.
#   The payload is a binary string (bytes).
#   qos is an integer quality of service indicator (0,1, or 2)
#   mid is an integer message ID.
def on_message(client, userdata, msg):
    logging.debug(f"message received: topic: {msg.topic} payload: {msg.payload}")

    # If the serial port is ready, re-transmit received messages to the
    # device. The msg.payload is a bytes object which can be directly sent to
    # the serial port with an appended line ending.
    #if serial_port is not None and serial_port.is_open:
    #    serial_port.write(msg.payload + b'\n')
    return

def data_transmit(topic, payload, qos=1, retain=False):
    logging.debug(f"Publish to {topic}: {payload}, qos={qos}, retain={retain}")
    client.publish(topic, payload=payload, qos=qos, retain=retain)

class Pin:
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3

#----------------------------------------------------------------
# configure logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)-2s %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S')
logging.getLogger().setLevel(loglevel)

#----------------------------------------------------------------
# Launch the MQTT network client
client = mqtt.Client(client_id="Hargassner HSV-30", protocol=mqtt.MQTTv5)
client.enable_logger()
client.on_connect = on_connect
client.on_unsubscribe = on_unsubscribe
client.on_message = on_message
#client.tls_set()
client.username_pw_set(mqtt_username, mqtt_password)

# Start a background thread to connect to the MQTT network.
client.connect(mqtt_hostname, mqtt_portnum)
client.loop_start()

################################################################
# Connect to the serial device.
serial_port = serial.Serial(serial_portname, baudrate=19200, timeout=2.0)

# wait briefly for the system to complete waking up
time.sleep(2)

################################################################
# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads= ADS1115(i2c)
# Create single-ended input on channel 0
chan0 = AnalogIn(ads, Pin.ZERO)

# wait briefly for the system to complete waking up
time.sleep(2)

logging.info(f"Entering event loop for {serial_portname} and {chan0}.  Enter Control-C to quit.")

h2msp = h2m_serial_parser(loglevel)
h2mvp = h2m_voltage_parser(loglevel)

while(True):
    if (tick == 0):
        h2m = h2m_helper(data_transmit, loglevel)
    tick = (tick + 1) % 10

    try:
        # reset input buffer, hargassner is writing every 0.5s
        serial_port.reset_input_buffer()
        serial_input = serial_port.readline().decode(encoding='ascii',errors='ignore').strip()
        parsed_serial_input, serial_data_valid = h2msp.parse(serial_input)
        voltage = chan0.voltage
        parsed_voltage, voltage_data_valid = h2mvp.parse(voltage)
        if not serial_data_valid or not voltage_data_valid:
            logging.warning(f"serial={serial_input}, serial_data_valid={serial_data_valid}, voltage={voltage}, voltage_data_valid={voltage_data_valid}")
        else:
            if client.is_connected():
                data = [
                    h2m_data("raw_data_serial", serial_input, "Raw Serial Data", enabled=False, category="diagnostic"),
                    h2m_data("raw_data_voltage", voltage, "Raw Voltage Data", enabled=False, category="diagnostic", device_clazz="voltage", unit="V", field_type=FieldType.FLOAT),
                    h2m_data("last_seen", datetime.datetime.now(datetime.UTC).isoformat(), "Last Seen", category="diagnostic", icon="mdi:clock")
                ]
                h2m.send("HSV30", "Lambdatronic", data + parsed_serial_input + parsed_voltage)
                time.sleep(16)
    except Exception as e:
        logging.error(f"{e}")
    time.sleep(3)

serial_port.close()
