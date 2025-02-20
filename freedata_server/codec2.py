"""
Python interface to the C-language codec2 library.
"""
# -*- coding: utf-8 -*-

# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init

import ctypes
from ctypes import *
import hashlib
import glob
import os
import sys
from enum import Enum
from threading import Lock
import codec2_filter_coeff
import numpy as np
import structlog

log = structlog.get_logger("codec2")


# Enum for codec2 modes
class FREEDV_MODE(Enum):
    """
    Enumeration for codec2 modes and names
    """
    signalling = 19
    signalling_ack = 20
    datac0 = 14
    datac1 = 10
    datac3 = 12
    datac4 = 18
    datac13 = 19
    datac14 = 20
    data_ofdm_200 = 21200
    data_ofdm_250 = 21250
    data_ofdm_500 = 21500
    data_ofdm_1700 = 211700
    data_ofdm_2438 = 2124381
    #data_qam_2438 = 2124382
    #qam16c2 = 22

class FREEDV_MODE_USED_SLOTS(Enum):
    """
    Enumeration for codec2 used slots
    """
    sig0 = [False, False, True, False, False]
    sig1 = [False, False, True, False, False]
    datac0 = [False, False, True, False, False]
    datac1 = [False, True, True, True, False]
    datac3 = [False, False, True, False, False]
    datac4 = [False, False, True, False, False]
    datac13 = [False, False, True, False, False]
    datac14 = [False, False, True, False, False]
    data_ofdm_200 = [False, False, True, False, False]
    data_ofdm_250 = [False, False, True, False, False]
    data_ofdm_500 = [False, False, True, False, False]
    data_ofdm_1700 = [False, True, True, True, False]
    data_ofdm_2438 = [True, True, True, True, True]
    data_qam_2438 = [True, True, True, True, True]
    qam16c2 = [True, True, True, True, True]

# Function for returning the mode value
def freedv_get_mode_value_by_name(mode: str) -> int:
    """
    Get the codec2 mode by entering its string

    Args:
        mode: String representation of the codec2 mode.

    Returns:
        int
    """
    return FREEDV_MODE[mode.lower()].value


# Function for returning the mode name
def freedv_get_mode_name_by_value(mode: int) -> str:
    """
    Get the codec2 mode name as string
    Args:
        mode: Integer value of the codec2 mode.

    Returns:
        string
    """
    return FREEDV_MODE(mode).name

# Get the directory of the current script file
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Use script_dir to construct the paths for file search
if sys.platform == "linux":
    files = glob.glob(os.path.join(script_dir, "**/*libcodec2*"), recursive=True)
    #files.append(os.path.join(script_dir, "libcodec2.so"))
elif sys.platform == "darwin":
    if hasattr(sys, "_MEIPASS"):
        files = glob.glob(os.path.join(getattr(sys, "_MEIPASS"), '**/*libcodec2*'), recursive=True)
    else:
        files = glob.glob(os.path.join(script_dir, "**/*libcodec2*.dylib"), recursive=True)
elif sys.platform in ["win32", "win64"]:
    files = glob.glob(os.path.join(script_dir, "**\\*libcodec2*.dll"), recursive=True)
else:
    files = []
api = None

for file in files:
    try:
        api = ctypes.CDLL(file)
        log.info("[C2 ] Libcodec2 loaded", path=file)
        break
    except OSError as err:
        pass
        #log.info("[C2 ] Error:  Libcodec2 found but not loaded", path=file, e=err)

# Quit module if codec2 cant be loaded
if api is None or "api" not in locals():
    log.critical("[C2 ] Error:  Libcodec2 not loaded - Exiting")
    sys.exit(1)

#log.info("[C2 ] Libcodec2 loaded...", path=file)
# ctypes function init

# api.freedv_set_tuning_range.restype = ctypes.c_int
# api.freedv_set_tuning_range.argype = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float]

api.freedv_open.argype = [ctypes.c_int]  # type: ignore
api.freedv_open.restype = ctypes.c_void_p

