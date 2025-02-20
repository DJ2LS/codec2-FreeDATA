from modem_frametypes import FRAME_TYPE as FR_TYPE
import helpers
import codec2
import maidenhead

class DataFrameFactory:

    LENGTH_SIG0_FRAME = 14
    LENGTH_SIG1_FRAME = 14
    LENGTH_ACK_FRAME = 3

    """
        helpers.set_flag(byte, 'DATA-ACK-NACK', True, FLAG_POSITIONS)
        helpers.get_flag(byte, 'DATA-ACK-NACK', FLAG_POSITIONS)    
    """
    ARQ_FLAGS = {
        'FINAL': 0,  # Bit-position for indicating the FINAL state
        'ABORT': 1, # Bit-position for indicating the ABORT request
        'CHECKSUM': 2,  # Bit-position for indicating the CHECKSUM is correct or not
    }

    BEACON_FLAGS = {
        'AWAY_FROM_KEY': 0,  # Bit-position for indicating the AWAY FROM KEY state
    }

    def __init__(self, config):

        self.myfullcall = f"{config['STATION']['mycall']}-{config['STATION']['myssid']}"
        self.mygrid = maidenhead.generate_full_maidenhead(config["STATION"]["mygrid"])

        # table for holding our frame templates
        self.template_list = {}

        self._load_broadcast_templates()
        self._load_ping_templates()
        self._load_arq_templates()
        self._load_p2p_connection_templates()

    def _load_broadcast_templates(self):
        # cq frame
        self.template_list[FR_TYPE.CQ.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "origin": 6,
            "gridsquare": 4
        }

        # qrv frame
        self.template_list[FR_TYPE.QRV.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "origin": 6,
            "gridsquare": 4,
            "snr": 1
        }

        # beacon frame
        self.template_list[FR_TYPE.BEACON.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "origin": 6,
            "gridsquare": 4,
            "flag": 1
        }

    def _load_ping_templates(self):
        # ping frame
        self.template_list[FR_TYPE.PING.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "destination_crc": 3,
            "origin_crc": 3,
            "origin": 6
        }

        # ping ack
        self.template_list[FR_TYPE.PING_ACK.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "destination_crc": 3,
            "origin_crc": 3,
            "gridsquare": 4,
            "snr": 1,
        }


    def _load_arq_templates(self):

        self.template_list[FR_TYPE.ARQ_SESSION_OPEN.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "destination_crc": 3,
            "origin": 6,
            "session_id": 1,
            "maximum_bandwidth": 2,
            "protocol_version" : 1
        }

        self.template_list[FR_TYPE.ARQ_SESSION_OPEN_ACK.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "session_id": 1,
            "origin": 6,
            "destination_crc": 3,
            "version": 1,
            "snr": 1,
            "flag": 1,
        }

        self.template_list[FR_TYPE.ARQ_SESSION_INFO.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "session_id": 1,
            "total_length": 4,
            "total_crc": 4,
            "snr": 1,
            "flag": 1,
            "type": 1,
        }

        self.template_list[FR_TYPE.ARQ_SESSION_INFO_ACK.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "session_id": 1,
            "offset": 4,
            "snr": 1,
            "speed_level": 1,
            "frames_per_burst": 1,
            "flag": 1,
        }

        self.template_list[FR_TYPE.ARQ_STOP.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "session_id": 1,
        }

        self.template_list[FR_TYPE.ARQ_STOP_ACK.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "session_id": 1,
        }

        # arq burst frame
        self.template_list[FR_TYPE.ARQ_BURST_FRAME.value] = {
            "frame_length": None,
            "session_id": 1,
            "speed_level": 1,
            "offset": 4,
            "data": "dynamic",
        }

        # arq burst ack
        self.template_list[FR_TYPE.ARQ_BURST_ACK.value] = {
            "frame_length": self.LENGTH_ACK_FRAME,
            "session_id": 1,
            #"offset":4,
            "speed_level": 1,
            #"frames_per_burst": 1,
            #"snr": 1,
            "flag": 1,
        }
    
    def _load_p2p_connection_templates(self):
        # p2p connect request
        self.template_list[FR_TYPE.P2P_CONNECTION_CONNECT.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "destination_crc": 3,
            "origin": 6,
            "session_id": 1,
        }
        
        # connect ACK
        self.template_list[FR_TYPE.P2P_CONNECTION_CONNECT_ACK.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "destination_crc": 3,
            "origin": 6,
            "session_id": 1,
        }
        
        # heartbeat for "is alive"
        self.template_list[FR_TYPE.P2P_CONNECTION_HEARTBEAT.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "session_id": 1,
        }

        # ack heartbeat
        self.template_list[FR_TYPE.P2P_CONNECTION_HEARTBEAT_ACK.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "session_id": 1,
        }

        # p2p payload frames
        self.template_list[FR_TYPE.P2P_CONNECTION_PAYLOAD.value] = {
            "frame_length": None,
            "session_id": 1,
            "sequence_id": 1,
            "data": "dynamic",
        }

        # p2p payload frame ack
        self.template_list[FR_TYPE.P2P_CONNECTION_PAYLOAD_ACK.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "session_id": 1,
            "sequence_id": 1,
        }
        
        # heartbeat for "is alive"
        self.template_list[FR_TYPE.P2P_CONNECTION_DISCONNECT.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "session_id": 1,
        }

        # ack heartbeat
        self.template_list[FR_TYPE.P2P_CONNECTION_DISCONNECT_ACK.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "session_id": 1,
        }



    def construct(self, frametype, content, frame_length = LENGTH_SIG1_FRAME):
        frame_template = self.template_list[frametype.value]

        if isinstance(frame_template["frame_length"], int):
            frame_length = frame_template["frame_length"]
        else:
            frame_length -= 2

        frame = bytearray(frame_length)
        if frametype in [FR_TYPE.ARQ_BURST_ACK]:
            buffer_position = 0
        else:
            frame[:1] = bytes([frametype.value])
            buffer_position = 1
        for key, item_length in frame_template.items():
            if key == "frame_length":
                continue

            if not isinstance(item_length, int):
                item_length = len(content[key])
            if buffer_position + item_length > frame_length:
                raise OverflowError("Frame data overflow!")
            frame[buffer_position: buffer_position + item_length] = content[key]
            buffer_position += item_length

        return frame

    def deconstruct(self, frame, mode_name=None):

        buffer_position = 1
        # Handle the case where the frame type is not recognized
        #raise ValueError(f"Unknown frame type: {frametype}")
        if mode_name in ["SIGNALLING_ACK"]:
            frametype = FR_TYPE.ARQ_BURST_ACK.value
            frame_template = self.template_list.get(frametype)
            frame = bytes([frametype]) + frame
        else:
            # Extract frametype and get the corresponding template
            frametype = int.from_bytes(frame[:1], "big")
            frame_template = self.template_list.get(frametype)

        extracted_data = {"frame_type": FR_TYPE(frametype).name, "frame_type_int": frametype}

        for key, item_length in frame_template.items():
            if key == "frame_length":
                continue

            # data is always on the last payload slots
            if item_length in ["dynamic"] and key in["data"]:
                print(len(frame))
                data = frame[buffer_position:-2]
                item_length = len(data)
            else:
                data = frame[buffer_position: buffer_position + item_length]

            # Process the data based on the key
            if key in ["origin", "destination"]:
                extracted_data[key] = helpers.bytes_to_callsign(data).decode()

            elif key in ["origin_crc", "destination_crc", "total_crc"]:
                extracted_data[key] = data.hex()

            elif key == "gridsquare":
                extracted_data[key] = helpers.decode_grid(data)

            elif key in ["session_id", "speed_level", 
                            "frames_per_burst", "version",
                            "offset", "total_length", "state", "type", "maximum_bandwidth", "protocol_version"]:
                extracted_data[key] = int.from_bytes(data, 'big')

            elif key in ["snr"]:
                extracted_data[key] = helpers.snr_from_bytes(data)

            elif key == "flag":

                data = int.from_bytes(data, "big")
                extracted_data[key] = {}
                # check for frametype for selecting the correspinding flag dictionary
                if frametype in [FR_TYPE.ARQ_SESSION_OPEN_ACK.value, FR_TYPE.ARQ_SESSION_INFO_ACK.value, FR_TYPE.ARQ_BURST_ACK.value]:
                    flag_dict = self.ARQ_FLAGS
                    for flag in flag_dict:
                        # Update extracted_data with the status of each flag
                        # get_flag returns True or False based on the bit value at the flag's position
                        extracted_data[key][flag] = helpers.get_flag(data, flag, flag_dict)

                if frametype in [FR_TYPE.BEACON.value]:
                    flag_dict = self.BEACON_FLAGS
                    for flag in flag_dict:
                        # Update extracted_data with the status of each flag
                        # get_flag returns True or False based on the bit value at the flag's position
                        extracted_data[key][flag] = helpers.get_flag(data, flag, flag_dict)


            else:
                extracted_data[key] = data

            buffer_position += item_length

        return extracted_data

    def get_bytes_per_frame(self, mode: codec2.FREEDV_MODE) -> int:
        freedv = codec2.open_instance(mode.value)
        bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv) / 8)
        return bytes_per_frame
    
    def get_available_data_payload_for_mode(self, type: FR_TYPE, mode:codec2.FREEDV_MODE):
        whole_frame_length = self.get_bytes_per_frame(mode)
        available = whole_frame_length - 2 # 2Bytes CRC16
        available -= 1 # Frame Type
        for field, length in self.template_list[type.value].items():
            if field != 'frame_length' and isinstance(length, int):
                available -= length
        return available

    def build_ping(self, destination):
        payload = {
            "destination_crc": helpers.get_crc_24(destination),
            "origin_crc": helpers.get_crc_24(self.myfullcall),
            "origin": helpers.callsign_to_bytes(self.myfullcall),
        }
        return self.construct(FR_TYPE.PING, payload)

    def build_ping_ack(self, destination, snr):
        payload = {
            "destination_crc": helpers.get_crc_24(destination),
            "origin_crc": helpers.get_crc_24(self.myfullcall),
            "gridsquare": helpers.encode_grid(self.mygrid),
            "snr": helpers.snr_to_bytes(snr)
        }
        return self.construct(FR_TYPE.PING_ACK, payload)

    def build_cq(self):
        payload = {
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "gridsquare": helpers.encode_grid(self.mygrid)
        }
        return self.construct(FR_TYPE.CQ, payload)

    def build_qrv(self, snr):
        payload = {
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "gridsquare": helpers.encode_grid(self.mygrid),
            "snr": helpers.snr_to_bytes(snr)
        }
        return self.construct(FR_TYPE.QRV, payload)

    def build_beacon(self, flag_away_from_key=False):
        flag = 0b00000000
        if flag_away_from_key:
            flag = helpers.set_flag(flag, 'AWAY_FROM_KEY', True, self.BEACON_FLAGS)

        payload = {
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "gridsquare": helpers.encode_grid(self.mygrid),
            "flag": flag.to_bytes(1, 'big'),

        }
        return self.construct(FR_TYPE.BEACON, payload)

    def build_fec_is_writing(self):
        payload = {
            "origin": helpers.callsign_to_bytes(self.myfullcall),
        }
        return self.construct(FR_TYPE.IS_WRITING, payload)

    def build_fec_wakeup(self, mode):
        mode_int = codec2.freedv_get_mode_value_by_name(mode)

        payload = {
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "mode": bytes([mode_int]),
            "n_bursts": bytes([1]) # n payload bursts,

        }
        return self.construct(FR_TYPE.FEC_WAKEUP, payload)

    def build_fec(self, mode, payload):
        mode_int = codec2.freedv_get_mode_value_by_name(mode)
        payload_per_frame = codec2.get_bytes_per_frame(mode_int) - 2
        fec_payload_length = payload_per_frame - 1
        fec_frame = bytearray(payload_per_frame)
        fec_frame[:1] = bytes([FR_TYPE.FEC.value])
        fec_frame[1:payload_per_frame] = bytes(payload[:fec_payload_length])
        return fec_frame

    def build_test(self, mode):
        mode_int = codec2.freedv_get_mode_value_by_name(mode)
        payload_per_frame = codec2.get_bytes_per_frame(mode_int) - 2
        test_frame = bytearray(payload_per_frame)
        test_frame[:1] = bytes([FR_TYPE.TEST_FRAME.value])
        return test_frame

    def build_arq_session_open(self, destination, session_id, maximum_bandwidth, protocol_version):
        payload = {
            "destination_crc": helpers.get_crc_24(destination),
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "session_id": session_id.to_bytes(1, 'big'),
            "maximum_bandwidth": maximum_bandwidth.to_bytes(2, 'big'),
            "protocol_version": protocol_version.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.ARQ_SESSION_OPEN, payload)

    def build_arq_session_open_ack(self, session_id, destination, version, snr, flag_abort=False):
        flag = 0b00000000
        if flag_abort:
            flag = helpers.set_flag(flag, 'ABORT', True, self.ARQ_FLAGS)

        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "destination_crc": helpers.get_crc_24(destination),
            "version": bytes([version]),
            "snr": helpers.snr_to_bytes(1),
            "flag": flag.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.ARQ_SESSION_OPEN_ACK, payload)
    
    def build_arq_session_info(self, session_id: int, total_length: int, total_crc: bytes, snr, type):
        flag = 0b00000000

        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
            "total_length": total_length.to_bytes(4, 'big'),
            "total_crc": total_crc,
            "snr": helpers.snr_to_bytes(1),
            "flag": flag.to_bytes(1, 'big'),
            "type": type.to_bytes(1, 'big'),

        }
        return self.construct(FR_TYPE.ARQ_SESSION_INFO, payload)

    def build_arq_stop(self, session_id: int):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.ARQ_STOP, payload)

    def build_arq_stop_ack(self, session_id: int):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.ARQ_STOP_ACK, payload)

    def build_arq_session_info_ack(self, session_id, offset, snr, speed_level, frames_per_burst, flag_final=False, flag_abort=False):
        flag = 0b00000000
        if flag_final:
            flag = helpers.set_flag(flag, 'FINAL', True, self.ARQ_FLAGS)
        if flag_abort:
            flag = helpers.set_flag(flag, 'ABORT', True, self.ARQ_FLAGS)

        payload = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "session_id": session_id.to_bytes(1, 'big'),
            "offset": offset.to_bytes(4, 'big'),
            "snr": helpers.snr_to_bytes(1),
            "speed_level": speed_level.to_bytes(1, 'big'),
            "frames_per_burst": frames_per_burst.to_bytes(1, 'big'),
            "flag": flag.to_bytes(1, 'big'),
        }        
        return self.construct(FR_TYPE.ARQ_SESSION_INFO_ACK, payload)

    def build_arq_burst_frame(self, freedv_mode: codec2.FREEDV_MODE, session_id: int, offset: int, data: bytes, speed_level: int):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
            "speed_level": speed_level.to_bytes(1, 'big'),
            "offset": offset.to_bytes(4, 'big'),
            "data": data,
        }
        return self.construct(
            FR_TYPE.ARQ_BURST_FRAME, payload, self.get_bytes_per_frame(freedv_mode)
        )

    def build_arq_burst_ack(self, session_id: bytes, speed_level: int, flag_final=False, flag_checksum=False, flag_abort=False):
        flag = 0b00000000
        if flag_final:
            flag = helpers.set_flag(flag, 'FINAL', True, self.ARQ_FLAGS)

        if flag_checksum:
            flag = helpers.set_flag(flag, 'CHECKSUM', True, self.ARQ_FLAGS)

        if flag_abort:
            flag = helpers.set_flag(flag, 'ABORT', True, self.ARQ_FLAGS)

        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
            "speed_level": speed_level.to_bytes(1, 'big'),
            "flag": flag.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.ARQ_BURST_ACK, payload)
    
    def build_p2p_connection_connect(self, destination, origin, session_id):
        payload = {
            "destination_crc": helpers.get_crc_24(destination),
            "origin": helpers.callsign_to_bytes(origin),
            "session_id": session_id.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.P2P_CONNECTION_CONNECT, payload)
    
    def build_p2p_connection_connect_ack(self, destination, origin, session_id):
        payload = {
            "destination_crc": helpers.get_crc_24(destination),
            "origin": helpers.callsign_to_bytes(origin),
            "session_id": session_id.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.P2P_CONNECTION_CONNECT_ACK, payload)
    
    def build_p2p_connection_heartbeat(self, session_id):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.P2P_CONNECTION_HEARTBEAT, payload)
    
    def build_p2p_connection_heartbeat_ack(self, session_id):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.P2P_CONNECTION_HEARTBEAT_ACK, payload)
    
    def build_p2p_connection_payload(self, freedv_mode: codec2.FREEDV_MODE, session_id: int, sequence_id: int, data: bytes):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
            "sequence_id": sequence_id.to_bytes(1, 'big'),
            "data": data,
        }
        return self.construct(
            FR_TYPE.P2P_CONNECTION_PAYLOAD,
            payload,
            self.get_bytes_per_frame(freedv_mode),
        )
    
    def build_p2p_connection_payload_ack(self, session_id, sequence_id):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
            "sequence_id": sequence_id.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.P2P_CONNECTION_PAYLOAD_ACK, payload)

    def build_p2p_connection_disconnect(self, session_id):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.P2P_CONNECTION_DISCONNECT, payload)

    def build_p2p_connection_disconnect_ack(self, session_id):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.P2P_CONNECTION_DISCONNECT_ACK, payload)
