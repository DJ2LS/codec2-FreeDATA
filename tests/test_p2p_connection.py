import sys
import time

sys.path.append('freedata_server')

import unittest
import unittest.mock
from config import CONFIG
import helpers
import queue
import threading
import base64
from command_p2p_connection import P2PConnectionCommand
from state_manager import StateManager
from frame_dispatcher import DISPATCHER
import random
import structlog
import numpy as np
from event_manager import EventManager
from state_manager import StateManager
from data_frame_factory import DataFrameFactory
import codec2
import p2p_connection
from socket_interface import SocketInterfaceHandler
from socket_interface_commands import SocketCommandHandler
import socket


class TestModem:
    def __init__(self, event_q, state_q):
        self.data_queue_received = queue.Queue()
        self.demodulator = unittest.mock.Mock()
        self.event_manager = EventManager([event_q])
        self.logger = structlog.get_logger('Modem')
        self.states = StateManager(state_q)

    def getFrameTransmissionTime(self, mode):
        samples = 0
        c2instance = codec2.open_instance(mode.value)
        samples += codec2.api.freedv_get_n_tx_preamble_modem_samples(c2instance)
        samples += codec2.api.freedv_get_n_tx_modem_samples(c2instance)
        samples += codec2.api.freedv_get_n_tx_postamble_modem_samples(c2instance)
        time = samples / 8000
        return time

    def transmit(self, mode, repeats: int, repeat_delay: int, frames: bytearray) -> bool:
        # Simulate transmission time
        tx_time = self.getFrameTransmissionTime(mode) + 0.1  # PTT
        self.logger.info(f"TX {tx_time} seconds...")
        threading.Event().wait(tx_time)

        transmission = {
            'mode': mode,
            'bytes': frames,
        }
        self.data_queue_received.put(transmission)