api.freedv_set_sync.argype = [ctypes.c_void_p, ctypes.c_int]  # type: ignore
api.freedv_set_sync.restype = ctypes.c_void_p

api.freedv_open_advanced.argtype = [ctypes.c_int, ctypes.c_void_p]  # type: ignore
api.freedv_open_advanced.restype = ctypes.c_void_p

api.freedv_get_bits_per_modem_frame.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_bits_per_modem_frame.restype = ctypes.c_int

api.freedv_get_modem_extended_stats.argtype = [ctypes.c_void_p, ctypes.c_void_p]
api.freedv_get_modem_extended_stats.restype = ctypes.c_int

api.freedv_nin.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_nin.restype = ctypes.c_int

api.freedv_rawdatarx.argtype = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]  # type: ignore
api.freedv_rawdatarx.restype = ctypes.c_int

api.freedv_rawdatatx.argtype = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]  # type: ignore
api.freedv_rawdatatx.restype = ctypes.c_int

api.freedv_rawdatapostambletx.argtype = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]  # type: ignore
api.freedv_rawdatapostambletx.restype = ctypes.c_int

api.freedv_rawdatapreambletx.argtype = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]  # type: ignore
api.freedv_rawdatapreambletx.restype = ctypes.c_int

api.freedv_get_n_max_modem_samples.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_n_max_modem_samples.restype = ctypes.c_int

api.freedv_set_frames_per_burst.argtype = [ctypes.c_void_p, ctypes.c_int]  # type: ignore
api.freedv_set_frames_per_burst.restype = ctypes.c_void_p

api.freedv_get_rx_status.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_rx_status.restype = ctypes.c_int

api.freedv_get_modem_stats.argtype = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]  # type: ignore
api.freedv_get_modem_stats.restype = ctypes.c_int

api.freedv_get_n_tx_postamble_modem_samples.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_n_tx_postamble_modem_samples.restype = ctypes.c_int

api.freedv_get_n_tx_preamble_modem_samples.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_n_tx_preamble_modem_samples.restype = ctypes.c_int

api.freedv_get_n_tx_modem_samples.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_n_tx_modem_samples.restype = ctypes.c_int

api.freedv_get_n_max_modem_samples.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_n_max_modem_samples.restype = ctypes.c_int

api.freedv_ofdm_print_info.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_ofdm_print_info.restype = ctypes.c_void_p

api.FREEDV_FS_8000 = 8000  # type: ignore


# ------- MODEM STATS STRUCTURES
MODEM_STATS_NC_MAX = 50 + 1 * 2
MODEM_STATS_NR_MAX = 320 * 2
MODEM_STATS_ET_MAX = 8
MODEM_STATS_EYE_IND_MAX = 160
MODEM_STATS_NSPEC = 512
MODEM_STATS_MAX_F_HZ = 4000
MODEM_STATS_MAX_F_EST = 4


class MODEMSTATS(ctypes.Structure):
    """Modem statistics structure"""

    _fields_ = [
        ("Nc", ctypes.c_int),
        ("snr_est", ctypes.c_float),
        ("rx_symbols", (ctypes.c_float * MODEM_STATS_NR_MAX) * MODEM_STATS_NC_MAX),
        ("nr", ctypes.c_int),
        ("sync", ctypes.c_int),
        ("foff", ctypes.c_float),
        ("rx_timing", ctypes.c_float),
        ("clock_offset", ctypes.c_float),
        ("sync_metric", ctypes.c_float),
        ("pre", ctypes.c_int),
        ("post", ctypes.c_int),
        ("uw_fails", ctypes.c_int),
        ("rx_eye", (ctypes.c_float * MODEM_STATS_ET_MAX) * MODEM_STATS_EYE_IND_MAX),
        ("neyetr", ctypes.c_int),  # How many eye traces are plotted
        ("neyesamp", ctypes.c_int),  # How many samples in the eye diagram
        ("f_est", (ctypes.c_float * MODEM_STATS_MAX_F_EST)),
        ("fft_buf", (ctypes.c_float * MODEM_STATS_NSPEC * 2)),
        ("fft_cfg", ctypes.c_void_p)
    ]


