"""
FRAME DISPATCHER - We are dispatching the received frames to the needed functions


"""
import threading
import structlog
from modem_frametypes import FRAME_TYPE as FR_TYPE
import event_manager
from data_frame_factory import DataFrameFactory

from frame_handler import FrameHandler
from frame_handler_ping import PingFrameHandler
from frame_handler_cq import CQFrameHandler
from frame_handler_arq_session import ARQFrameHandler
from frame_handler_p2p_connection import P2PConnectionFrameHandler
from frame_handler_beacon import BeaconFrameHandler



class DISPATCHER():

    FRAME_HANDLER = {
        FR_TYPE.ARQ_SESSION_OPEN_ACK.value: {"class": ARQFrameHandler, "name": "ARQ OPEN ACK"},
        FR_TYPE.ARQ_SESSION_OPEN.value: {"class": ARQFrameHandler, "name": "ARQ Data Channel Open"},
        FR_TYPE.ARQ_SESSION_INFO_ACK.value: {"class": ARQFrameHandler, "name": "ARQ INFO ACK"},
        FR_TYPE.ARQ_SESSION_INFO.value: {"class": ARQFrameHandler, "name": "ARQ Data Channel Info"},
        FR_TYPE.P2P_CONNECTION_CONNECT.value: {"class": P2PConnectionFrameHandler, "name": "P2P Connection CONNECT"},
        FR_TYPE.P2P_CONNECTION_CONNECT_ACK.value: {"class": P2PConnectionFrameHandler, "name": "P2P Connection CONNECT ACK"},
        FR_TYPE.P2P_CONNECTION_DISCONNECT.value: {"class": P2PConnectionFrameHandler, "name": "P2P Connection DISCONNECT"},
        FR_TYPE.P2P_CONNECTION_DISCONNECT_ACK.value: {"class": P2PConnectionFrameHandler,
                                                   "name": "P2P Connection DISCONNECT ACK"},
        FR_TYPE.P2P_CONNECTION_PAYLOAD.value: {"class": P2PConnectionFrameHandler,
                                                   "name": "P2P Connection PAYLOAD"},
        FR_TYPE.P2P_CONNECTION_PAYLOAD_ACK.value: {"class": P2PConnectionFrameHandler,
                                                   "name": "P2P Connection PAYLOAD ACK"},

        #FR_TYPE.ARQ_CONNECTION_HB.value: {"class": ARQFrameHandler, "name": "ARQ HEARTBEAT"},
        #FR_TYPE.ARQ_CONNECTION_OPEN.value: {"class": ARQFrameHandler, "name": "ARQ OPEN SESSION"},
        FR_TYPE.ARQ_STOP.value: {"class": ARQFrameHandler, "name": "ARQ STOP"},
        FR_TYPE.ARQ_STOP_ACK.value: {"class": ARQFrameHandler, "name": "ARQ STOP ACK"},
        FR_TYPE.BEACON.value: {"class": BeaconFrameHandler, "name": "BEACON"},
        FR_TYPE.ARQ_BURST_FRAME.value:{"class": ARQFrameHandler, "name": "BURST FRAME"},
        FR_TYPE.ARQ_BURST_ACK.value: {"class": ARQFrameHandler, "name":  "BURST ACK"},
        FR_TYPE.CQ.value: {"class": CQFrameHandler, "name":  "CQ"},
        FR_TYPE.PING_ACK.value: {"class": FrameHandler, "name":  "PING ACK"},
        FR_TYPE.PING.value: {"class": PingFrameHandler, "name":  "PING"},
        FR_TYPE.QRV.value: {"class": FrameHandler, "name":  "QRV"},
        #FR_TYPE.IS_WRITING.value: {"class": FrameHandler, "name": "IS_WRITING"},
        #FR_TYPE.FEC.value: {"class": FrameHandler, "name":  "FEC"},
        #FR_TYPE.FEC_WAKEUP.value: {"class": FrameHandler, "name":  "FEC WAKEUP"},
    }

    def __init__(self, config, event_manager, states, modem, socket_interface_manager):
        self.log = structlog.get_logger("frame_dispatcher")

        self.log.info("loading frame dispatcher.....\n")
        self.config = config
        self.states = states
        self.event_manager = event_manager
        self.socket_interface_manager = socket_interface_manager
        self.stop_event = threading.Event()

        self._initialize_handlers(config, states)

        self.modem = modem
        self.data_queue_received = modem.data_queue_received

        self.arq_sessions = []


    def _initialize_handlers(self, config, states):
        """Initializes various data handlers."""

        self.frame_factory = DataFrameFactory(config)

    def start(self):
        """Starts worker threads for transmit and receive operations."""
        threading.Thread(target=self.worker_receive, name="Receive Worker", daemon=True).start()

    def stop(self):
        self.stop_event.set()

    def worker_receive(self) -> None:
        """Queue received data for processing"""
        while not self.stop_event.is_set():
            try:
                data = self.data_queue_received.get(timeout=1)
                if data:
                    self.process_data(
                        data['payload'],
                        data['freedv'],
                        data['bytes_per_frame'],
                        data['snr'],
                        data['frequency_offset'],
                        data['mode_name'],
                    )
            except Exception:
                continue

    def process_data(self, bytes_out, freedv, bytes_per_frame: int, snr, frequency_offset, mode_name) -> None:
        # get frame as dictionary
        deconstructed_frame = self.frame_factory.deconstruct(bytes_out, mode_name=mode_name)
        frametype = deconstructed_frame["frame_type_int"]
        if frametype not in self.FRAME_HANDLER:
            self.log.warning(
                "[DISPATCHER] ARQ - other frame type", frametype=FR_TYPE(frametype).name)
            return
        
        # instantiate handler
        handler_class = self.FRAME_HANDLER[frametype]['class']
        handler: FrameHandler = handler_class(self.FRAME_HANDLER[frametype]['name'],
                                self.config,
                                self.states,
                                self.event_manager,
                                self.modem, self.socket_interface_manager
                                              )
        handler.handle(deconstructed_frame, snr, frequency_offset, freedv, bytes_per_frame)

    def get_id_from_frame(self, data):
        if data[:1] == FR_TYPE.ARQ_SESSION_OPEN:
            return data[13:14]
        return None
