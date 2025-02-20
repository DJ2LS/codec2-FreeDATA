import threading
from enum import Enum
from modem_frametypes import FRAME_TYPE
from codec2 import FREEDV_MODE
import data_frame_factory
import structlog
import random
from queue import Queue
import time
from command_arq_raw import ARQRawCommand
import numpy as np
import base64
from arq_data_type_handler import ARQDataTypeHandler, ARQ_SESSION_TYPES
from arq_session_iss import ARQSessionISS

class States(Enum):
    NEW = 0
    CONNECTING = 1
    CONNECT_SENT = 2
    CONNECT_ACK_SENT = 3
    CONNECTED = 4
    #HEARTBEAT_SENT = 5
    #HEARTBEAT_ACK_SENT = 6
    PAYLOAD_SENT = 7
    ARQ_SESSION = 8
    DISCONNECTING = 9
    DISCONNECTED = 10
    FAILED = 11



class P2PConnection:
    STATE_TRANSITION = {
        States.NEW: {
            FRAME_TYPE.P2P_CONNECTION_CONNECT.value: 'connected_irs',
        },
        States.CONNECTING: {
            FRAME_TYPE.P2P_CONNECTION_CONNECT_ACK.value: 'connected_iss',
        },
        States.CONNECTED: {
            FRAME_TYPE.P2P_CONNECTION_CONNECT.value: 'connected_irs',
            FRAME_TYPE.P2P_CONNECTION_CONNECT_ACK.value: 'connected_iss',
            FRAME_TYPE.P2P_CONNECTION_PAYLOAD.value: 'received_data',
            FRAME_TYPE.P2P_CONNECTION_DISCONNECT.value: 'received_disconnect',
        },
        States.PAYLOAD_SENT: {
            FRAME_TYPE.P2P_CONNECTION_PAYLOAD_ACK.value: 'transmitted_data',
        },
        States.DISCONNECTING: {
            FRAME_TYPE.P2P_CONNECTION_DISCONNECT_ACK.value: 'received_disconnect_ack',
        },
        States.DISCONNECTED: {
            FRAME_TYPE.P2P_CONNECTION_DISCONNECT.value: 'received_disconnect',
            FRAME_TYPE.P2P_CONNECTION_DISCONNECT_ACK.value: 'received_disconnect_ack',

        },
    }

    def __init__(self, config: dict, modem, origin: str, destination: str, state_manager, event_manager, socket_interface_manager=None):
        self.logger = structlog.get_logger(type(self).__name__)
        self.config = config

        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)

        self.socket_interface_manager = socket_interface_manager

        self.destination = destination
        self.origin = origin
        self.bandwidth = 0

        self.state_manager = state_manager
        self.event_manager = event_manager
        self.modem = modem
        if self.modem:
            self.modem.demodulator.set_decode_mode(is_p2p_connection=True)

        self.p2p_data_tx_queue = Queue()
        #Remove after testing
        self.p2p_data_rx_queue = Queue()

        self.arq_data_type_handler = ARQDataTypeHandler(self.event_manager, self.state_manager)


        self.state = States.NEW
        self.session_id = self.generate_id()

        self.event_frame_received = threading.Event()

        self.RETRIES_CONNECT = 5
        self.TIMEOUT_CONNECT = 5
        self.TIMEOUT_DATA = 5
        self.RETRIES_DATA = 5
        self.ENTIRE_CONNECTION_TIMEOUT = 100

        self.is_ISS = False # Indicator, if we are ISS or IRS

        self.last_data_timestamp= time.time()
        self.start_data_processing_worker()


    def start_data_processing_worker(self):
        """Starts a worker thread to monitor the transmit data queue and process data."""

        def data_processing_worker():
            while True:
                if time.time() > self.last_data_timestamp + self.ENTIRE_CONNECTION_TIMEOUT and self.state is not States.ARQ_SESSION:
                    self.disconnect()
                    return

                if not self.p2p_data_tx_queue.empty() and self.state == States.CONNECTED:
                    self.process_data_queue()
                threading.Event().wait(0.1)




        # Create and start the worker thread
        worker_thread = threading.Thread(target=data_processing_worker, daemon=True)
        worker_thread.start()

    def generate_id(self):
        while True:
            random_int = random.randint(1,255)
            if random_int not in self.state_manager.p2p_connection_sessions:
                return random_int

            if len(self.state_manager.p2p_connection_sessions) >= 255:
                return False

    def set_details(self, snr, frequency_offset):
        self.snr = snr
        self.frequency_offset = frequency_offset

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}][id={self.session_id}][state={self.state}][ISS={bool(self.is_ISS)}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def set_state(self, state):
        if self.state == state:
            self.log(f"{type(self).__name__} state {self.state.name} unchanged.")
        else:
            self.log(f"{type(self).__name__} state change from {self.state.name} to {state.name}")
        self.state = state

    def on_frame_received(self, frame):
        self.last_data_timestamp = time.time()
        self.event_frame_received.set()
        self.log(f"Received {frame['frame_type']}")
        frame_type = frame['frame_type_int']
        if self.state in self.STATE_TRANSITION:
            if frame_type in self.STATE_TRANSITION[self.state]:
                action_name = self.STATE_TRANSITION[self.state][frame_type]
                response = getattr(self, action_name)(frame)

                return

        self.log(f"Ignoring unknown transition from state {self.state.name} with frame {frame['frame_type']}")

    def transmit_frame(self, frame: bytearray, mode='auto'):
        self.log("Transmitting frame")
        if mode in ['auto']:
            mode = self.get_mode_by_speed_level(self.speed_level)

        self.modem.transmit(mode, 1, 1, frame)

    def transmit_wait_and_retry(self, frame_or_burst, timeout, retries, mode):
        while retries > 0:
            self.event_frame_received = threading.Event()
            if isinstance(frame_or_burst, list): burst = frame_or_burst
            else: burst = [frame_or_burst]
            for f in burst:
                self.transmit_frame(f, mode)
            self.event_frame_received.clear()
            self.log(f"Waiting {timeout} seconds...")
            if self.event_frame_received.wait(timeout):
                return
            self.log("Timeout!")
            retries = retries - 1

        #self.connected_iss() # override connection state for simulation purposes
        self.session_failed()

    def launch_twr(self, frame_or_burst, timeout, retries, mode):
        twr = threading.Thread(target = self.transmit_wait_and_retry, args=[frame_or_burst, timeout, retries, mode], daemon=True)
        twr.start()

    def transmit_and_wait_irs(self, frame, timeout, mode):
        self.event_frame_received.clear()
        self.transmit_frame(frame, mode)
        self.log(f"Waiting {timeout} seconds...")
        #if not self.event_frame_received.wait(timeout):
        #    self.log("Timeout waiting for ISS. Session failed.")
        #    self.transmission_failed()

    def launch_twr_irs(self, frame, timeout, mode):
        thread_wait = threading.Thread(target = self.transmit_and_wait_irs,
                                       args = [frame, timeout, mode], daemon=True)
        thread_wait.start()

    def connect(self):
        self.set_state(States.CONNECTING)
        self.is_ISS = True

        session_open_frame = self.frame_factory.build_p2p_connection_connect(self.destination, self.origin, self.session_id)
        self.launch_twr(session_open_frame, self.TIMEOUT_CONNECT, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        return

    def connected_iss(self, frame=None):
        self.log("CONNECTED ISS...........................")
        self.set_state(States.CONNECTED)
        self.is_ISS = True

        if self.socket_interface_manager and hasattr(self.socket_interface_manager.command_server, "command_handler"):
            self.socket_interface_manager.command_server.command_handler.socket_respond_connected(self.origin, self.destination, self.bandwidth)

    def connected_irs(self, frame):
        self.log("CONNECTED IRS...........................")
        self.state_manager.register_p2p_connection_session(self)
        self.set_state(States.CONNECTED)
        self.is_ISS = False
        self.orign = frame["origin"]
        self.destination = frame["destination_crc"]
        #If these 2 lines are not here, the receiving station does not reply back with an ACK to a P2P_CONNECTION_CONNECT packet. Is this intentional? Leaving here for testing for now.
        session_open_frame = self.frame_factory.build_p2p_connection_connect_ack(self.destination, self.origin, self.session_id)
        self.launch_twr_irs(session_open_frame, self.ENTIRE_CONNECTION_TIMEOUT, mode=FREEDV_MODE.signalling)

        if self.socket_interface_manager and hasattr(self.socket_interface_manager.command_server, "command_handler"):
            self.socket_interface_manager.command_server.command_handler.socket_respond_connected(self.origin, self.destination, self.bandwidth)


    def session_failed(self):
        self.set_state(States.FAILED)
        if self.socket_interface_manager and hasattr(self.socket_interface_manager.command_server, "command_handler"):
            self.socket_interface_manager.command_server.command_handler.socket_respond_disconnected()

    def process_data_queue(self, frame=None):
        if self.p2p_data_tx_queue.empty():
            return
        print("processing data....")

        data = self.p2p_data_tx_queue.get()
        sequence_id = random.randint(0,255)

        if  len(data) <= 11:
            mode = FREEDV_MODE.signalling
        elif 11 < len(data) <= 32:
            mode = FREEDV_MODE.datac4
        else:
            self.transmit_arq(data)
            return

        payload = self.frame_factory.build_p2p_connection_payload(mode, self.session_id, sequence_id, data)
        self.launch_twr(payload, self.TIMEOUT_DATA, self.RETRIES_DATA,mode=mode)
        self.set_state(States.PAYLOAD_SENT)

        return

    def received_data(self, frame):
        print(f"received data...: {frame}")

        ack_data = self.frame_factory.build_p2p_connection_payload_ack(self.session_id, 0)
        self.launch_twr_irs(ack_data, self.ENTIRE_CONNECTION_TIMEOUT, mode=FREEDV_MODE.signalling_ack)

        print(vars(self.socket_interface_manager.data_server))
        if self.socket_interface_manager and hasattr(self.socket_interface_manager.data_server, "data_handler"):
            self.socket_interface_manager.data_server.data_handler.send_data_to_client(frame['data'].rstrip('\x00'))


    def transmitted_data(self, frame):
        print("transmitted data...")
        self.set_state(States.CONNECTED)

    def disconnect(self):
        if self.state not in [States.DISCONNECTING, States.DISCONNECTED]:
            self.set_state(States.DISCONNECTING)
            disconnect_frame = self.frame_factory.build_p2p_connection_disconnect(self.session_id)
            self.launch_twr(disconnect_frame, self.TIMEOUT_CONNECT, self.RETRIES_CONNECT, mode=FREEDV_MODE.signalling)
        return

    def received_disconnect(self, frame):
        self.log("DISCONNECTED...............")
        self.set_state(States.DISCONNECTED)
        if self.socket_interface_manager:
            self.socket_interface_manager.command_server.command_handler.socket_respond_disconnected()
        self.is_ISS = False
        disconnect_ack_frame = self.frame_factory.build_p2p_connection_disconnect_ack(self.session_id)
        self.launch_twr_irs(disconnect_ack_frame, self.ENTIRE_CONNECTION_TIMEOUT, mode=FREEDV_MODE.signalling)

    def received_disconnect_ack(self, frame):
        self.log("DISCONNECTED...............")
        self.set_state(States.DISCONNECTED)
        if self.socket_interface_manager:
            self.socket_interface_manager.command_server.command_handler.socket_respond_disconnected()

    def transmit_arq(self, data):
        """
        This function needs to be fixed - we want to send ARQ data within a p2p connection
        check p2p_connection handler in arq_data_type_handler

        """
        self.set_state(States.ARQ_SESSION)



        print("----------------------------------------------------------------")
        print(self.destination)
        print(self.state_manager.p2p_connection_sessions)

        prepared_data, type_byte = self.arq_data_type_handler.prepare(data, ARQ_SESSION_TYPES.p2p_connection)
        iss = ARQSessionISS(self.config, self.modem, self.destination, self.state_manager, prepared_data, type_byte)
        iss.id = self.session_id
        if iss.id:
            self.state_manager.register_arq_iss_session(iss)
            iss.start()
            return iss

    def transmitted_arq(self):
        self.last_data_timestamp = time.time()
        self.set_state(States.CONNECTED)
        #socket_interface_manager.command_server.<command>

    def received_arq(self, data):
        self.last_data_timestamp = time.time()
        self.set_state(States.CONNECTED)
        #self.p2p_data_rx_queue.put(data)
        #socket_interface_manager.command_server.<command>
        self.socket_interface_manager.data_server.data_handler.send_data_to_client(data)