# Return code flags for freedv_get_rx_status() function
api.FREEDV_RX_TRIAL_SYNC = 0x1  # type: ignore # demodulator has trial sync
api.FREEDV_RX_SYNC = 0x2  # type: ignore # demodulator has sync
api.FREEDV_RX_BITS = 0x4  # type: ignore # data bits have been returned
api.FREEDV_RX_BIT_ERRORS = 0x8  # type: ignore # FEC may not have corrected all bit errors (not all parity checks OK)

api.rx_sync_flags_to_text = [  # type: ignore
    "----",
    "---T",
    "--S-",
    "--ST",
    "-B--",
    "-B-T",
    "-BS-",
    "-BST",
    "E---",
    "E--T",
    "E-S-",
    "E-ST",
    "EB--",
    "EB-T",
    "EBS-",
    "EBST",
]

# Audio buffer ---------------------------------------------------------
class audio_buffer:
    """
    Thread-safe audio buffer, which fits the needs of codec2

    made by David Rowe, VK5DGR
    """

    # A buffer of int16 samples, using a fixed length numpy array self.buffer for storage
    # self.nbuffer is the current number of samples in the buffer
    def __init__(self, size):
        log.debug("[C2 ] Creating audio buffer", size=size)
        self.size = size
        self.buffer = np.zeros(size, dtype=np.int16)
        self.nbuffer = 0
        self.mutex = Lock()

    def push(self, samples):
        """
        Push new data to buffer

        Args:
            samples:

        Returns:
            Nothing
        """
        self.mutex.acquire()
        # Add samples at the end of the buffer
        assert self.nbuffer + len(samples) <= self.size
        self.buffer[self.nbuffer : self.nbuffer + len(samples)] = samples
        self.nbuffer += len(samples)
        self.mutex.release()

    def pop(self, size):
        """
        get data from buffer in size of NIN
        Args:
          size:

        Returns:
            Nothing
        """
        self.mutex.acquire()
        # Remove samples from the start of the buffer
        self.nbuffer -= size
        self.buffer[: self.nbuffer] = self.buffer[size : size + self.nbuffer]
        assert self.nbuffer >= 0
        self.mutex.release()


# Resampler ---------------------------------------------------------

# Oversampling rate
api.FDMDV_OS_48 = 6  # type: ignore
# Number of oversampling taps at 48kHz
api.FDMDV_OS_TAPS_48K = 48  # type: ignore
# Number of oversampling filter taps at 8kHz
api.FDMDV_OS_TAPS_48_8K = api.FDMDV_OS_TAPS_48K // api.FDMDV_OS_48  # type: ignore
api.fdmdv_8_to_48_short.argtype = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]  # type: ignore
api.fdmdv_48_to_8_short.argtype = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]  # type: ignore


