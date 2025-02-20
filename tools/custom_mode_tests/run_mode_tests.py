"""
AI-Generated FreeDATA Mode Testing Script by DJ2LS using ChatGPT

This script tests different FreeDV modes for their ability to modulate and demodulate data.
It evaluates the following metrics:
- Average audio volume in dB
- Max possible audio volume in dB
- Peak-to-Average Power Ratio (PAPR)
- Frequency spectrum analysis using FFT

The script runs predefined mode pairs in both transmission and reception directions,
and visualizes the results in separate plots.
"""


import sys

sys.path.append('freedata_server')

import ctypes
import threading
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict
from scipy.fftpack import fft
from codec2 import open_instance, api, audio_buffer, FREEDV_MODE, resampler
import modulator
import config
import helpers


class FreeDV:
    def __init__(self, mode, config_file):
        self.mode = mode
        self.config = config.CONFIG(config_file)
        self.modulator = modulator.Modulator(self.config.read())
        self.freedv = open_instance(self.mode.value)

    def demodulate(self, txbuffer):
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
            audiobuffer.pop(nin)
            if nbytes == bytes_per_frame:
                api.freedv_set_sync(self.freedv, 0)
                return True  # Passed

        return False  # Failed

    def compute_audio_metrics(self, txbuffer):
        """Compute Average Volume in dB, Max Possible Volume, PAPR, and FFT for a given signal."""
        # Ensure correct dtype and normalize to float range [-1, 1]
        txbuffer = txbuffer.astype(np.float32) / 32768.0

        avg_volume = np.mean(np.abs(txbuffer))
        avg_volume_db = 20 * np.log10(avg_volume) if avg_volume > 0 else -np.inf
        max_possible_volume_db = 20 * np.log10(1.0)  # Max possible volume when signal is fully utilized
        max_val = np.max(np.abs(txbuffer))

        # Prevent division by zero and ensure reasonable values
        if avg_volume == 0 or max_val == 0:
            papr = 0
        else:
            papr = 10 * np.log10((max_val ** 2) / (avg_volume ** 2))

        # Compute FFT
        fft_values = np.abs(fft(txbuffer))[:len(txbuffer) // 2]
        freqs = np.fft.fftfreq(len(txbuffer), d=1 / 8000)[:len(txbuffer) // 2]  # Assuming 8 kHz sample rate

        return avg_volume_db, max_possible_volume_db, papr, freqs, fft_values

    def write_to_file(self, txbuffer, filename):
        with open(filename, 'wb') as f:
            f.write(txbuffer)


def plot_audio_metrics(avg_volume_per_mode, avg_max_volume_per_mode, avg_papr_per_mode):
    """Plot audio metrics in a separate window."""
    plt.figure(figsize=(10, 5))
    modes = list(avg_volume_per_mode.keys())
    volume_values = list(avg_volume_per_mode.values())
    max_volume_values = list(avg_max_volume_per_mode.values())
    papr_values = list(avg_papr_per_mode.values())

    plt.plot(modes, volume_values, marker='o', linestyle='-', label='Average Volume (dB)')
    plt.plot(modes, max_volume_values, marker='x', linestyle='--', label='Max Possible Volume (dB)', color='blue')
    plt.plot(modes, papr_values, marker='s', linestyle='-', label='Average PAPR (dB)', color='red')
    plt.ylabel('Volume (dB) / PAPR (dB)')
    plt.xlabel('Modes')
    plt.title('Audio Metrics per Mode')
    plt.legend()
    plt.xticks(rotation=45, ha='right')
    plt.pause(0.1)


def plot_fft_per_mode(fft_data):
    """Plot FFTs in a separate window."""
    for mode, (freqs, fft_values) in fft_data.items():
        plt.figure(figsize=(8, 4))
        plt.plot(freqs, fft_values, label=f'FFT {mode}')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Magnitude')
        plt.title(f'FFT of {mode}')
        plt.legend()
    plt.pause(0.1)


def plot_results_summary(results):
    """Plot pass/fail results for each mode pair."""
    mode_pairs = [f"{tx} -> {rx}" for tx, rx, _, _, _, _ in results]
    pass_fail = [1 if result[2] else -1 for result in results]  # Convert True/False to 1/0
    colors = ['green' if r == 1 else 'red' for r in pass_fail]

    plt.figure(figsize=(10, 5))
    plt.bar(mode_pairs, pass_fail, color=colors)
    plt.ylabel('Pass (1) / Fail (0)')
    plt.xlabel('Mode Pairs')
    plt.title('Mode Constellation Pass/Fail Summary')
    plt.xticks(rotation=45, ha='right')
    plt.ylim(-1, 1)  # Ensure bars are properly visible
    plt.show()

def test_freedv_mode_pairs(mode_pairs, config_file='config.ini'):
    results = []
    fft_data = {}
    volume_per_mode = {}
    max_volume_per_mode = {}
    papr_per_mode = {}

    for tx_mode, rx_mode in mode_pairs:
        for test_tx, test_rx in [(tx_mode, rx_mode), (rx_mode, tx_mode)]:
            freedv_tx = FreeDV(test_tx, config_file)
            freedv_rx = FreeDV(test_rx, config_file)

            message = b'ABC'
            txbuffer = freedv_tx.modulator.create_burst(test_tx, 1, 100, message)
            txbuffer = np.frombuffer(txbuffer, dtype=np.int16)

            result = freedv_rx.demodulate(txbuffer)
            avg_volume_db, max_possible_volume_db, papr, freqs, fft_values = freedv_tx.compute_audio_metrics(txbuffer)
            results.append((test_tx.name, test_rx.name, result, avg_volume_db, max_possible_volume_db, papr))
            volume_per_mode[test_tx.name] = avg_volume_db
            max_volume_per_mode[test_tx.name] = max_possible_volume_db
            papr_per_mode[test_tx.name] = papr
            fft_data[test_tx.name] = (freqs, fft_values)

    return results, volume_per_mode, max_volume_per_mode, papr_per_mode, fft_data


if __name__ == "__main__":
    test_mode_pairs = [
        (FREEDV_MODE.datac13, FREEDV_MODE.data_ofdm_200),
        (FREEDV_MODE.datac14, FREEDV_MODE.datac14),
        (FREEDV_MODE.datac4, FREEDV_MODE.data_ofdm_250),
        (FREEDV_MODE.data_ofdm_500, FREEDV_MODE.data_ofdm_500),
        (FREEDV_MODE.datac0, FREEDV_MODE.datac0),
        (FREEDV_MODE.datac3, FREEDV_MODE.datac3),
        (FREEDV_MODE.datac1, FREEDV_MODE.data_ofdm_1700),
        (FREEDV_MODE.data_ofdm_2438, FREEDV_MODE.data_ofdm_2438),
    ]
    results, avg_volume_per_mode, avg_max_volume_per_mode, avg_papr_per_mode, fft_data = test_freedv_mode_pairs(
        test_mode_pairs)
    plot_audio_metrics(avg_volume_per_mode, avg_max_volume_per_mode, avg_papr_per_mode)
    plot_fft_per_mode(fft_data)
    plot_results_summary(results)
