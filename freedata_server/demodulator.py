import numpy as np
import codec2
import ctypes
import structlog
import threading
import audio
import itertools

TESTMODE = False

class Demodulator():

    MODE_DICT = {}
    # Iterate over the FREEDV_MODE enum members
    for mode in codec2.FREEDV_MODE:
            MODE_DICT[mode.value] = {
                'decode': False,
                'bytes_per_frame': None,
                'bytes_out': None,
                'audio_buffer': None,
                'nin': None,
                'instance': None,
                'state_buffer': [],
                'name': mode.name.upper(),
                'decoding_thread': None
            }

    def __init__(self, config, audio_rx_q, data_q_rx, states, event_manager, service_queue, fft_queue):
        self.log = structlog.get_logger("Demodulator")
        self.config = config

        self.shutdown_flag = threading.Event()

        self.service_queue = service_queue
        self.AUDIO_FRAMES_PER_BUFFER_RX = 4800
        self.buffer_overflow_counter = [0] * len(codec2.FREEDV_MODE)
        self.is_codec2_traffic_counter = 0
        self.is_codec2_traffic_cooldown = 5

        self.audio_received_queue = audio_rx_q
        self.data_queue_received = data_q_rx

        self.states = states
        self.event_manager = event_manager

        self.fft_queue = fft_queue

        # Audio Stream object
        self.stream = None

        # init codec2 resampler
        self.resampler = codec2.resampler()

        self.init_codec2()
        self.init_tci()

        # enable decoding of signalling modes
        self.MODE_DICT[codec2.FREEDV_MODE.signalling.value]["decode"] = True
        self.MODE_DICT[codec2.FREEDV_MODE.signalling_ack.value]["decode"] = True


    def init_codec2(self):
        # Open codec2 instances
        for mode in codec2.FREEDV_MODE:
            self.init_codec2_mode(mode.value)

    def init_tci(self):
        if self.config['RADIO']['control'] == "tci":
            tci_rx_callback_thread = threading.Thread(
                target=self.tci_rx_callback,
                name="TCI RX CALLBACK THREAD",
                daemon=True,
            )
            tci_rx_callback_thread.start()


    def init_codec2_mode(self, mode):
        """
        Init codec2 and return some important parameters
        """

        # create codec2 instance
        #c2instance = ctypes.cast(
        c2instance = codec2.open_instance(mode)

        # get bytes per frame
        bytes_per_frame = int(
            codec2.api.freedv_get_bits_per_modem_frame(c2instance) / 8
        )
        # create byte out buffer
        bytes_out = ctypes.create_string_buffer(bytes_per_frame)

        # set initial frames per burst
        codec2.api.freedv_set_frames_per_burst(c2instance, 1)

        # init audio buffer
        audio_buffer = codec2.audio_buffer(2 * self.AUDIO_FRAMES_PER_BUFFER_RX)

        # get initial nin
        nin = codec2.api.freedv_nin(c2instance)

        # Additional Datac0-specific information - these are not referenced anywhere else.
        # self.signalling_datac0_payload_per_frame = self.signalling_datac0_bytes_per_frame - 2
        # self.signalling_datac0_n_nom_modem_samples = codec2.api.freedv_get_n_nom_modem_samples(
        #     self.signalling_datac0_freedv
        # )
        # self.signalling_datac0_n_tx_modem_samples = codec2.api.freedv_get_n_tx_modem_samples(
        #     self.signalling_datac0_freedv
        # )
        # self.signalling_datac0_n_tx_preamble_modem_samples = (
        #     codec2.api.freedv_get_n_tx_preamble_modem_samples(self.signalling_datac0_freedv)
        # )
        # self.signalling_datac0_n_tx_postamble_modem_samples = (
        #     codec2.api.freedv_get_n_tx_postamble_modem_samples(self.signalling_datac0_freedv)
        # )

        self.MODE_DICT[mode]["instance"] = c2instance
        self.MODE_DICT[mode]["bytes_per_frame"] = bytes_per_frame
        self.MODE_DICT[mode]["bytes_out"] = bytes_out
        self.MODE_DICT[mode]["audio_buffer"] = audio_buffer
        self.MODE_DICT[mode]["nin"] = nin

    def start(self, stream):
        self.stream = stream

        for mode in self.MODE_DICT:
            # Start decoder threads
            self.MODE_DICT[mode]['decoding_thread'] = threading.Thread(
                target=self.demodulate_audio,args=[mode], name=self.MODE_DICT[mode]['name'], daemon=True
            )
            self.MODE_DICT[mode]['decoding_thread'].start()

    def get_frequency_offset(self, freedv: ctypes.c_void_p) -> float:
        """
        Ask codec2 for the calculated (audio) frequency offset of the received signal.

        :param freedv: codec2 instance to query
        :type freedv: ctypes.c_void_p
        :return: Offset of audio frequency in Hz
        :rtype: float
        """
        modemStats = codec2.MODEMSTATS()
        codec2.api.freedv_get_modem_extended_stats(freedv, ctypes.byref(modemStats))
        offset = round(modemStats.foff) * (-1)
        return offset

    def demodulate_audio(self, mode) -> int:
        """
        De-modulate supplied audio stream with supplied codec2 instance.
        Decoded audio is placed into `bytes_out`.
        """

        audiobuffer = self.MODE_DICT[mode]["audio_buffer"]
        nin = self.MODE_DICT[mode]["nin"]
        freedv = self.MODE_DICT[mode]["instance"]
        bytes_out = self.MODE_DICT[mode]["bytes_out"]
        bytes_per_frame= self.MODE_DICT[mode]["bytes_per_frame"]
        state_buffer = self.MODE_DICT[mode]["state_buffer"]
        mode_name = self.MODE_DICT[mode]["name"]
        try:
            while self.stream and self.stream.active and not self.shutdown_flag.is_set():
                threading.Event().wait(0.01)
                if audiobuffer.nbuffer >= nin and not self.shutdown_flag.is_set():
                    # demodulate audio
                    nbytes = codec2.api.freedv_rawdatarx(
                        freedv, bytes_out, audiobuffer.buffer.ctypes
                    )
                    # get current freedata_server states and write to list
                    # 1 trial
                    # 2 sync
                    # 3 trial sync
                    # 6 decoded
                    # 10 error decoding == NACK
                    rx_status = codec2.api.freedv_get_rx_status(freedv)

                    if rx_status not in [0]:
                        self.is_codec2_traffic_counter = self.is_codec2_traffic_cooldown
                        self.log.debug(
                            "[MDM] [demod_audio] freedata_server state", mode=mode_name, rx_status=rx_status,
                            sync_flag=codec2.api.rx_sync_flags_to_text[rx_status]
                        )

                    # decrement codec traffic counter for making state smoother
                    if self.is_codec2_traffic_counter > 0:
                        self.is_codec2_traffic_counter -= 1
                        self.states.set_channel_busy_condition_codec2(True)
                    else:
                        self.states.set_channel_busy_condition_codec2(False)
                    if rx_status == 10:
                        state_buffer.append(rx_status)

                    audiobuffer.pop(nin)
                    nin = codec2.api.freedv_nin(freedv)
                    if nbytes == bytes_per_frame:
                        self.log.debug(
                            "[MDM] [demod_audio] Pushing received data to received_queue", nbytes=nbytes, mode_name=mode_name
                        )
                        snr = self.calculate_snr(freedv)
                        self.get_scatter(freedv)

                        item = {
                            'payload': bytes_out,
                            'freedv': freedv,
                            'bytes_per_frame': bytes_per_frame,
                            'snr': snr,
                            'frequency_offset': self.get_frequency_offset(freedv),
                            'mode_name': mode_name
                        }

                        self.data_queue_received.put(item)


                        state_buffer = []
        except Exception as e:
            error_message = str(e)
            # we expect this error when shutdown
            if error_message in ["PortAudio not initialized [PaErrorCode -10000]", "Invalid stream pointer [PaErrorCode -9988]"]:
                return
            else:
                self.log.warning(
                    "[MDM] [demod_audio] demod loop ended", mode=mode_name, e=e
                )
                audio.sd._terminate()

    def tci_rx_callback(self) -> None:
        """
        Callback for TCI RX

        data_in48k must be filled with 48000Hz audio raw data

        """

        while True and not self.shutdown_flag.is_set():

            audio_48k = self.audio_received_queue.get()
            audio_48k = np.frombuffer(audio_48k, dtype=np.int16)

            audio.calculate_fft(audio_48k, self.fft_queue, self.states)

            length_audio_48k = len(audio_48k)
            index = 0
            for mode in self.MODE_DICT:
                mode_data = self.MODE_DICT[mode]
                audiobuffer = mode_data['audio_buffer']
                decode = mode_data['decode']
                index += 1
                if audiobuffer:
                    if (audiobuffer.nbuffer + length_audio_48k) > audiobuffer.size:
                        self.buffer_overflow_counter[index] += 1
                        self.event_manager.send_buffer_overflow(self.buffer_overflow_counter)
                    elif decode:
                        audiobuffer.push(audio_48k)

    def set_frames_per_burst(self, frames_per_burst: int) -> None:
        """
        Configure codec2 to send the configured number of frames per burst.

        :param frames_per_burst: Number of frames per burst requested
        :type frames_per_burst: int
        """
        # Limit frames per burst to acceptable values
        frames_per_burst = min(frames_per_burst, 1)
        frames_per_burst = max(frames_per_burst, 5)

        # FIXME
        frames_per_burst = 1

        codec2.api.freedv_set_frames_per_burst(self.dat0_datac1_freedv, frames_per_burst)
        codec2.api.freedv_set_frames_per_burst(self.dat0_datac3_freedv, frames_per_burst)
        codec2.api.freedv_set_frames_per_burst(self.dat0_datac4_freedv, frames_per_burst)

    def calculate_snr(self, freedv: ctypes.c_void_p) -> float:
        """
        Ask codec2 for data about the received signal and calculate
        the signal-to-noise ratio.

        :param freedv: codec2 instance to query
        :type freedv: ctypes.c_void_p
        :return: Signal-to-noise ratio of the decoded data
        :rtype: float
        """
        try:
            modem_stats_snr = ctypes.c_float()
            modem_stats_sync = ctypes.c_int()

            codec2.api.freedv_get_modem_stats(
                freedv, ctypes.byref(modem_stats_sync), ctypes.byref(modem_stats_snr)
            )
            modem_stats_snr = modem_stats_snr.value
            modem_stats_sync = modem_stats_sync.value

            snr = round(modem_stats_snr, 1)
            self.log.info("[MDM] calculate_snr: ", snr=snr)
            # snr = np.clip(
            #    snr, -127, 127
            # )  # limit to max value of -128/128 as a possible fix of #188
            return int(snr)
        except Exception as err:
            self.log.error(f"[MDM] calculate_snr: Exception: {err}")
            return 0

    def get_scatter(self, freedv: ctypes.c_void_p) -> None:
        """
        Ask codec2 for data about the received signal and calculate the scatter plot.

        :param freedv: codec2 instance to query
        :type freedv: ctypes.c_void_p
        """
       
        modemStats = codec2.MODEMSTATS()
        ctypes.cast(
            codec2.api.freedv_get_modem_extended_stats(freedv, ctypes.byref(modemStats)),
            ctypes.c_void_p,
        )

        scatterdata = []
        # original function before itertool
        # for i in range(codec2.MODEM_STATS_NC_MAX):
        #    for j in range(1, codec2.MODEM_STATS_NR_MAX, 2):
        #        # print(f"{modemStats.rx_symbols[i][j]} - {modemStats.rx_symbols[i][j]}")
        #        xsymbols = round(modemStats.rx_symbols[i][j - 1] // 1000)
        #        ysymbols = round(modemStats.rx_symbols[i][j] // 1000)
        #        if xsymbols != 0.0 and ysymbols != 0.0:
        #            scatterdata.append({"x": str(xsymbols), "y": str(ysymbols)})

        for i, j in itertools.product(range(codec2.MODEM_STATS_NC_MAX), range(1, codec2.MODEM_STATS_NR_MAX, 2)):
            # print(f"{modemStats.rx_symbols[i][j]} - {modemStats.rx_symbols[i][j]}")
            xsymbols = round(modemStats.rx_symbols[i][j - 1] // 1000)
            ysymbols = round(modemStats.rx_symbols[i][j] // 1000)
            if xsymbols != 0.0 and ysymbols != 0.0:
                scatterdata.append({"x": str(xsymbols), "y": str(ysymbols)})

        # Send all the data if we have too-few samples, otherwise send a sampling
        if 150 > len(scatterdata) > 0:
            self.event_manager.send_scatter_change(scatterdata)

        else:
            # only take every tenth data point
            self.event_manager.send_scatter_change(scatterdata[::10])

    def reset_data_sync(self) -> None:
        """
        reset sync state for modes

        :param frames_per_burst: Number of frames per burst requested
        :type frames_per_burst: int
        """
        for mode in self.MODE_DICT:
            codec2.api.freedv_set_sync(self.MODE_DICT[mode]["instance"], 0)

    def set_decode_mode(self, modes_to_decode=None, is_arq_irs=False, is_p2p_connection=False):
        # Reset all modes to not decode
        for m in self.MODE_DICT:
            self.MODE_DICT[m]["decode"] = False

        # signalling is always true
        self.MODE_DICT[codec2.FREEDV_MODE.signalling.value]["decode"] = True
        # we only need to decode signalling ack as ISS or within P2P Connection
        if is_arq_irs and not is_p2p_connection:
            self.MODE_DICT[codec2.FREEDV_MODE.signalling_ack.value]["decode"] = False
        else:
            self.MODE_DICT[codec2.FREEDV_MODE.signalling_ack.value]["decode"] = True


        # lowest speed level is always true
        # TODO DO we need this for all states? we only need this on IRS and P2P Connection
        self.MODE_DICT[codec2.FREEDV_MODE.datac4.value]["decode"] = True

        # Enable specified modes
        if modes_to_decode:
            for mode, decode in modes_to_decode.items():
                if mode in self.MODE_DICT:
                    self.MODE_DICT[mode]["decode"] = decode

    def shutdown(self):
        print("shutting down demodulators...")
        self.shutdown_flag.set()
        for mode in self.MODE_DICT:
            self.MODE_DICT[mode]['decoding_thread'].join(3)