class resampler:
    """
    Re-sampler class
    """

    # Re-sample an array of variable length, we just store the filter memories here
    MEM8 = api.FDMDV_OS_TAPS_48_8K
    MEM48 = api.FDMDV_OS_TAPS_48K

    def __init__(self):
        log.debug("[C2 ] Create 48<->8 kHz resampler")
        self.filter_mem8 = np.zeros(self.MEM8, dtype=np.int16)
        self.filter_mem48 = np.zeros(self.MEM48)

    def resample48_to_8(self, in48):
        """
        Audio resampler integration from codec2
        Downsample audio from 48000Hz to 8000Hz
        Args:
            in48: input data as np.int16

        Returns:
            Downsampled 8000Hz data as np.int16
        """
        assert in48.dtype == np.int16
        # Length of input vector must be an integer multiple of api.FDMDV_OS_48
        assert len(in48) % api.FDMDV_OS_48 == 0  # type: ignore

        # Concatenate filter memory and input samples
        in48_mem = np.zeros(self.MEM48 + len(in48), dtype=np.int16)
        in48_mem[: self.MEM48] = self.filter_mem48
        in48_mem[self.MEM48 :] = in48

        # In C: pin48=&in48_mem[MEM48]
        pin48 = ctypes.byref(np.ctypeslib.as_ctypes(in48_mem), 2 * self.MEM48)
        n8 = int(len(in48) / api.FDMDV_OS_48)  # type: ignore
        out8 = np.zeros(n8, dtype=np.int16)
        api.fdmdv_48_to_8_short(out8.ctypes, pin48, n8)  # type: ignore

        # Store memory for next time
        self.filter_mem48 = in48_mem[: self.MEM48]

        return out8

    def resample8_to_48(self, in8):
        """
        Audio resampler integration from codec2
        Re-sample audio from 8000Hz to 48000Hz
        Args:
            in8: input data as np.int16

        Returns:
            48000Hz audio as np.int16
        """
        assert in8.dtype == np.int16

        # Concatenate filter memory and input samples
        in8_mem = np.zeros(self.MEM8 + len(in8), dtype=np.int16)
        in8_mem[: self.MEM8] = self.filter_mem8
        in8_mem[self.MEM8 :] = in8

        # In C: pin8=&in8_mem[MEM8]
        pin8 = ctypes.byref(np.ctypeslib.as_ctypes(in8_mem), 2 * self.MEM8)
        out48 = np.zeros(api.FDMDV_OS_48 * len(in8), dtype=np.int16)  # type: ignore
        api.fdmdv_8_to_48_short(out48.ctypes, pin8, len(in8))  # type: ignore

        # Store memory for next time
        self.filter_mem8 = in8_mem[: self.MEM8]

        return out48

def open_instance(mode: int) -> ctypes.c_void_p:
    data_custom = 21
    if mode in [FREEDV_MODE.data_ofdm_200.value, FREEDV_MODE.data_ofdm_250.value, FREEDV_MODE.data_ofdm_500.value, FREEDV_MODE.data_ofdm_1700.value, FREEDV_MODE.data_ofdm_2438.value]:
    #if mode in [FREEDV_MODE.data_ofdm_500.value, FREEDV_MODE.data_ofdm_2438.value, FREEDV_MODE.data_qam_2438]:
        custom_params = ofdm_configurations[mode]
        return ctypes.cast(
                    api.freedv_open_advanced(
                        data_custom,
                        ctypes.byref(custom_params),
                    ),
                    ctypes.c_void_p,
                )
    else:
        if mode not in [data_custom]:
            return ctypes.cast(api.freedv_open(mode), ctypes.c_void_p)


def get_bytes_per_frame(mode: int) -> int:
    """
    Provide bytes per frame information for accessing from data handler

    :param mode: Codec2 mode to query
    :type mode: int or str
    :return: Bytes per frame of the supplied codec2 data mode
    :rtype: int
    """
    freedv = open_instance(mode)
    # TODO add close session
    # get number of bytes per frame for mode
    return int(api.freedv_get_bits_per_modem_frame(freedv) / 8)


MAX_UW_BITS = 64#192

