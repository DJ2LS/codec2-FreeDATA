import threading
import frame_dispatcher
import modem
import structlog
import audio
import radio_manager
from socket_interface import SocketInterfaceHandler
import queue

class SM:
    def __init__(self, app):
        self.log = structlog.get_logger("service manager")
        self.app = app
        self.modem = False
        self.app.radio_manager = False
        self.config = self.app.config_manager.read()
        self.modem_fft = app.modem_fft
        self.modem_service = app.modem_service
        self.state_manager = app.state_manager
        self.event_manager = app.event_manager
        self.schedule_manager = app.schedule_manager
        self.socket_interface_manager = None

        self.shutdown_flag = threading.Event()


        self.runner_thread = threading.Thread(
            target=self.runner, name="runner thread", daemon=False
        )

        self.runner_thread.start()


    def runner(self):
        while not self.shutdown_flag.is_set():
            try:
                cmd = self.modem_service.get()
                if self.shutdown_flag.is_set():
                    return

                if cmd in ['start'] and not self.modem:
                    self.config = self.app.config_manager.read()

                    self.start_radio_manager()
                    self.start_modem()

                    if self.config['SOCKET_INTERFACE']['enable']:
                        self.socket_interface_manager = SocketInterfaceHandler(self.modem, self.app.config_manager, self.state_manager, self.event_manager).start_servers()
                    else:
                        self.socket_interface_manager = None




                elif cmd in ['stop'] and self.modem:
                    self.stop_modem()
                    self.stop_radio_manager()
                    if self.config['SOCKET_INTERFACE']['enable'] and self.socket_interface_manager:
                        self.socket_interface_manager.stop_servers()
                    # we need to wait a bit for avoiding a portaudio crash
                    threading.Event().wait(0.5)

                elif cmd in ['restart']:
                    self.stop_modem()
                    self.stop_radio_manager()
                    if self.config['SOCKET_INTERFACE']['enable'] and self.socket_interface_manager:
                        self.socket_interface_manager.stop_servers()
                        del self.socket_interface_manager
                        self.socket_interface_manager = SocketInterfaceHandler(self.modem, self.app.config_manager, self.state_manager, self.event_manager).start_servers()
                    # we need to wait a bit for avoiding a portaudio crash
                    threading.Event().wait(0.5)

                    self.config = self.app.config_manager.read()
                    self.start_radio_manager()

                    if self.start_modem():
                        self.event_manager.modem_restarted()

                else:
                    if not self.shutdown_flag.is_set():
                        self.log.warning("[SVC] freedata_server command processing failed", cmd=cmd, state=self.state_manager.is_modem_running)

            # Queue is empty
            except queue.Empty:
                pass

            # finally clear processing commands
            self.modem_service.queue.clear()

    def start_modem(self):

        if self.config['STATION']['mycall'] in ['XX1XXX']:
            self.log.warning("wrong callsign in config! interrupting startup")
            return False

        if self.state_manager.is_modem_running:
            self.log.warning("freedata_server already running")
            return False

        # test audio devices
        audio_test = self.test_audio()
        if False in audio_test or None in audio_test or self.state_manager.is_modem_running:
            self.log.warning("starting freedata_server failed", input_test=audio_test[0], output_test=audio_test[1])
            self.state_manager.set("is_modem_running", False)
            self.event_manager.modem_failed()
            return False

        self.log.info("starting freedata_server....")
        self.modem = modem.RF(self.config, self.event_manager, self.modem_fft, self.modem_service, self.state_manager, self.app.radio_manager)

        self.frame_dispatcher = frame_dispatcher.DISPATCHER(self.config, 
                                                            self.event_manager,
                                                            self.state_manager,
                                                            self.modem,
                                                            self.socket_interface_manager)
        self.frame_dispatcher.start()

        self.event_manager.modem_started()
        self.state_manager.set("is_modem_running", True)
        self.modem.start_modem()
        self.schedule_manager.start(self.modem)

        return True
        
    def stop_modem(self):
        self.log.warning("stopping modem....")
        try:
            if self.modem and hasattr(self.app, 'modem_service'):
                self.modem.stop_modem()
                del self.modem
                self.modem = False
        except AttributeError:
            pass
        self.state_manager.set("is_modem_running", False)
        try:
            if self.schedule_manager and hasattr(self.app, 'schedule_manager'):
                self.schedule_manager.stop()
        except AttributeError:
            pass
        try:
            if self.frame_dispatcher and hasattr(self.app, 'frame_dispatcher'):
                self.frame_dispatcher.stop()
        except AttributeError:
            pass

        self.event_manager.modem_stopped()

    def test_audio(self):
        try:
            audio_test = audio.test_audio_devices(self.config['AUDIO']['input_device'],
                                                  self.config['AUDIO']['output_device'])
            self.log.info("tested audio devices", result=audio_test)

            return audio_test
        except Exception as e:
            self.log.error("Error testing audio devices", e=e)
            return [False, False]

    def start_radio_manager(self):
        self.app.radio_manager = radio_manager.RadioManager(self.config, self.state_manager, self.event_manager, self.socket_interface_manager)

    def stop_radio_manager(self):
        if hasattr(self.app, 'radio_manager'):
            self.app.radio_manager.stop()
            del self.app.radio_manager

    def shutdown(self):
        self.log.warning("[SHUTDOWN] stopping service manager....")
        self.modem_service.put("stop")
        threading.Event().wait(2) # we need some time before processing with the shutdown_event_flag
        self.shutdown_flag.set()
        self.runner_thread.join(0.5)
