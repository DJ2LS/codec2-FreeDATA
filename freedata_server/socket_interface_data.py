""" WORK IN PROGRESS by DJ2LS"""


class SocketDataHandler:

    def __init__(self, cmd_request, modem, config_manager, state_manager, event_manager, socket_interface_manager):
        self.cmd_request = cmd_request
        self.modem = modem
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.event_manager = event_manager
        self.socket_interface_manager = socket_interface_manager
        self.session = None

    def send_response(self, message):
        full_message = f"{message}\r\n"
        self.cmd_request.sendall(full_message.encode())

    def send_data_to_client(self, data):
        self.cmd_request.sendall(data)