class OFDM_CONFIG(ctypes.Structure):
    _fields_ = [
        ("tx_centre", ctypes.c_float),  # TX Centre Audio Frequency
        ("rx_centre", ctypes.c_float),  # RX Centre Audio Frequency
        ("fs", ctypes.c_float),  # Sample Frequency
        ("rs", ctypes.c_float),  # Symbol Rate
        ("ts", ctypes.c_float),  # Symbol duration
        ("tcp", ctypes.c_float),  # Cyclic Prefix duration
        ("timing_mx_thresh", ctypes.c_float),  # Threshold for timing metrics
        ("nc", ctypes.c_int),  # Number of carriers
        ("ns", ctypes.c_int),  # Number of Symbol frames
        ("np", ctypes.c_int),  # Number of freedata_server frames per packet
        ("bps", ctypes.c_int),  # Bits per Symbol
        ("txtbits", ctypes.c_int),  # Number of auxiliary data bits
        ("nuwbits", ctypes.c_int),  # Number of unique word bits
        ("bad_uw_errors", ctypes.c_int),  # Threshold for bad unique word detection
        ("ftwindowwidth", ctypes.c_int),  # Filter window width
        ("edge_pilots", ctypes.c_int),  # Edge pilots configuration
        ("state_machine", ctypes.c_char_p),  # Name of sync state machine used
        ("codename", ctypes.c_char_p),  # LDPC codename
        ("tx_uw", ctypes.c_uint8 * MAX_UW_BITS),  # User defined unique word
        ("amp_est_mode", ctypes.c_int),  # Amplitude estimator algorithm mode
        ("tx_bpf_en", ctypes.c_bool),  # TX BPF enable flag
        ("rx_bpf_en", ctypes.c_bool),  # RX BPF enable flag
        ("tx_bpf_proto", ctypes.POINTER(ctypes.c_float)),  # low pass prototype for complex BPF
        ("tx_bpf_proto_n", ctypes.c_int),  # number of taps in low pass prototype
        ("foff_limiter", ctypes.c_bool),  # Frequency offset limiter enable flag
        ("amp_scale", ctypes.c_float),  # Amplitude scale factor
        ("clip_gain1", ctypes.c_float),  # Pre-clipping gain
        ("clip_gain2", ctypes.c_float),  # Post-clipping gain
        ("clip_en", ctypes.c_bool),  # Clipping enable flag
        ("mode", ctypes.c_char * 16),  # OFDM mode in string form
        ("data_mode", ctypes.c_char_p),  # Data mode ("streaming", "burst", etc.)
        ("fmin", ctypes.c_float),  # Minimum frequency for tuning range
        ("fmax", ctypes.c_float),  # Maximum frequency for tuning range

    ]

class FREEDV_ADVANCED(ctypes.Structure):
    """Advanced structure for fsk and ofdm modes"""
    _fields_ = [
        ("interleave_frames", ctypes.c_int),
        ("M", ctypes.c_int),
        ("Rs", ctypes.c_int),
        ("Fs", ctypes.c_int),
        ("first_tone", ctypes.c_int),
        ("tone_spacing", ctypes.c_int),
        ("codename", ctypes.c_char_p),
        ("config", ctypes.POINTER(OFDM_CONFIG))
    ]


api.freedv_open_advanced.argtypes = [ctypes.c_int, ctypes.POINTER(FREEDV_ADVANCED)]
api.freedv_open_advanced.restype = ctypes.c_void_p

def create_default_ofdm_config():

    ofdm_default_config = OFDM_CONFIG(
        tx_centre=1500.0,
        rx_centre=1500.0,
        fs=8000.0,
        rs=62.5,
        ts=0.016,
        tcp=0.006,
        timing_mx_thresh=0.10,
        nc=9,
        ns=5,
        np=29,
        bps=2,
        txtbits=0,
        nuwbits=40,
        bad_uw_errors=10,
        ftwindowwidth=80,
        edge_pilots=False,
        state_machine="data".encode('utf-8'),
        codename="H_1024_2048_4f".encode('utf-8'),
        tx_uw=(c_uint8 * MAX_UW_BITS)(*([0] * MAX_UW_BITS)),
        amp_est_mode=1,
        tx_bpf_en=False,
        rx_bpf_en=False,
        tx_bpf_proto=codec2_filter_coeff.testFilter,
        tx_bpf_proto_n=int(ctypes.sizeof(codec2_filter_coeff.testFilter) / ctypes.sizeof(ctypes.c_float)),
        foff_limiter=False,
        amp_scale=300E3,
        clip_gain1=2.2,
        clip_gain2=0.8,
        clip_en=False,
        mode="CUSTOM".encode('utf-8'),
        data_mode="streaming".encode('utf-8'),
        fmin=-50.0,
        fmax=50.0,
    )

    return FREEDV_ADVANCED(
        interleave_frames = 0,
        M = 2,
        Rs = 100,
        Fs = 8000,
        first_tone = 1000,
        tone_spacing = 200,
        codename = "H_256_512_4".encode("utf-8"),
        config = ctypes.pointer(ofdm_default_config),
    )


