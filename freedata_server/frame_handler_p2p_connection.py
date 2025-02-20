from queue import Queue
import frame_handler
from event_manager import EventManager
from state_manager import StateManager
from modem_frametypes import FRAME_TYPE as FR
from p2p_connection import P2PConnection

class P2PConnectionFrameHandler(frame_handler.FrameHandler):

    def follow_protocol(self):

        if not self.should_respond():
            return

        frame = self.details['frame']
        session_id = frame['session_id']
        snr = self.details["snr"]
        frequency_offset = self.details["frequency_offset"]

        if frame['frame_type_int'] == FR.P2P_CONNECTION_CONNECT.value:

            # Lost OPEN_ACK case .. ISS will retry opening a session
            if session_id in self.states.arq_irs_sessions:
                session = self.states.p2p_connection_sessions[session_id]

            # Normal case when receiving a SESSION_OPEN for the first time
            else:
            #    if self.states.check_if_running_arq_session():
            #        self.logger.warning("DISCARDING SESSION OPEN because of ongoing ARQ session ", frame=frame)
            #        return
                print(frame)
                session = P2PConnection(self.config,
                                        self.modem,
                                        frame['origin'],
                                        frame['destination_crc'],
                                        self.states, self.event_manager, self.socket_interface_manager)
                session.session_id = session_id
                self.states.register_p2p_connection_session(session)

        elif frame['frame_type_int'] in [
            FR.P2P_CONNECTION_CONNECT_ACK.value,
            FR.P2P_CONNECTION_DISCONNECT.value,
            FR.P2P_CONNECTION_DISCONNECT_ACK.value,
            FR.P2P_CONNECTION_PAYLOAD.value,
            FR.P2P_CONNECTION_PAYLOAD_ACK.value,
        ]:
            session = self.states.get_p2p_connection_session(session_id)

        else:
            self.logger.warning("DISCARDING FRAME", frame=frame)
            return

        session.set_details(snr, frequency_offset)
        session.on_frame_received(frame)
