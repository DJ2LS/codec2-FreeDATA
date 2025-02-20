""" WORK IN PROGRESS by DJ2LS"""
"""
access command handler from external via: 
    self.socket_manager.command_server.command_handler.<function>
    self.socket_manager.data_server.data_handler.<function>

"""

import socketserver
import threading
import structlog
import select
from socket_interface_commands import SocketCommandHandler
from socket_interface_data import SocketDataHandler
import io

class CommandSocket(socketserver.BaseRequestHandler):
    #def __init__(self, request, client_address, server):
    def __init__(self, request, client_address, server, modem=None, state_manager=None, event_manager=None, config_manager=None, socket_interface_manager=None):
        self.state_manager = state_manager
        self.event_manager = event_manager
        self.config_manager = config_manager
        self.modem = modem
        self.logger = structlog.get_logger(type(self).__name__)
        self.socket_interface_manager = socket_interface_manager

        self.command_handler = SocketCommandHandler(request, self.modem, self.config_manager, self.state_manager, self.event_manager, self.socket_interface_manager)

        self.handlers = {
            'CONNECT': self.command_handler.handle_connect,
            'DISCONNECT': self.command_handler.handle_disconnect,
            'MYCALL': self.command_handler.handle_mycall,
            'BW': self.command_handler.handle_bw,
            'ABORT': self.command_handler.handle_abort,
            'PUBLIC': self.command_handler.handle_public,
            'CWID': self.command_handler.handle_cwid,
            'LISTEN': self.command_handler.handle_listen,
            'COMPRESSION': self.command_handler.handle_compression,
            'WINLINK SESSION': self.command_handler.handle_winlink_session,
            'VERSION': self.command_handler.handle_version,

        }
        # Register this CommandSocket's command_handler with the command_server
        if hasattr(self.socket_interface_manager, 'command_server'):
            self.socket_interface_manager.command_server.command_handler = self.command_handler
        super().__init__(request, client_address, server)

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def handle(self):
        self.log(f"Client connected: {self.client_address}")
        try:
            # Wrap the socket in a binary file-like object.
            file_obj = self.request.makefile('rb')
            # Setting newline='\r' makes a carriage return the delimiter for readline().
            text_file = io.TextIOWrapper(file_obj, encoding='utf-8', newline='\r')

            # Continuously read data until the connection is closed.
            while True:
                line = text_file.readline()
                # An empty string indicates that the connection has been closed.
                if line == "":
                    break
                self.log(f"<<<<< {line}")
                self.parse_command(line)
        finally:
            self.log(f"Command connection closed with {self.client_address}")

    def parse_command(self, data):
        for command in self.handlers:
            if data.startswith(command):
                # Extract command arguments after the command itself
                args = data[len(command):].strip().split()
                self.dispatch_command(command, args)
                return
        message = "WRONG \r"
        self.request.sendall(message.encode('utf-8'))

    def dispatch_command(self, command, data):
        if command in self.handlers:
            handler = self.handlers[command]
            handler(data)
        else:
            message = "WRONG \r"
            self.request.sendall(message.encode('utf-8'))


