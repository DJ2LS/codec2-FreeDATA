import sys
sys.path.append('freedata_server')

import unittest
from config import CONFIG
from frame_dispatcher import DISPATCHER
import helpers
import queue
from state_manager import StateManager
from event_manager import EventManager
from command_ping import PingCommand
from command_cq import CQCommand
import modem
import frame_handler
from radio_manager import RadioManager

class TestProtocols(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('freedata_server/config.ini.example')
        cls.config = config_manager.read()

        cls.state_manager_queue = queue.Queue()
        cls.state_manager = StateManager(cls.state_manager_queue)

        cls.event_queue = queue.Queue()
        cls.event_manager = EventManager([cls.event_queue])

        cls.radio_manager = RadioManager(cls.config, cls.state_manager, cls.event_manager, None)
        cls.modem_transmit_queue = queue.Queue()

        cls.modem = modem.RF(cls.config, cls.event_queue, queue.Queue(), queue.Queue(), cls.state_manager, cls.radio_manager)
        modem.TESTMODE = True
        frame_handler.TESTMODE = True

        #cls.freedata_server.start_modem()
        cls.frame_dispatcher = DISPATCHER(cls.config, 
                                          cls.event_manager,
                                          cls.state_manager,
                                          cls.modem, None)

    def shortcutTransmission(self, frame_bytes):
        self.frame_dispatcher.process_data(frame_bytes, None, len(frame_bytes), 0, 0, mode_name="TEST")

    def assertEventReceivedType(self, event_type):
        ev = self.event_queue.get()
        self.assertIn('type', ev)
        self.assertIn('received', ev)
        self.assertEqual(ev['received'], event_type)

    def testPingWithAck(self):
        # Run ping command
        api_params = { "dxcall": "AA1AAA-1"}
        ping_cmd = PingCommand(self.config, self.state_manager, self.event_manager, api_params)
        #ping_cmd.run(self.event_queue, self.freedata_server)
        frame = ping_cmd.test(self.event_queue)
        # Shortcut the transmit queue directly to the frame dispatcher
        self.shortcutTransmission(frame)
        self.assertEventReceivedType('PING')

        event_frame = self.event_queue.get()
        # Check ACK
        self.shortcutTransmission(event_frame)
        self.assertEventReceivedType('PING_ACK')
        print("PING/PING ACK CHECK SUCCESSFULLY")

    def testCQWithQRV(self):
        self.config['STATION']['respond_to_cq'] = True
        self.state_manager.set_channel_busy_condition_codec2(False)

        api_params = {}
        cmd = CQCommand(self.config, self.state_manager, self.event_manager, api_params)
        #cmd.run(self.event_queue, self.freedata_server)
        frame = cmd.test(self.event_queue)

        self.shortcutTransmission(frame)
        self.assertEventReceivedType('CQ')

        event_frame = self.event_queue.get()
        # Check QRV
        self.shortcutTransmission(event_frame)
        self.assertEventReceivedType('QRV')
        print("CQ/QRV CHECK SUCCESSFULLY")

if __name__ == '__main__':
    unittest.main()
