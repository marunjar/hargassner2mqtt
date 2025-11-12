from enum import Enum
import json
import logging
import re

VERSION = "0.1"
HA_PREFIX = "homeassistant"
STATE_PREFIX = "hargassner"

logging.basicConfig(
    format='[%(asctime)s] %(levelname)-2s %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S')

class h2m_helper():
    def __init__(self, transmit_callback, loglevel) -> None:
        logging.getLogger().setLevel(loglevel)
        self.systems = {}
        self.transmit_callback = transmit_callback

    def sanitize(self, value):
        return re.sub("[^a-zA-Z0-9_-]", "_", value).lower()

    def __get_measurements_list(self, json_data):
        return json_data.keys()

    def announce_new(self, system_name, sensor_name, parsed_values):
        # Add current host if unknown
        current_system, is_new_h = self.add_system(system_name)
        # Add unknown sensors to host
        current_sensor, is_new_s = current_system.add_sensor(sensor_name)
        # Add unknown measurements to each sensor
        for parsed_value in parsed_values:
            _, is_new_m = current_sensor.add_measurement(parsed_value)

        if is_new_s and current_sensor.enabled:
            logging.info(f"Added sensor: {current_sensor.topic}")

        return (is_new_s | is_new_h | is_new_m), current_sensor

    def send(self, system_name, sensor_name, parsed_values):
        is_new, current_sensor = self.announce_new(system_name, sensor_name, parsed_values)

        if current_sensor.enabled:
            json_data = {}
            for parsed_value in parsed_values:
                json_data[f"{parsed_value.field}"] = f"{parsed_value.value}"

            # current_sensor.announce()
            self.transmit_callback(f"{current_sensor.topic}", json.dumps(json_data), qos=0, retain=False)

    def add_system(self, system_name):
        system_id = self.sanitize(system_name)
        current_system = self.systems.get(system_id)
        if current_system is None:
            current_system = hargassner(self, system_id, system_name)
            self.systems[system_id] = current_system
            return current_system, True

        return current_system, False

class FieldType(Enum):
    STR = 1
    FLOAT = 2
    INT = 3
    BOOL = 4

class h2m_data():
    def __init__(self, field, value, visible_name, field_type=FieldType.STR, device_clazz=None, state_clazz=None, unit=None, icon=None, enabled=True, category=None) -> None:
        self.field = field
        self.value = value
        self.visible_name = visible_name
        self.field_type = field_type
        self.device_clazz = device_clazz
        self.state_clazz = state_clazz
        self.unit = unit
        self.icon = icon
        self.enabled = enabled
        self.category = category

class hargassner():
    def __init__(self, parent_parser, system_id, name) -> None:
        self.system_id = system_id
        self.name = name
        self.sensors = {}
        self.parent_parser = parent_parser

        self.info = {}
        self.info["identifiers"] = [f"hargassner_bridge_{self.system_id}"]
        self.info["model"] = "Hargassner Bridge"
        self.info["name"] = f"Hargassner {self.name}"
        self.info["sw_version"] = VERSION
        self.info["manufacturer"] = "Hargassner"
        self.enabled = False
        logging.debug(f"Created heating system: system_id={self.system_id}, name={self.name}")

    def add_sensor(self, sensor_name):
        sensor_id = self.parent_parser.sanitize(sensor_name)
        # To create the sensor name, also check for extra tags (for the case of disks for example)
        current_sensor = self.sensors.get(sensor_id)
        if current_sensor is None:
            current_sensor = sensor(self, sensor_id, sensor_name)
            self.sensors[sensor_id] = current_sensor
            return current_sensor, True

        return current_sensor, False

class sensor():
    def __init__(self, parent_system, sensor_id, name) -> None:
        self.sensor_id = sensor_id
        self.name = name
        self.measurements = {}
        self.parent_system = parent_system
        self.enabled = False
        self.topic = f"{STATE_PREFIX}/{self.parent_system.system_id}/{self.sensor_id}/data"
        logging.debug(f"Created sensor: sensor_id={self.sensor_id}, name={self.name}, topic={self.topic}")

    def add_measurement(self, parsed_value):
        measurement_id = self.parent_system.parent_parser.sanitize(parsed_value.field)
        current_measurement = self.measurements.get(measurement_id)
        if current_measurement is None:
            current_measurement = measurement(self, parsed_value)
            self.measurements[measurement_id] = current_measurement
            return current_measurement, current_measurement.enabled

        return current_measurement, False

    def announce(self):
        for measurement_name, current_measurement in self.measurements:
            current_measurement.announce()

class measurement():
    def __init__(self, parent_sensor, parsed_value) -> None:
        self.parsed_value = parsed_value
        self.component = self.__get_component()
        self.parent_sensor = parent_sensor
        self.topic = f"{HA_PREFIX}/{self.component}/{self.parent_sensor.parent_system.system_id}/{self.parent_sensor.sensor_id}_{self.parsed_value.field}"
        self.uid = f"{STATE_PREFIX}.{self.parent_sensor.parent_system.system_id}_{self.parent_sensor.sensor_id}_{self.parsed_value.field}"
        self.enabled = True
        parent_sensor.enabled = True
        parent_sensor.parent_system.enabled = True
        logging.debug(f"Created measurement: measurement_id={self.parsed_value.field}, name={self.parsed_value.visible_name}, topic={self.topic}")

        self.announce()

    def __get_component(self):
        if (self.parsed_value.field_type == FieldType.BOOL):
            return "binary_sensor"
        else:
            return "sensor"

    def announce(self):
        if (self.enabled):
            config_payload = {
                # "~": self.topic,
                "name": f"{self.parsed_value.visible_name}",
                "state_topic": f"{self.parent_sensor.topic}",
                "device_class": self.parsed_value.device_clazz,
                "state_class": self.parsed_value.state_clazz,
                "unit_of_measurement": self.parsed_value.unit,
                "device": self.parent_sensor.parent_system.info,
                "origin": {
                    "name": "hargassner2mqtt",
                    "sw": VERSION
                },
                "unique_id": self.uid,
                "default_entity_id": f"{self.component}.{self.uid}",
                "enabled_by_default": f"{str(self.parsed_value.enabled)}",
                "platform": self.component,
                "qos": 2,
                "value_template": self.get_value_template(),
            }
            if (self.parsed_value.icon != None):
                config_payload["icon"] = self.parsed_value.icon
            if (self.parsed_value.category != None):
                config_payload["entity_category"] = self.parsed_value.category
            if (self.parsed_value.field_type == FieldType.BOOL):
                config_payload["payload_off"] = str(False)
                config_payload["payload_on"] = str(True)

            # If it is a new measumente, announce it to hassio
            logging.debug(f"Announce measurement: {self.parsed_value.field}, {self.topic}")
            self.parent_sensor.parent_system.parent_parser.transmit_callback(f"{self.topic}/config", json.dumps(config_payload), retain=True)

    def get_value_template(self):
        match self.parsed_value.field_type:
            case FieldType.BOOL:
                return f"{{{{ value_json.{self.parsed_value.field} }}}}"
            case FieldType.FLOAT:
                return f"{{{{ value_json.{self.parsed_value.field} | float(0) }}}}"
            case FieldType.INT:
                return f"{{{{ value_json.{self.parsed_value.field} | int(0) }}}}"
            case _:
                return f"{{{{ value_json.{self.parsed_value.field} }}}}"