class DataSocket(socketserver.BaseRequestHandler):
    #def __init__(self, request, client_address, server):
    def __init__(self, request, client_address, server, modem=None, state_manager=None, event_manager=None, config_manager=None, socket_interface_manager=None):
        self.state_manager = state_manager
        self.event_manager = event_manager
        self.config_manager = config_manager
        self.modem = modem
        self.socket_interface_manager = socket_interface_manager

        self.data_handler = SocketDataHandler(request, self.modem, self.config_manager, self.state_manager, self.event_manager, self.socket_interface_manager)

        self.logger = structlog.get_logger(type(self).__name__)

        # not sure if we really need this
        #if hasattr(self.socket_interface_manager, 'data_server'):
        #    self.socket_interface_manager.data_server.data_handler = self.data_handler


        super().__init__(request, client_address, server)

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def handle(self):
        self.log(f"Data connection established with {self.client_address}")
        try:
            while True:
                
                ready_to_read, _, _ = select.select([self.request], [], [], 1)  # 1-second timeout
                if ready_to_read:
                    self.data = self.request.recv(1024).strip()
                    if not self.data:
                        break
                    try:
                        self.log(f"Data received from {self.client_address}: [{len(self.data)}] - {self.data.decode()}")
                    except Exception:
                        self.log(f"Data received from {self.client_address}: [{len(self.data)}] - {self.data}")


                    for session_id in self.state_manager.p2p_connection_sessions:
                        session = self.state_manager.p2p_connection_sessions[session_id]

                        print(f"sessions: {self.state_manager.p2p_connection_sessions}")
                        print(f"session_id: {session_id}")
                        print(f"session: {session}")
                        print(f"data to send: {self.data}")

                        print(session.p2p_data_tx_queue.empty())
                        session.p2p_data_tx_queue.put(self.data)
                        print(session.p2p_data_tx_queue.empty())

                # Check if there's something to send from the queue, without blocking
                """
                TODO This part isnt needed anymore, since socket_interface_data.py handles this
                
                for session_id in self.state_manager.p2p_connection_sessions:
                    session = self.state_manager.get_p2p_connection_session(session_id)
                    if not session.p2p_data_rx_queue.empty():
                        data_to_send = session.p2p_data_rx_queue.get_nowait()  # Use get_nowait to avoid blocking
                        self.request.sendall(data_to_send)
                        self.log(f"Sent data to {self.client_address}")
                """

        finally:
            self.log(f"Data connection closed with {self.client_address}")


#class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
#    allow_reuse_address = True


class CustomThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    allow_reuse_port = True

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, **kwargs):
        self.extra_args = kwargs
        super().__init__(server_address, RequestHandlerClass, bind_and_activate=bind_and_activate)

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, **self.extra_args)

class SocketInterfaceHandler:
    def __init__(self, modem, config_manager, state_manager, event_manager):
        self.modem = modem
        self.config_manager = config_manager
        self.config = self.config_manager.read()
        self.state_manager = state_manager
        self.event_manager = event_manager
        self.logger = structlog.get_logger(type(self).__name__)
        self.ip = self.config["SOCKET_INTERFACE"]["host"]
        self.command_port = self.config["SOCKET_INTERFACE"]["cmd_port"]
        self.data_port = self.config["SOCKET_INTERFACE"]["data_port"]
        self.command_server = None
        self.data_server = None
        self.command_server_thread = None
        self.data_server_thread = None
        #Not sure if this will be the permanent home for these items. This will allow us to use several callsigns.
        #Bandwidth is also sent to the command socket by the client. Not sure how to translate this info to freedata yet.
        self.socket_interface_callsigns = None
        self.connecting_callsign = None
        self.socket_interface_bandwidth = None

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def start_servers(self):

        if self.command_port == 0:
            self.command_port = 8300

        if self.data_port == 0:
            self.data_port = 8301

        # Method to start both command and data server threads
        self.command_server_thread = threading.Thread(target=self.run_server, args=(self.ip, self.command_port, CommandSocket))
        self.data_server_thread = threading.Thread(target=self.run_server, args=(self.ip, self.data_port, DataSocket))

        self.command_server_thread.start()
        self.data_server_thread.start()

        # this might not work
        #self.command_server = self.command_server_thread._target.__self__
        #self.data_server = self.data_server_thread._target.__self__


        self.log(f"Interfaces started")
        return self

    def run_server(self,ip, port, handler):
        try:
            with CustomThreadedTCPServer((ip, port), handler, modem=self.modem, state_manager=self.state_manager, event_manager=self.event_manager, config_manager=self.config_manager, socket_interface_manager = self) as server:
                self.log(f"Server starting on ip:port: {ip}:{port}")
                if port == self.command_port:
                    self.command_server = server
                else:
                    self.data_server = server
                server.serve_forever()
                self.log(f"Server started on ip:port: {ip}:{port}")
        except Exception as e:
            self.log(f"Error starting server on ip:port: {ip}:{port} | {e}", isWarning=True)

    def stop_servers(self):
        # Gracefully shutdown the server
        if self.command_server:
            self.command_server.shutdown()
            self.command_server_thread.join(3)

            del self.command_server
        if self.data_server:
            self.data_server.shutdown()
            self.data_server_thread.join(3)
            del self.data_server

        self.log(f"socket interfaces stopped")
