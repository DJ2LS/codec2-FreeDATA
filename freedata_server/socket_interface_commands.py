""" WORK IN PROGRESS by DJ2LS"""
from command_p2p_connection import P2PConnectionCommand
import structlog

class SocketCommandHandler:

    def __init__(self, cmd_request, modem, config_manager, state_manager, event_manager, socket_interface_manager):
        self.logger = structlog.get_logger(type(self).__name__)
        self.cmd_request = cmd_request
        self.modem = modem
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.event_manager = event_manager
        self.socket_interface_manager = socket_interface_manager
        self.session = None

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def send_response(self, message):
        self.log(f">>>>> {message}")
        full_message = f"{message}\r"
        self.cmd_request.sendall(full_message.encode())

    def handle_connect(self, data):
        try:
            params = {
                'origin': data[0],
                'destination': data[1],
            }

            cmd = P2PConnectionCommand(self.config_manager.read(), self.state_manager, self.event_manager, params, self.socket_interface_manager)
            self.session = cmd.run(self.event_manager.queues, self.modem)
            self.send_response(f"OK")
            self.send_response(f"REGISTERED {data[0]}")
            self.send_response(f"UNENCRYPTED LINK")
            self.socket_interface_manager.connecting_callsign = data[0]
            #if self.session.session_id:
            #    self.state_manager.register_p2p_connection_session(self.session)
            #    self.send_response("OK")
            #    self.session.connect()
            #else:
            #    self.send_response("ERROR")
        except:
            self.send_response(f"ERR: {data}")

    def handle_disconnect(self, data):
        self.send_response(f"NOT IMPLEMENTED: {data}")

    def handle_mycall(self, data):
        #Storing all of the callsigns assigned by client, to make sure they are checked later in new frames.
        self.socket_interface_manager.socket_interface_callsigns = data
        self.send_response(f"OK")
        self.send_response(f"UNENCRYPTED LINK")
        self.send_response(f"ENCRYPTION DISABLED")

    def handle_bw(self, data):
        # Logic for handling BW command
        #self.socket_interface_manager.bandwidth = data
        self.send_response(f"OK")

    def handle_abort(self, data):
        # Logic for handling ABORT command
        self.send_response(f"NOT IMPLEMENTED: {data}")

    def handle_public(self, data):
        # Logic for handling PUBLIC command
        self.send_response(f"OK")

    def handle_cwid(self, data):
        # Logic for handling CWID command
        self.send_response(f"NOT IMPLEMENTED: {data}")

    def handle_listen(self, data):
        # Logic for handling LISTEN command
        self.send_response(f"OK")

    def handle_compression(self, data):
        # Logic for handling COMPRESSION command
        # We are always sending OK, as we have our own compression
        self.send_response(f"OK")

    def handle_winlink_session(self, data):
        # Logic for handling WINLINK SESSION command
        self.send_response(f"NOT IMPLEMENTED: {data}")

    def handle_version(self, data):
        # Logic for handling VERSION command
        # maybe we need to use a different version, like 5.0
        self.send_response(f"VERSION FREEDATA")

    def socket_respond_disconnected(self):
        self.send_response("DISCONNECTED")

    def socket_respond_connected(self, origin, destination, bandwidth):
        print("[socket interface_commands] socket_respond_connected")
        message = f"CONNECTED {self.socket_interface_manager.connecting_callsign} {destination} {bandwidth}"
        self.send_response(f"UNENCRYPTED LINK")
        self.send_response(f"LINK REGISTERED")
        self.send_response(message)

    def socket_respond_ptt(self, state):
        """ send the PTT state via command socket"""
        if state:
            message = f"PTT ON"
        else:
            message = f"PTT OFF"

        self.send_response(message)