class TestP2PConnectionSession(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('freedata_server/config.ini.example')
        cls.config = config_manager.read()
        cls.logger = structlog.get_logger("TESTS")
        cls.frame_factory = DataFrameFactory(cls.config)

        # ISS
        cls.iss_config_manager = config_manager
        cls.iss_state_manager = StateManager(queue.Queue())
        cls.iss_event_manager = EventManager([queue.Queue()])
        cls.iss_event_queue = queue.Queue()
        cls.iss_state_queue = queue.Queue()
        cls.iss_p2p_data_queue = queue.Queue()


        cls.iss_modem = TestModem(cls.iss_event_queue, cls.iss_state_queue)

        conf = cls.iss_config_manager.read()
        conf['SOCKET_INTERFACE']['cmd_port'] = 8000
        conf['SOCKET_INTERFACE']['data_port'] = 8001
        cls.iss_config_manager.write(conf)

        cls.iss_socket_interface_manager = SocketInterfaceHandler(cls.iss_modem, cls.iss_config_manager, cls.iss_state_manager, cls.iss_event_manager).start_servers()

        cls.iss_socket_cmd_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.iss_socket_cmd_client.connect(('127.0.0.1', 8000))

        cls.iss_socket_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.iss_socket_data_client.connect(('127.0.0.1', 8001))

        threading.Thread(target=cls.read_from_socket, args=[cls, cls.iss_socket_cmd_client, 'CMD', 'ISS'], daemon=False).start()
        threading.Thread(target=cls.read_from_socket, args=[cls, cls.iss_socket_data_client, 'DATA', 'ISS'], daemon=False).start()


        cls.iss_frame_dispatcher = DISPATCHER(cls.config,
                                              cls.iss_event_manager,
                                              cls.iss_state_manager,
                                              cls.iss_modem, cls.iss_socket_interface_manager)

        # IRS
        cls.irs_config_manager = config_manager
        cls.irs_state_manager = StateManager(queue.Queue())
        cls.irs_event_manager = EventManager([queue.Queue()])
        cls.irs_event_queue = queue.Queue()
        cls.irs_state_queue = queue.Queue()
        cls.irs_p2p_data_queue = queue.Queue()
        cls.irs_modem = TestModem(cls.irs_event_queue, cls.irs_state_queue)

        conf = cls.irs_config_manager.read()
        conf['SOCKET_INTERFACE']['cmd_port'] = 9000
        conf['SOCKET_INTERFACE']['data_port'] = 9001
        cls.irs_config_manager.write(conf)

        cls.irs_socket_interface_manager = SocketInterfaceHandler(cls.irs_modem, cls.irs_config_manager, cls.irs_state_manager, cls.irs_event_manager).start_servers()

        cls.irs_socket_cmd_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.irs_socket_cmd_client.connect(('127.0.0.1', 9000))

        cls.irs_socket_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.irs_socket_data_client.connect(('127.0.0.1', 8001))

        threading.Thread(target=cls.read_from_socket, args=[cls, cls.irs_socket_cmd_client, 'CMD', 'IRS'], daemon=False).start()
        threading.Thread(target=cls.read_from_socket, args=[cls, cls.irs_socket_data_client, 'DATA', 'IRS'], daemon=False).start()

        cls.irs_frame_dispatcher = DISPATCHER(cls.config,
                                              cls.irs_event_manager,
                                              cls.irs_state_manager,
                                              cls.irs_modem,cls.irs_socket_interface_manager)

        # Frame loss probability in %
        cls.loss_probability = 30

        cls.channels_running = True

        cls.connected_event = threading.Event()

        cls.disconnect_received = False

    def channelWorker(self, modem_transmit_queue: queue.Queue, frame_dispatcher: DISPATCHER):
        while self.channels_running:
            # Transfer data between both parties
            try:
                transmission = modem_transmit_queue.get(timeout=1)
                if random.randint(0, 100) < self.loss_probability:
                    self.logger.info(f"[{threading.current_thread().name}] Frame lost...")
                    continue

                frame_bytes = transmission['bytes']
                frame_dispatcher.process_data(frame_bytes, None, len(frame_bytes), 0, 0, "test")
            except queue.Empty:
                continue
        self.logger.info(f"[{threading.current_thread().name}] Channel closed.")

    def waitForSession(self, q, outbound=False):
        while True and self.channels_running:
            ev = q.get()
            print(ev)
            if 'P2P_CONNECTION_DISCONNECT_ACK' in ev or self.disconnect_received:
                self.logger.info(f"[{threading.current_thread().name}] session ended.")
                break

    def establishChannels(self):
        self.channels_running = True
        self.iss_to_irs_channel = threading.Thread(target=self.channelWorker,
                                                   args=[self.iss_modem.data_queue_received,
                                                         self.irs_frame_dispatcher],
                                                   name="ISS to IRS channel")
        self.iss_to_irs_channel.start()

        self.irs_to_iss_channel = threading.Thread(target=self.channelWorker,
                                                   args=[self.irs_modem.data_queue_received,
                                                         self.iss_frame_dispatcher],
                                                   name="IRS to ISS channel")
        self.irs_to_iss_channel.start()

    def waitAndCloseChannels(self):
        self.waitForSession(self.iss_event_queue, True)
        self.channels_running = False
        self.waitForSession(self.irs_event_queue, False)
        self.channels_running = False

    def generate_random_string(self, min_length, max_length):
        import string
        length = random.randint(min_length, max_length)
        return ''.join(random.choices(string.ascii_letters, k=length))#

    def read_from_socket(self, socket_instance, type=None, direction=None):
        while True:
            try:
                # Receive messages from the server
                data = socket_instance.recv(48)
                if not data:
                    # If no data is received, break out of the loop
                    print(f"Disconnected from server: {type}, {direction}")
                    break
                data = data.decode()
                print(f"\nReceived from server: {type}, {direction}: {data}\n", end='')
                if 'CONNECTED AA1AAA-1 BB2BBB-2 0' in data:
                    self.connected_event.set()

            except Exception as e:
                print(f"Error receiving data: {type}, {direction}: {e}")
                socket_instance.close()
                break

    def testConnect(self):

        self.loss_probability = 0
        self.establishChannels()

        time.sleep(2)
        cmd = 'CONNECT AA1AAA-1 BB2BBB-2 2300\r\n'
        self.iss_socket_cmd_client.sendall(cmd.encode('utf-8'))
        self.connected_event.wait()

        data = 'TEST\r\n'
        self.iss_socket_data_client.sendall(data.encode('utf-8'))

        self.waitAndCloseChannels()




if __name__ == '__main__':
    unittest.main()