def create_tx_uw(nuwbits, uw_sequence):
    """
    Creates a tx_uw ctypes array filled with the uw_sequence up to nuwbits.
    If uw_sequence is shorter than nuwbits, the rest of the array is filled with zeros.

    :param nuwbits: The number of bits for the tx_uw array, should not exceed MAX_UW_BITS.
    :param uw_sequence: List of integers representing the unique word sequence.
    :return: A ctypes array representing the tx_uw.
    """
    # Ensure nuwbits does not exceed MAX_UW_BITS
    if nuwbits > MAX_UW_BITS:
        raise ValueError(f"nuwbits exceeds MAX_UW_BITS: {MAX_UW_BITS}")

    tx_uw_array = (ctypes.c_uint8 * MAX_UW_BITS)(*([0] * MAX_UW_BITS))
    for i in range(min(len(uw_sequence), MAX_UW_BITS)):
        tx_uw_array[i] = uw_sequence[i]
    return tx_uw_array

# ---------------- OFDM 500 Hz Bandwidth ---------------#

# DATAC13 # OFDM 200
data_ofdm_200_config = create_default_ofdm_config()
data_ofdm_200_config.config.contents.ns = 5
data_ofdm_200_config.config.contents.np = 18
data_ofdm_200_config.config.contents.tcp = 0.006
data_ofdm_200_config.config.contents.ts = 0.016
data_ofdm_200_config.config.contents.rs = 1.0 / data_ofdm_200_config.config.contents.ts
data_ofdm_200_config.config.contents.nc = 3
data_ofdm_200_config.config.contents.timing_mx_thresh = 0.45
data_ofdm_200_config.config.contents.bad_uw_errors = 18
data_ofdm_200_config.config.contents.codename = "H_256_512_4".encode('utf-8')
data_ofdm_200_config.config.contents.amp_scale = 2.5*300E3
data_ofdm_200_config.config.contents.nuwbits = 48
data_ofdm_200_config.config.contents.tx_uw = create_tx_uw(data_ofdm_200_config.config.contents.nuwbits, [1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0])
data_ofdm_200_config.config.contents.clip_gain1 = 1.2
data_ofdm_200_config.config.contents.clip_gain2 = 1.0
data_ofdm_200_config.config.contents.tx_bpf_en = False
data_ofdm_200_config.config.contents.tx_bpf_proto = codec2_filter_coeff.generate_filter_coefficients(8000, 400, 101)
data_ofdm_200_config.config.contents.tx_bpf_proto_n = 101 # TODO sizeof(filtP200S400) / sizeof(float);


# DATAC4 # OFDM 250
data_ofdm_250_config = create_default_ofdm_config()
data_ofdm_250_config.config.contents.ns = 5
data_ofdm_250_config.config.contents.np = 47
data_ofdm_250_config.config.contents.tcp = 0.006
data_ofdm_250_config.config.contents.ts = 0.016
data_ofdm_250_config.config.contents.rs = 1.0 / data_ofdm_250_config.config.contents.ts
data_ofdm_250_config.config.contents.nc = 4
data_ofdm_250_config.config.contents.timing_mx_thresh = 0.5
data_ofdm_250_config.config.contents.bad_uw_errors = 12
data_ofdm_250_config.config.contents.codename = "H_1024_2048_4f".encode('utf-8')
data_ofdm_250_config.config.contents.amp_scale = 2*300E3
data_ofdm_250_config.config.contents.nuwbits = 32
data_ofdm_250_config.config.contents.tx_uw = create_tx_uw(data_ofdm_250_config.config.contents.nuwbits, [1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0])
data_ofdm_250_config.config.contents.clip_gain1 = 1.2
data_ofdm_250_config.config.contents.clip_gain2 = 1.0
data_ofdm_250_config.config.contents.tx_bpf_en = True
data_ofdm_250_config.config.contents.tx_bpf_proto = codec2_filter_coeff.generate_filter_coefficients(8000, 400, 101)
data_ofdm_250_config.config.contents.tx_bpf_proto_n = 101 # TODO sizeof(filtP200S400) / sizeof(float);


