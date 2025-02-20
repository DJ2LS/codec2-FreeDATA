from data_frame_factory import DataFrameFactory
import queue
from codec2 import FREEDV_MODE
import structlog
from state_manager import StateManager
from arq_data_type_handler import ARQDataTypeHandler


class TxCommand():

    def __init__(self, config: dict, state_manager: StateManager, event_manager, apiParams:dict = {}, socket_interface_manager=None):
        self.config = config
        self.logger = structlog.get_logger(type(self).__name__)
        self.state_manager = state_manager
        self.event_manager = event_manager
        self.set_params_from_api(apiParams)
        self.frame_factory = DataFrameFactory(config)
        self.arq_data_type_handler = ARQDataTypeHandler(event_manager, state_manager)
        self.socket_interface_manager = socket_interface_manager

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def set_params_from_api(self, apiParams):
        pass

    def get_name(self):
        return type(self).__name__

    def emit_event(self, event_queue):
        pass

    def log_message(self):
        return f"Running {self.get_name()}"

    def build_frame(self):
        pass

    def get_tx_mode(self):
        return FREEDV_MODE.signalling
    
    def make_modem_queue_item(self, mode, repeat, repeat_delay, frame):
        return {
            'mode': mode,
            'repeat': repeat,
            'repeat_delay': repeat_delay,
            'frame': frame,
        }

    def transmit(self, modem):
        frame = self.build_frame()
        modem.transmit(self.get_tx_mode(), 1, 0, frame)

    def run(self, event_queue: queue.Queue, modem):
        self.emit_event(event_queue)
        self.logger.info(self.log_message())
        self.transmit(modem)

    def test(self, event_queue: queue.Queue):
        self.emit_event(event_queue)
        self.logger.info(self.log_message())
        return self.build_frame()
