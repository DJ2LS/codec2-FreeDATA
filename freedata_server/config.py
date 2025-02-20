import configparser
import structlog
import json


class CONFIG:
    """
    CONFIG class for handling with config files

    """

    config_types = {
        'NETWORK': {
            'modemaddress': str,
            'modemport': int,
        },
        'STATION': {
            'mycall': str,
            'mygrid': str,
            'myssid': int,
            'ssid_list': list,
            'enable_explorer': bool,
            'enable_stats': bool,
            'respond_to_cq': bool,
            'enable_callsign_blacklist': bool,
            'callsign_blacklist': list

        },
        'AUDIO': {
            'input_device': str,
            'output_device': str,
            'rx_audio_level': int,
            'tx_audio_level': int,
        },
        'RADIO': {
            'control': str,
            'serial_port': str,
            'model_id': int,
            'serial_speed': int,
            'data_bits': int,
            'stop_bits': int,
            'serial_handshake': str,
            'ptt_port': str,
            'ptt_type': str,
            'serial_dcd': str,
            'serial_dtr': str,
            'serial_rts': str,
        },
        'RIGCTLD': {
            'ip': str,
            'port': int,
            'path': str,
            'command': str,
            'arguments': str,
            'enable_vfo': bool,
        },
        'TCI': {
            'tci_ip': str,
            'tci_port': int,
        },
        'MODEM': {
            'enable_morse_identifier': bool,
            'maximum_bandwidth': int,
            'tx_delay': int,
        },
        'SOCKET_INTERFACE': {
            'enable': bool,
            'host': str,
            'cmd_port': int,
            'data_port': int,
        },
        'MESSAGES': {
            'enable_auto_repeat': bool,
        },
        'QSO_LOGGING': {
            'enable_adif_udp': bool,
            'adif_udp_host': str,
            'adif_udp_port': int,
            'enable_adif_wavelog': bool,
            'adif_wavelog_host': str,
            'adif_wavelog_api_key': str,
        },

        'GUI': {
            'auto_run_browser': bool,
        }
    }

    default_values = {
        list: '[]',
        bool: 'False',
        int: '0',
        str: '',
    }

    def __init__(self, configfile: str):

        # set up logger
        self.log = structlog.get_logger(type(self).__name__)

        # init configparser
        self.parser = configparser.ConfigParser(inline_comment_prefixes="#", allow_no_value=True)
        
        try:
            self.config_name = configfile
        except Exception:
            self.config_name = "config.ini"

        # self.log.info("[CFG] config init", file=self.config_name)

        # check if config file exists
        self.config_exists()

        # validate config structure
        self.validate_config()

    def config_exists(self):
        """
        check if config file exists
        """
        try:
            return bool(self.parser.read(self.config_name, None))
        except Exception as configerror:
            self.log.error("[CFG] logfile init error", e=configerror)
            return False

    # Validates config data
    def validate_data(self, data):
        for section in data:
            for setting in data[section]:
                if not isinstance(data[section][setting], self.config_types[section][setting]):
                    message = (f"{section}.{setting} must be {self.config_types[section][setting]}."
                               f" '{data[section][setting]}' {type(data[section][setting])} given.")
                    raise ValueError(message)

    def validate_config(self):
        """
        Updates the configuration file to match exactly what is defined in self.config_types.
        It removes sections and settings not defined there and adds missing sections and settings.
        """
        existing_sections = self.parser.sections()

        # Remove sections and settings not defined in self.config_types
        for section in existing_sections:
            if section not in self.config_types:
                self.parser.remove_section(section)
                self.log.info(f"[CFG] Removing undefined section: {section}")
                continue
            existing_settings = self.parser.options(section)
            for setting in existing_settings:
                if setting not in self.config_types[section]:
                    self.parser.remove_option(section, setting)
                    self.log.info(f"[CFG] Removing undefined setting: {section}.{setting}")

        # Add missing sections and settings from self.config_types
        for section, settings in self.config_types.items():
            if section not in existing_sections:
                self.parser.add_section(section)
                self.log.info(f"[CFG] Adding missing section: {section}")
            for setting, value_type in settings.items():
                if not self.parser.has_option(section, setting):
                    default_value = self.default_values.get(value_type, None)

                    self.parser.set(section, setting, str(default_value))
                    self.log.info(f"[CFG] Adding missing setting: {section}.{setting}")

        return self.write_to_file()

    # Handle special setting data type conversion
    # is_writing means data from a dict being writen to the config file
    # if False, it means the opposite direction
    def handle_setting(self, section, setting, value, is_writing=False):
        try:
            if self.config_types[section][setting] == list:
                if is_writing:
                    # When writing, ensure the value is a list and then convert it to JSON
                    if isinstance(value, str):
                        value = json.loads(value)  # Convert JSON string to list
                    return json.dumps(value)  # Convert list to JSON string
                else:
                    # When reading, convert the JSON string back to a list
                    if isinstance(value, str):
                        return json.loads(value)
                    return value  # Return as-is if already a list

            elif self.config_types[section][setting] == bool and not is_writing:
                return self.parser.getboolean(section, setting)

            elif self.config_types[section][setting] == int and not is_writing:
                return self.parser.getint(section, setting)

            else:
                return value
        except KeyError as key:
            self.log.error("[CFG] key error in logfile, please check 'config.ini.example' for help", key=key)

    # Sets and writes config data from a dict containing data settings
    def write(self, data):
        # Validate config data before writing
        print(data)
        self.validate_data(data)
        for section in data:
            # init section if it doesn't exist yet
            if not section.upper() in self.parser.keys():
                self.parser[section] = {}

            for setting in data[section]:
                new_value = self.handle_setting(
                    section, setting, data[section][setting], True)
                try:
                    self.parser[section][setting] = str(new_value)
                except Exception as e:
                    self.log.error("[CFG] error setting config key", e=e)
        return self.write_to_file()

    def write_to_file(self):
        # Write config data to file
        try:
            with open(self.config_name, 'w') as configfile:
                self.parser.write(configfile)
                return self.read()
        except Exception as conferror:
            self.log.error("[CFG] reading logfile", e=conferror)
            return False

    def read(self):
        """
        read config file
        """
        # self.log.info("[CFG] reading...")
        if not self.config_exists():
            return False
        
        # at first just copy the config as read from file
        result = {s: dict(self.parser.items(s)) for s in self.parser.sections()}

        # handle the special settings
        for section in result:
            for setting in result[section]:
                result[section][setting] = self.handle_setting(
                   section, setting, result[section][setting], False)

        return result
