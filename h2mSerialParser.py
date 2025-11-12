from h2mHelper import h2m_data, FieldType
import logging

logging.basicConfig(
    format='[%(asctime)s] %(levelname)-2s %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S')

class h2m_serial_parser():
    def __init__(self, loglevel) -> None:
        logging.getLogger().setLevel(loglevel)
        return

    def __get_status_as_text(self, status):
        match status:
            case 0:
                return "Aus"
            case 6:
                return "BSK öffnet"
            case 7:
                return "Zündung"
            case 9:
                return "Zündung"
            case 10:
                return "Zündung"
            case 14:
                return "Leistungsbrand"
            case 15:
                return "Gluterhaltung"
            case 17:
                return "Entaschung in 10 min"
            case 18:
                return "Entaschen"
            case _:
                return str(status)

    def parse(self, value):
        logging.debug(f"Parsing: {value}")
        parsed_values = []
        try:
            value = value.strip()
            if not value.startswith("pm"):
                logging.debug(f"not starting with pm")
                return parsed_values, False

            values = value.split(" ")
            if len(values) != 41:
                logging.debug(f"data has wrong length: {len(values)}")
                return parsed_values, False

            parsed_values.append(h2m_data("primaerluftgeblaese", values[1], "Primärluftgebläse", field_type=FieldType.FLOAT, unit="%", icon="mdi:fan-speed-1", state_clazz="measurement"))
            parsed_values.append(h2m_data("saugzuggeblaese", values[2], "Saugzuggebläse", field_type=FieldType.FLOAT, unit="%", icon="mdi:fan", state_clazz="measurement"))
            parsed_values.append(h2m_data("o2_im_rauchgas", values[3], "O2 im Rauchgas", field_type=FieldType.FLOAT, unit="%", icon="mdi:smoke", state_clazz="measurement"))
            parsed_values.append(h2m_data("temperatur_kessel", values[4], "Temperatur Kessel", field_type=FieldType.FLOAT, unit="°C", device_clazz="temperature", state_clazz="measurement"))
            parsed_values.append(h2m_data("temperatur_rauchgas", values[5], "Temperatur Rauchgas", field_type=FieldType.FLOAT, unit="°C", device_clazz="temperature", state_clazz="measurement"))
            parsed_values.append(h2m_data("temperatur_aussen", values[6], "Temperatur Aussen", field_type=FieldType.FLOAT, unit="°C", device_clazz="temperature", state_clazz="measurement"))
            parsed_values.append(h2m_data("temperatur_aussen_mittel", values[7], "Temperatur Aussen Mittel", field_type=FieldType.FLOAT, unit="°C", device_clazz="temperature", state_clazz="measurement"))
            parsed_values.append(h2m_data("temperatur_heizkreis_1", values[8], "Temperatur Heizkreis 1", field_type=FieldType.FLOAT, unit="°C", device_clazz="temperature", state_clazz="measurement"))
            parsed_values.append(h2m_data("temperatur_heizkreis_2", values[9], "Temperatur Heizkreis 2", field_type=FieldType.FLOAT, unit="°C", device_clazz="temperature", state_clazz="measurement"))
            parsed_values.append(h2m_data("temperatur_heizkreis_1_soll", values[10], "Temperatur Heizkreis 1 Soll", field_type=FieldType.FLOAT, unit="°C", device_clazz="temperature", state_clazz="measurement"))
            parsed_values.append(h2m_data("temperatur_heizkreis_2_soll", values[11], "Temperatur Heizkreis 2 Soll", field_type=FieldType.FLOAT, unit="°C", device_clazz="temperature", state_clazz="measurement"))
            parsed_values.append(h2m_data("temperatur_ruecklauf", values[12], "Temperatur Rücklauf", field_type=FieldType.FLOAT, unit="°C", device_clazz="temperature", state_clazz="measurement"))
            parsed_values.append(h2m_data("temperatur_boiler", values[13], "Temperatur Boiler", field_type=FieldType.FLOAT, unit="°C", device_clazz="temperature", state_clazz="measurement"))
            parsed_values.append(h2m_data("foerdermenge", values[14], "Fördermenge", field_type=FieldType.FLOAT, unit="%", icon="mdi:pine-tree-fire", state_clazz="measurement"))
            parsed_values.append(h2m_data("temperatur_kessel_soll", values[15], "Temperatur Kessel Soll", field_type=FieldType.FLOAT, unit="°C", device_clazz="temperature", state_clazz="measurement"))
            parsed_values.append(h2m_data("status", values[29], "Status", field_type=FieldType.INT, category="diagnostic"))
            parsed_values.append(h2m_data("statusnachricht", self.__get_status_as_text(int(values[29])), "Statusnachricht"))
            parsed_values.append(h2m_data("einschubschnecke_strom", values[30], "Einschubschnecke Strom", field_type=FieldType.FLOAT, unit="A", device_clazz="current", state_clazz="measurement", enabled=False))
            parsed_values.append(h2m_data("raumaustragung_strom", values[31], "Raumaustragung Strom", field_type=FieldType.FLOAT, unit="A", device_clazz="current", state_clazz="measurement", enabled=False))
            parsed_values.append(h2m_data("ascheaustragung_strom", values[32], "Ascheaustragung Strom", field_type=FieldType.FLOAT, unit="A", device_clazz="current", state_clazz="measurement", enabled=False))
            register1 = int(values[33], 16)
            parsed_values.append(h2m_data("einschubschnecke_vorwaerts", str(register1 & 1 != 0), "Einschubschnecke Vorwärts", field_type=FieldType.BOOL, device_clazz="running", enabled=False))
            parsed_values.append(h2m_data("einschubschnecke_rueckwaerts", str(register1 & 2 != 0), "Einschubschnecke Rückwärts", field_type=FieldType.BOOL, device_clazz="running", enabled=False))
            parsed_values.append(h2m_data("raumaustragung_vorwaerts", str(register1 & 4 != 0), "Raumaustragung Vorwärts", field_type=FieldType.BOOL, device_clazz="running", enabled=False))
            parsed_values.append(h2m_data("raumaustragung_rueckwaerts", str(register1 & 8 != 0), "Raumaustragung Rückwärts", field_type=FieldType.BOOL, device_clazz="running", enabled=False))
            parsed_values.append(h2m_data("ascheaustragung_vorwaerts", str(register1 & 16 != 0), "Ascheaustragung Vorwärts", field_type=FieldType.BOOL, device_clazz="running", enabled=False))
            parsed_values.append(h2m_data("ascheaustragung_rueckwaerts", str(register1 & 32 != 0), "Ascheaustragung Rückwärts", field_type=FieldType.BOOL, device_clazz="running", enabled=False))
            register2 = int(values[34], 16)
            parsed_values.append(h2m_data("branschutzklappe_motor", str(register2 & 1 != 0), "Brandschutzklappe Motor", field_type=FieldType.BOOL, device_clazz="running", enabled=False))
            parsed_values.append(h2m_data("zuendung_geblaese", str(register2 & 2 != 0), "Zündung Gebläse", field_type=FieldType.BOOL, device_clazz="running"))
            parsed_values.append(h2m_data("zuendung_heizung", str(register2 & 4 != 0), "Zündung Heizung", field_type=FieldType.BOOL, device_clazz="running"))
            parsed_values.append(h2m_data("pumpe_fernleitung", str(register2 & 8 != 0), "Pumpe Fernleitung", field_type=FieldType.BOOL, device_clazz="running"))
            parsed_values.append(h2m_data("pumpe_boiler", str(register2 & 16 != 0), "Pumpe Boiler", field_type=FieldType.BOOL, device_clazz="running"))
            parsed_values.append(h2m_data("pumpe_heizkreis_1", str(register2 & 32 != 0), "Pumpe Heizkreis 1", field_type=FieldType.BOOL, device_clazz="running"))
            parsed_values.append(h2m_data("mischer_heizkreis_1_auf", str(register2 & 64 != 0), "Mischer Heizkreis 1 Auf", field_type=FieldType.BOOL, device_clazz="running", enabled=False))
            parsed_values.append(h2m_data("mischer_heizkreis_1_zu", str(register2 & 128 != 0), "Mischer Heizkreis 1 Zu", field_type=FieldType.BOOL, device_clazz="running", enabled=False))
            parsed_values.append(h2m_data("pumpe_heizkreis_2", str(register2 & 256 != 0), "Pumpe Heizkreis 2", field_type=FieldType.BOOL, device_clazz="running"))
            parsed_values.append(h2m_data("mischer_heizkreis_2_auf", str(register2 & 512 != 0), "Mischer Heizkreis 2 Auf", field_type=FieldType.BOOL, device_clazz="running", enabled=False))
            parsed_values.append(h2m_data("mischer_heizkreis_2_zu", str(register2 & 1024 != 0), "Mischer Heizkreis 2 Zu", field_type=FieldType.BOOL, device_clazz="running", enabled=False))
            parsed_values.append(h2m_data("stoerung", str(register2 & 2048 != 0), "Störung", field_type=FieldType.BOOL, device_clazz="problem"))
            register3 = int(values[35], 16)
            parsed_values.append(h2m_data("pumpe_ruecklauf", str(register3 & 8 != 0), "Pumpe Rücklauf", field_type=FieldType.BOOL, device_clazz="running"))
            register4 = int(values[36], 16)
            parsed_values.append(h2m_data("rost", str(register4 & 128 == 0), "Rost", field_type=FieldType.BOOL, device_clazz="opening", enabled=False))
            parsed_values.append(h2m_data("brandschutzklappe", str(register4 & 256 != 0), "Brandschutzklappe", field_type=FieldType.BOOL, device_clazz="opening"))
            parsed_values.append(h2m_data("anforderung_externer_heizkreis", str(register4 & 512 != 0), "Anforderung Ext. HK", field_type=FieldType.BOOL, device_clazz="running"))

            return parsed_values, True
        except Exception as e:
            logging.debug(f"Parse failed: {e}")
            return parsed_values, False