# OFDM 500
data_ofdm_500_config = create_default_ofdm_config()
data_ofdm_500_config.config.contents.ns = 5
data_ofdm_500_config.config.contents.np = 32
data_ofdm_500_config.config.contents.tcp = 0.006
data_ofdm_500_config.config.contents.ts = 0.016
data_ofdm_500_config.config.contents.rs = 1.0 / data_ofdm_500_config.config.contents.ts
data_ofdm_500_config.config.contents.nc = 8
data_ofdm_500_config.config.contents.timing_mx_thresh = 0.1
data_ofdm_500_config.config.contents.bad_uw_errors = 18
data_ofdm_500_config.config.contents.codename = "H_1024_2048_4f".encode('utf-8')
data_ofdm_500_config.config.contents.amp_scale = 300E3 # 290E3
data_ofdm_500_config.config.contents.nuwbits = 56
data_ofdm_500_config.config.contents.tx_uw = create_tx_uw(data_ofdm_500_config.config.contents.nuwbits, [0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1])
data_ofdm_500_config.config.contents.clip_gain1 = 2.5 # 2.8
data_ofdm_500_config.config.contents.clip_gain2 = 1.0 #0.9
data_ofdm_500_config.config.contents.tx_bpf_en = True
data_ofdm_500_config.config.contents.tx_bpf_proto = codec2_filter_coeff.generate_filter_coefficients(8000, 600, 100)
data_ofdm_500_config.config.contents.tx_bpf_proto_n = 100


# DATAC1 # OFDM1700
data_ofdm_1700_config = create_default_ofdm_config()
data_ofdm_1700_config.config.contents.ns = 5
data_ofdm_1700_config.config.contents.np = 38
data_ofdm_1700_config.config.contents.tcp = 0.006
data_ofdm_1700_config.config.contents.ts = 0.016
data_ofdm_1700_config.config.contents.nc = 27
data_ofdm_1700_config.config.contents.nuwbits = 16
data_ofdm_1700_config.config.contents.timing_mx_thresh = 0.10
data_ofdm_1700_config.config.contents.bad_uw_errors = 6
data_ofdm_1700_config.config.contents.codename = b"H_4096_8192_3d"
data_ofdm_1700_config.config.contents.clip_gain1 = 2.7
data_ofdm_1700_config.config.contents.clip_gain2 = 0.8
data_ofdm_1700_config.config.contents.amp_scale = 145E3
data_ofdm_1700_config.config.contents.tx_bpf_en = False
data_ofdm_1700_config.config.contents.tx_bpf_proto = codec2_filter_coeff.generate_filter_coefficients(8000, 2000, 100)
data_ofdm_1700_config.config.contents.tx_bpf_proto_n = 100
data_ofdm_1700_config.config.contents.tx_uw = create_tx_uw(data_ofdm_1700_config.config.contents.nuwbits, [1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0])


"""
# DATAC3
data_ofdm_500_config = create_default_ofdm_config()
data_ofdm_500_config.config.contents.ns = 5
data_ofdm_500_config.config.contents.np = 29
data_ofdm_500_config.config.contents.tcp = 0.006
data_ofdm_500_config.config.contents.ts = 0.016
data_ofdm_500_config.config.contents.rs = 1.0 / data_ofdm_500_config.config.contents.ts
data_ofdm_500_config.config.contents.nc = 9
data_ofdm_500_config.config.contents.nuwbits = 40
data_ofdm_500_config.config.contents.timing_mx_thresh = 0.10
data_ofdm_500_config.config.contents.bad_uw_errors = 10
data_ofdm_500_config.config.contents.codename = b"H_1024_2048_4f"
data_ofdm_500_config.config.contents.clip_gain1 = 2.2
data_ofdm_500_config.config.contents.clip_gain2 = 0.8
data_ofdm_500_config.config.contents.tx_uw = create_tx_uw(data_ofdm_500_config.config.contents.nuwbits, [1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0])
"""

