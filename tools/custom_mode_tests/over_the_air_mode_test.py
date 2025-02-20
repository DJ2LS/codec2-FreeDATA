import sys
sys.path.append('freedata_server')

import threading
import ctypes
from codec2 import open_instance, api, audio_buffer, FREEDV_MODE, resampler
import modulator
import config
import helpers
import numpy as np


class FreeDV:
    def __init__(self, mode, config_file):
        self.mode = mode
        self.config = config.CONFIG(config_file)
        self.modulator = modulator.Modulator(self.config.read())
        self.freedv = open_instance(self.mode.value)

    def demodulate(self, txbuffer):
        print(f"DEMOD: {self.mode} {self.mode.value}")
        c2instance = open_instance(self.mode.value)
        bytes_per_frame = int(api.freedv_get_bits_per_modem_frame(c2instance) / 8)
        bytes_out = ctypes.create_string_buffer(bytes_per_frame)
        api.freedv_set_frames_per_burst(c2instance, 1)
        audiobuffer = audio_buffer(len(txbuffer))
        nin = api.freedv_nin(c2instance)
        audiobuffer.push(txbuffer)
        threading.Event().wait(0.01)

        while audiobuffer.nbuffer >= nin:
            nbytes = api.freedv_rawdatarx(self.freedv, bytes_out, audiobuffer.buffer.ctypes)
            rx_status = api.freedv_get_rx_status(self.freedv)
            nin = api.freedv_nin(self.freedv)
            print(f"{rx_status} - {nin}")

            audiobuffer.pop(nin)

            if nbytes == bytes_per_frame:
                print("DECODED!!!!")
                api.freedv_set_sync(self.freedv, 0)

        print("---------------------------------")
        print("ENDED")
        print(nin)
        print(audiobuffer.nbuffer)

    def write_to_file(self, txbuffer, filename):
        with open(filename, 'wb') as f:
            f.write(txbuffer)
        print(f"TX buffer written to {filename}")

# Usage example
if __name__ == "__main__":

    # geht
    MODE = FREEDV_MODE.data_ofdm_250
    RX_MODE = FREEDV_MODE.datac4

    # fail
    #MODE = FREEDV_MODE.datac4
    #RX_MODE = FREEDV_MODE.data_ofdm_250

    FRAMES = 1

    freedv_instance = FreeDV(MODE, 'config.ini')
    freedv_rx_instance = FreeDV(RX_MODE, 'config.ini')

    message = b'ABC'
    txbuffer = freedv_instance.modulator.create_burst(MODE, FRAMES, 100, message)
    freedv_instance.write_to_file(txbuffer, 'ota_audio.raw')
    txbuffer = np.frombuffer(txbuffer, dtype=np.int16)
    freedv_rx_instance.demodulate(txbuffer)


# ./src/freedv_data_raw_rx --framesperburst 2 --testframes DATAC0 - /dev/null --vv
# aplay -f S16_LE ../raw/test_datac1_006.raw
# cat ota_audio.raw | ./freedata_server/lib/codec2/codec2/build_macos/src/freedv_data_raw_rx DATAC0 - /dev/null -vv
"""
Python --> Python --> C



#x = np.frombuffer(txbuffer, dtype=np.int16)
    #resampler = resampler()
    #txbuffer = resampler.resample8_to_48(x)
    #txbuffer = resampler.resample48_to_8(txbuffer)
    #print(txbuffer)




"""