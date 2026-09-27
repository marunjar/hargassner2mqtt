from h2mHelper import h2m_data, FieldType
import logging

logging.basicConfig(
    format='[%(asctime)s] %(levelname)-2s %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S')

class h2m_voltage_parser():

    def __init__(self, loglevel) -> None:
        logging.getLogger().setLevel(loglevel)
        self.last_value = None
        self.time_constant = 3
        return

    def __volt_2_bar(self, voltage):
        bar = round((voltage - 0.5) * 5 / 4, 2)
        if bar < 0:
            bar = 0

        if (self.last_value is None):
            filtered_value = bar
        else:
            # basic lowpass
            A = 1 / self.time_constant
            B = 1 - A
            filtered_value = round(A * self.last_value + B * bar, 2)

        logging.debug(f"{bar} bar, filtered value: {filtered_value}")
        self.last_value = filtered_value

        return filtered_value

    def __volt_2_stat(self, voltage):
        if voltage < 0.25:
            s="Short to ground or not connected"
        elif voltage > 4.75:
            s="Short to VCC"
        else :
            s="Ok"
        return s

    def parse(self, voltage):
        logging.debug(f"Parsing: {voltage}")
        parsed_values = []
        try:
            if not isinstance(voltage, float):
                logging.debug(f"no float")
                return parsed_values, False
            voltage = round(voltage, 5)

            parsed_values.append(h2m_data("heizungsdruck", self.__volt_2_bar(voltage), "Heizungsdruck", field_type=FieldType.FLOAT, device_clazz="pressure", unit="bar", icon="mdi:water-boiler", state_clazz="measurement"))
            parsed_values.append(h2m_data("heizungsdruck_stoerung", str(self.__volt_2_stat(voltage) != "Ok"), "Heizungsdruck Störung", field_type=FieldType.BOOL, device_clazz="problem"))
            parsed_values.append(h2m_data("heizungsdruck_statusnachricht", self.__volt_2_stat(voltage), "Heizungsdruck Status", category="diagnostic", enabled=False))

            return parsed_values, True
        except Exception as e:
            logging.debug(f"Parse failed: {e}")
            return parsed_values, False