# ---------------- OFDM 2438 Hz Bandwidth 16200,9720 ---------------#
data_ofdm_2438_config = create_default_ofdm_config()
data_ofdm_2438_config.config.contents.ns = 5
data_ofdm_2438_config.config.contents.np = 52
data_ofdm_2438_config.config.contents.tcp = 0.004
data_ofdm_2438_config.config.contents.ts = 0.016
data_ofdm_2438_config.config.contents.rs = 1.0 / data_ofdm_2438_config.config.contents.ts
data_ofdm_2438_config.config.contents.nc = 39
data_ofdm_2438_config.config.contents.nuwbits = 24
data_ofdm_2438_config.config.contents.timing_mx_thresh = 0.10
data_ofdm_2438_config.config.contents.bad_uw_errors = 8
data_ofdm_2438_config.config.contents.amp_est_mode = 0
data_ofdm_2438_config.config.contents.amp_scale = 106E3
data_ofdm_2438_config.config.contents.codename = "H_16200_9720".encode('utf-8')
data_ofdm_2438_config.config.contents.clip_gain1 = 3.3
data_ofdm_2438_config.config.contents.clip_gain2 = 0.8
data_ofdm_2438_config.config.contents.timing_mx_thresh = 0.10
data_ofdm_2438_config.config.contents.tx_uw = create_tx_uw(data_ofdm_2438_config.config.contents.nuwbits, [1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1])
data_ofdm_2438_config.config.contents.tx_bpf_en = True
data_ofdm_2438_config.config.contents.tx_bpf_proto = codec2_filter_coeff.generate_filter_coefficients(8000, 2500, 100)
data_ofdm_2438_config.config.contents.tx_bpf_proto_n = 100

# ---------------- QAM 2438 Hz Bandwidth ---------------#
"""
data_qam_2438_config = create_default_ofdm_config()
data_qam_2438_config.config.contents.bps = 4
data_qam_2438_config.config.contents.ns = 5
data_qam_2438_config.config.contents.np = 26
data_qam_2438_config.config.contents.tcp = 0.005
data_qam_2438_config.config.contents.ts = 0.018
data_qam_2438_config.config.contents.rs = 1.0 / data_qam_2438_config.config.contents.ts
data_qam_2438_config.config.contents.nc = 39
data_qam_2438_config.config.contents.nuwbits = 162
data_qam_2438_config.config.contents.timing_mx_thresh = 0.10
data_qam_2438_config.config.contents.bad_uw_errors = 50
data_qam_2438_config.config.contents.amp_est_mode = 0
data_qam_2438_config.config.contents.amp_scale = 145E3
data_qam_2438_config.config.contents.codename = b"H_16200_9720"
data_qam_2438_config.config.contents.clip_gain1 = 2.7
data_qam_2438_config.config.contents.clip_gain2 = 0.8
data_qam_2438_config.config.contents.timing_mx_thresh = 0.10
data_qam_2438_config.config.contents.tx_uw = create_tx_uw(162, [1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0])
"""

ofdm_configurations = {
    FREEDV_MODE.data_ofdm_200.value: data_ofdm_200_config,
    FREEDV_MODE.data_ofdm_250.value: data_ofdm_250_config,
    FREEDV_MODE.data_ofdm_500.value: data_ofdm_500_config,
    FREEDV_MODE.data_ofdm_1700.value: data_ofdm_1700_config,
    FREEDV_MODE.data_ofdm_2438.value: data_ofdm_2438_config,
    #FREEDV_MODE.data_qam_2438.value: data_qam_2438_config

}
