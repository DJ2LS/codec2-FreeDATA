import ctypes
import codec2
import structlog


class Modulator:
    log = structlog.get_logger("RF")

    def __init__(self, config):
        self.config = config
        self.tx_delay = config['MODEM']['tx_delay']
        self.modem_sample_rate = codec2.api.FREEDV_FS_8000

        # Initialize codec2, rig control, and data threads
        self.init_codec2()

    def init_codec2(self):
        # Open codec2 instances

        # INIT TX MODES - here we need all modes.
        self.freedv_datac0_tx = codec2.open_instance(codec2.FREEDV_MODE.datac0.value)
        self.freedv_datac1_tx = codec2.open_instance(codec2.FREEDV_MODE.datac1.value)
        self.freedv_datac3_tx = codec2.open_instance(codec2.FREEDV_MODE.datac3.value)
        self.freedv_datac4_tx = codec2.open_instance(codec2.FREEDV_MODE.datac4.value)
        self.freedv_datac13_tx = codec2.open_instance(codec2.FREEDV_MODE.datac13.value)
        self.freedv_datac14_tx = codec2.open_instance(codec2.FREEDV_MODE.datac14.value)
        self.data_ofdm_200_tx = codec2.open_instance(codec2.FREEDV_MODE.data_ofdm_200.value)
        self.data_ofdm_250_tx = codec2.open_instance(codec2.FREEDV_MODE.data_ofdm_250.value)
        self.data_ofdm_500_tx = codec2.open_instance(codec2.FREEDV_MODE.data_ofdm_500.value)
        self.data_ofdm_1700_tx = codec2.open_instance(codec2.FREEDV_MODE.data_ofdm_1700.value)
        self.data_ofdm_2438_tx = codec2.open_instance(codec2.FREEDV_MODE.data_ofdm_2438.value)
        #self.freedv_qam16c2_tx = codec2.open_instance(codec2.FREEDV_MODE.qam16c2.value)
        #self.data_qam_2438_tx = codec2.open_instance(codec2.FREEDV_MODE.data_qam_2438.value)

    def transmit_add_preamble(self, buffer, freedv):
        # Init buffer for preample
        n_tx_preamble_modem_samples = codec2.api.freedv_get_n_tx_preamble_modem_samples(
            freedv
        )
        mod_out_preamble = ctypes.create_string_buffer(n_tx_preamble_modem_samples * 2)

        # Write preamble to txbuffer
        codec2.api.freedv_rawdatapreambletx(freedv, mod_out_preamble)
        buffer += bytes(mod_out_preamble)
        return buffer

    def transmit_add_postamble(self, buffer, freedv):
        # Init buffer for postamble
        n_tx_postamble_modem_samples = (
            codec2.api.freedv_get_n_tx_postamble_modem_samples(freedv)
        )
        mod_out_postamble = ctypes.create_string_buffer(
            n_tx_postamble_modem_samples * 2
        )
        # Write postamble to txbuffer
        codec2.api.freedv_rawdatapostambletx(freedv, mod_out_postamble)
        # Append postamble to txbuffer
        buffer += bytes(mod_out_postamble)
        return buffer

    def transmit_add_silence(self, buffer, duration):
        data_delay = int(self.modem_sample_rate * (duration / 1000))  # type: ignore
        mod_out_silence = ctypes.create_string_buffer(data_delay * 2)
        buffer += bytes(mod_out_silence)
        return buffer

    def transmit_create_frame(self, txbuffer, freedv, frame):
        # Get number of bytes per frame for mode
        bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv) / 8)
        payload_bytes_per_frame = bytes_per_frame - 2
        #print(payload_bytes_per_frame)
        # Init buffer for data
        n_tx_modem_samples = codec2.api.freedv_get_n_tx_modem_samples(freedv)
        mod_out = ctypes.create_string_buffer(n_tx_modem_samples * 2)

        # Create buffer for data
        # Use this if CRC16 checksum is required (DATAc1-3)
        buffer = bytearray(payload_bytes_per_frame)
        # Set buffersize to length of data which will be sent
        buffer[: len(frame)] = frame  # type: ignore

        # Create crc for data frame -
        #   Use the crc function shipped with codec2
        #   to avoid CRC algorithm incompatibilities
        # Generate CRC16
        crc = ctypes.c_ushort(
            codec2.api.freedv_gen_crc16(bytes(buffer), payload_bytes_per_frame)
        )
        # Convert crc to 2-byte (16-bit) hex string
        crc = crc.value.to_bytes(2, byteorder="big")
        # Append CRC to data buffer
        buffer += crc
        assert (bytes_per_frame == len(buffer))
        data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
        # modulate DATA and save it into mod_out pointer
        codec2.api.freedv_rawdatatx(freedv, mod_out, data)
        txbuffer += bytes(mod_out)
        return txbuffer

    def create_burst(
            self, mode, repeats: int, repeat_delay: int, frames: bytearray
    ) -> bool:
        """

        Args:
          mode:
          repeats:
          repeat_delay:
          frames:

        """



        # get freedv instance by mode
        mode_transition = {
            codec2.FREEDV_MODE.signalling_ack: self.freedv_datac14_tx,
            codec2.FREEDV_MODE.signalling: self.freedv_datac13_tx,
            codec2.FREEDV_MODE.datac0: self.freedv_datac0_tx,
            codec2.FREEDV_MODE.datac1: self.freedv_datac1_tx,
            codec2.FREEDV_MODE.datac3: self.freedv_datac3_tx,
            codec2.FREEDV_MODE.datac4: self.freedv_datac4_tx,
            codec2.FREEDV_MODE.datac13: self.freedv_datac13_tx,
            codec2.FREEDV_MODE.datac14: self.freedv_datac14_tx,
            codec2.FREEDV_MODE.data_ofdm_200: self.data_ofdm_200_tx,
            codec2.FREEDV_MODE.data_ofdm_250: self.data_ofdm_250_tx,
            codec2.FREEDV_MODE.data_ofdm_500: self.data_ofdm_500_tx,
            codec2.FREEDV_MODE.data_ofdm_1700: self.data_ofdm_1700_tx,
            codec2.FREEDV_MODE.data_ofdm_2438: self.data_ofdm_2438_tx,
            #codec2.FREEDV_MODE.qam16c2: self.freedv_qam16c2_tx,
            #codec2.FREEDV_MODE.data_qam_2438: self.freedv_data_qam_2438_tx,
        }
        if mode in mode_transition:
            freedv = mode_transition[mode]
        else:
            print("wrong mode.................")
            print(mode)
            #return False


        # Open codec2 instance
        self.MODE = mode
        self.log.debug(
            "[MDM] TRANSMIT", mode=self.MODE.name, delay=self.tx_delay
        )

        txbuffer = bytes()


        # Add empty data to handle ptt toggle time
        if self.tx_delay > 0:
            txbuffer = self.transmit_add_silence(txbuffer, self.tx_delay)

        if not isinstance(frames, list): frames = [frames]
        for _ in range(repeats):

            # Create modulation for all frames in the list
            for frame in frames:
                txbuffer = self.transmit_add_preamble(txbuffer, freedv)
                txbuffer = self.transmit_create_frame(txbuffer, freedv, frame)
                txbuffer = self.transmit_add_postamble(txbuffer, freedv)

            # Add delay to end of frames
            txbuffer = self.transmit_add_silence(txbuffer, repeat_delay)

        return txbuffer

