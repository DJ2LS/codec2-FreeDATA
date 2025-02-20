import rigctld
import rigdummy
import serial_ptt
import threading

class RadioManager:
    def __init__(self, config, state_manager, event_manager, socket_interface_manager):
        self.config = config
        self.state_manager = state_manager
        self.event_manager = event_manager
        self.socket_interface_manager = socket_interface_manager

        self.radiocontrol = config['RADIO']['control']
        self.rigctld_ip = config['RIGCTLD']['ip']
        self.rigctld_port = config['RIGCTLD']['port']

        self.refresh_rate = 1
        self.stop_event = threading.Event()
        self.update_thread = threading.Thread(target=self.update_parameters, daemon=True)
        self._init_rig_control()

    def _init_rig_control(self):
        # Check how we want to control the radio
        if self.radiocontrol in ["rigctld", "rigctld_bundle"]:
            self.radio = rigctld.radio(self.config, self.state_manager, hostname=self.rigctld_ip,port=self.rigctld_port)
        elif self.radiocontrol == "serial_ptt":
            self.radio = serial_ptt.radio(self.config, self.state_manager)

        elif self.radiocontrol == "tci":
            raise NotImplementedError
            # self.radio = self.tci_module
        else:
            self.radio = rigdummy.radio()

        self.update_thread.start()

    def set_ptt(self, state):
        self.radio.set_ptt(state)
        # set disabled ptt twice for reducing chance of stuck PTT
        if not state:
            self.radio.set_ptt(state)

        # send ptt state via socket interface
        if self.socket_interface_manager:
            self.socket_interface_manager.command_server.command_handler.socket_respond_ptt(state)


    def set_tuner(self, state):
        self.radio.set_tuner(state)
        self.state_manager.set_radio("radio_tuner", state)

    def set_frequency(self, frequency):
        self.radio.set_frequency(frequency)
        self.state_manager.set_radio("radio_frequency", frequency)

    def set_mode(self, mode):
        self.radio.set_mode(mode)
        self.state_manager.set_radio("radio_mode", mode)

    def set_rf_level(self, level):
        self.radio.set_rf_level(level)
        self.state_manager.set_radio("radio_rf_level", level)

    def update_parameters(self):
        while not self.stop_event.is_set():
            parameters = self.radio.get_parameters()

            self.state_manager.set_radio("radio_frequency", parameters['frequency'])
            self.state_manager.set_radio("radio_mode", parameters['mode'])
            self.state_manager.set_radio("radio_bandwidth", parameters['bandwidth'])
            self.state_manager.set_radio("radio_rf_level", parameters['rf'])
            self.state_manager.set_radio("radio_tuner", parameters['tuner'])

            if self.state_manager.isTransmitting():
                self.radio_alc = parameters['alc']
                self.state_manager.set_radio("radio_swr", parameters['swr'])

            self.state_manager.set_radio("s_meter_strength", parameters['strength'])
            threading.Event().wait(self.refresh_rate)

    def stop(self):
        self.stop_event.set()
        self.radio.disconnect()
        self.radio.stop_service()