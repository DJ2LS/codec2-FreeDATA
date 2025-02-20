import queue
from command import TxCommand
import api_validations
import base64
from queue import Queue
from p2p_connection import P2PConnection

class P2PConnectionCommand(TxCommand):

    def set_params_from_api(self, apiParams):
        self.origin = apiParams['origin']
        if not api_validations.validate_freedata_callsign(self.origin):
            self.origin = f"{self.origin}-0"

        self.destination = apiParams['destination']
        if not api_validations.validate_freedata_callsign(self.destination):
            self.destination = f"{self.destination}-0"


    def connect(self, event_queue: Queue, modem):
        pass

    def run(self, event_queue: Queue, modem):
        try:
            self.emit_event(event_queue)
            session = P2PConnection(self.config, modem, self.origin, self.destination, self.state_manager, self.event_manager, self.socket_interface_manager)
            print(session)
            if session.session_id:
                self.state_manager.register_p2p_connection_session(session)
                session.connect()
                return session
            return False

        except Exception as e:
            self.log(f"Error starting P2P Connection session: {e}", isWarning=True)

        return False