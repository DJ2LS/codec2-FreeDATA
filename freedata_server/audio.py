"""
Gather information about audio devices.
"""
import multiprocessing
import sounddevice as sd
import structlog
import numpy as np
import queue
import helpers

log = structlog.get_logger("audio")


def get_audio_devices():
    """
    return list of input and output audio devices in own process to avoid crashes of portaudio on raspberry pi

    also uses a process data manager
    """
    # we need to run this on Windows for multiprocessing support
    # multiprocessing.freeze_support()
    # multiprocessing.get_context("spawn")

    # we need to reset and initialize sounddevice before running the multiprocessing part.
    # If we are not doing this at this early point, not all devices will be displayed
    #sd._terminate()
    #sd._initialize()

    # log.debug("[AUD] get_audio_devices")
    with multiprocessing.Manager() as manager:
        proxy_input_devices = manager.list()
        proxy_output_devices = manager.list()
        # print(multiprocessing.get_start_method())
        proc = multiprocessing.Process(
            target=fetch_audio_devices, args=(proxy_input_devices, proxy_output_devices)
        )
        proc.start()
        proc.join(3)

        # additional logging for audio devices
        # log.debug("[AUD] get_audio_devices: input_devices:", list=f"{proxy_input_devices}")
        # log.debug("[AUD] get_audio_devices: output_devices:", list=f"{proxy_output_devices}")
        return list(proxy_input_devices), list(proxy_output_devices)


def device_crc(device) -> str:
    crc_hwid = helpers.get_crc_16(bytes(f"{device['name']}.{device['hostapi']}", encoding="utf-8"))
    crc_hwid = crc_hwid.hex()
    return crc_hwid

def fetch_audio_devices(input_devices, output_devices):
    """
    get audio devices from portaudio

    Args:
      input_devices: proxy variable for input devices
      output_devices: proxy variable for output devices

    Returns:

    """
    devices = sd.query_devices(device=None, kind=None)

    for index, device in enumerate(devices):
        # Use a try/except block because Windows doesn't have an audio device range
        try:
            name = device["name"]
            # Ignore some Flex Radio devices to make device selection simpler
            if name.startswith("DAX RESERVED") or name.startswith("DAX IQ"):
                continue

            max_output_channels = device["max_output_channels"]
            max_input_channels = device["max_input_channels"]

        except KeyError:
            continue
        except Exception as err:
            print(err)
            max_input_channels = 0
            max_output_channels = 0

        if max_input_channels > 0:
            hostapi_name = sd.query_hostapis(device['hostapi'])['name']

            new_input_device = {"id": device_crc(device), 
                                "name": device['name'], 
                                "api": hostapi_name,
                                "native_index":index}
            # check if device not in device list
            if new_input_device not in input_devices:
                input_devices.append(new_input_device)

        if max_output_channels > 0:
            hostapi_name = sd.query_hostapis(device['hostapi'])['name']
            new_output_device = {"id": device_crc(device), 
                                 "name": device['name'], 
                                 "api": hostapi_name,
                                 "native_index":index}
            # check if device not in device list
            if new_output_device not in output_devices:
                output_devices.append(new_output_device)

    return input_devices, output_devices


# FreeData uses the crc as id inside the configuration
# SD lib uses a numerical id which is essentially an 
# index of the device within the list
# returns (id, name)
def get_device_index_from_crc(crc, isInput: bool):
    try:
        in_devices = []
        out_devices = []

        fetch_audio_devices(in_devices, out_devices)

        if isInput:
            detected_devices = in_devices
        else:
            detected_devices = out_devices

        for i, dev in enumerate(detected_devices):
            if dev['id'] == crc:
                return (dev['native_index'], dev['name'])

    except Exception as e:
        log.warning(f"Audio device {crc} not detected ", devices=detected_devices, isInput=isInput)
        return [None, None]

def test_audio_devices(input_id: str, output_id: str) -> list:
    test_result = [False, False]
    try:
        result = get_device_index_from_crc(input_id, True)
        if result is None:
            # in_dev_index, in_dev_name = None, None
            raise ValueError(f"[Audio-Test] Invalid input device index {input_id}.")
        else:
            in_dev_index, in_dev_name = result
            sd.check_input_settings(
                device=in_dev_index,
                channels=1,
                dtype="int16",
                samplerate=48000,
            )
            test_result[0] = True
    except (sd.PortAudioError, ValueError) as e:
        log.warning(f"[Audio-Test] Input device error ({input_id}):", e=e)
        test_result[0] = False
    try:
        result = get_device_index_from_crc(output_id, False)
        if result is None:
            # out_dev_index, out_dev_name = None, None
            raise ValueError(f"[Audio-Test] Invalid output device index {output_id}.")
        else:
            out_dev_index, out_dev_name = result
            sd.check_output_settings(
                device=out_dev_index,
                channels=1,
                dtype="int16",
                samplerate=48000,
            )
            test_result[1] = True


    except (sd.PortAudioError, ValueError) as e:
        log.warning(f"[Audio-Test] Output device error ({output_id}):", e=e)
        test_result[1] = False

    sd._terminate()
    sd._initialize()
    return test_result

def set_audio_volume(datalist: np.ndarray, dB: float) -> np.ndarray:
    """
    Scale values for the provided audio samples by dB.

    :param datalist: Audio samples to scale
    :type datalist: np.ndarray
    :param dB: Decibels to scale samples, constrained to the range [-50, 50]
    :type dB: float
    :return: Scaled audio samples
    :rtype: np.ndarray
    """
    try:
        dB = float(dB)
    except ValueError as e:
        print(f"[MDM] Changing audio volume failed with error: {e}")
        dB = 0.0  # 0 dB means no change

    # Clip dB value to the range [-50, 50]
    dB = np.clip(dB, -30, 20)

    # Ensure datalist is an np.ndarray
    if not isinstance(datalist, np.ndarray):
        print("[MDM] Invalid data type for datalist. Expected np.ndarray.")
        return datalist

    # Convert dB to linear scale
    scale_factor = 10 ** (dB / 20)

    # Scale samples
    scaled_data = datalist * scale_factor

    # Clip values to int16 range and convert data type
    return np.clip(scaled_data, -32768, 32767).astype(np.int16)


def normalize_audio(datalist: np.ndarray) -> np.ndarray:
    """
    Normalize the audio samples so the loudest value reaches 95% of the maximum possible value for np.int16
    :param datalist: Audio samples to normalize
    :type datalist: np.ndarray
    :return: Normalized audio samples, clipped to the range of int16
    :rtype: np.ndarray
    """
    if not isinstance(datalist, np.ndarray):
        print("[MDM] Invalid datalist type. Expected np.ndarray.")
        return datalist

    # Ensure datalist is not empty
    if datalist.size == 0:
        print("[MDM] Datalist is empty. Returning unmodified.")
        return datalist

    # Find the maximum absolute value in the data
    max_value = np.max(np.abs(datalist))

    # If max_value is 0, return the datalist (avoid division by zero)
    if max_value == 0:
        print("[MDM] Max value is zero. Cannot normalize. Returning unmodified.")
        return datalist

    # Define the target max value as 95% of the maximum for np.int16
    target_max_value = int(32767 * 0.95)

    # Compute the normalization factor
    normalization_factor = target_max_value / max_value

    # Normalize the audio data
    normalized_data = datalist * normalization_factor

    # Clip to the int16 range and cast
    normalized_data = np.clip(normalized_data, -32768, 32767).astype(np.int16)

    # Debug information: normalization factor, loudest value before, and after normalization
    loudest_before = max_value
    loudest_after = np.max(np.abs(normalized_data))
    print(f"[AUDIO] Normalization factor: {normalization_factor:.6f}, Loudest before: {loudest_before}, Loudest after: {loudest_after}")

    return normalized_data



RMS_COUNTER = 0
CHANNEL_BUSY_DELAY = 0
SLOT_DELAY = [0, 0, 0, 0, 0]


def prepare_data_for_fft(data, target_length_samples=400):
    """
    Prepare data array for FFT by padding if necessary to match the target length.
    Center the data if it's shorter than the target length.

    Parameters:
    - data: numpy array of np.int16, representing the input data.
    - target_length_samples: int, the target length of the data in samples.

    Returns:
    - numpy array of np.int16, padded and/or centered if necessary.
    """
    # Calculate the current length in samples
    current_length_samples = data.size

    # Check if padding is needed
    if current_length_samples < target_length_samples:
        # Calculate total padding needed
        total_pad_length = target_length_samples - current_length_samples
        # Calculate padding on each side
        pad_before = total_pad_length // 2
        pad_after = total_pad_length - pad_before
        # Pad the data to center it
        data_padded = np.pad(data, (pad_before, pad_after), 'constant', constant_values=(0,))
        return data_padded
    else:
        # No padding needed, return original data
        return data

def calculate_fft(data, fft_queue, states) -> None:
    """
    Calculate an average signal strength of the channel to assess
    whether the channel is "busy."
    """
    # Initialize dbfs counter
    # rms_counter = 0

    # https://gist.github.com/ZWMiller/53232427efc5088007cab6feee7c6e4c
    # Fast Fourier Transform, 10*log10(abs) is to scale it to dB
    # and make sure it's not imaginary

    global RMS_COUNTER, CHANNEL_BUSY_DELAY

    try:
        data = prepare_data_for_fft(data, target_length_samples=800)
        fftarray = np.fft.rfft(data)

        # Set value 0 to 1 to avoid division by zero
        fftarray[fftarray == 0] = 1
        dfft = 10.0 * np.log10(abs(fftarray))

        # get average of dfft
        avg = np.mean(dfft)

        # Detect signals which are higher than the
        # average + 10 (+10 smoothes the output).
        # Data higher than the average must be a signal.
        # Therefore we are setting it to 100 so it will be highlighted
        # Have to do this when we are not transmitting so our
        # own sending data will not affect this too much
        if not states.isTransmitting():
            dfft[dfft > avg + 15] = 100

            # Calculate audio dbfs
            # https://stackoverflow.com/a/9763652
            # calculate dbfs every 50 cycles for reducing CPU load
            RMS_COUNTER += 1
            if RMS_COUNTER > 5:
                d = np.frombuffer(data, np.int16).astype(np.float32)
                # calculate RMS and then dBFS
                # https://dsp.stackexchange.com/questions/8785/how-to-compute-dbfs
                # try except for avoiding runtime errors by division/0
                try:
                    rms = int(np.sqrt(np.max(d ** 2)))
                    if rms == 0:
                        raise ZeroDivisionError
                    audio_dbfs = 20 * np.log10(rms / 32768)
                    states.set("audio_dbfs", audio_dbfs)
                except Exception as e:
                    states.set("audio_dbfs", -100)

                RMS_COUNTER = 0

        # Convert data to int to decrease size
        dfft = dfft.astype(int)

        # Create list of dfft
        dfftlist = dfft.tolist()

        # Reduce area where the busy detection is enabled
        # We want to have this in correlation with mode bandwidth
        # TODO This is not correctly and needs to be checked for correct maths
        # dfftlist[0:1] = 10,15Hz
        # Bandwidth[Hz] / 10,15
        # narrowband = 563Hz = 56
        # wideband = 1700Hz = 167
        # 1500Hz = 148
        # 2700Hz = 266
        # 3200Hz = 315
        # Initialize slot delay counters
        DELAY_INCREMENT = 2
        MAX_DELAY = 200

        # Main logic
        slot = 0
        slot1 = [0, 65]
        slot2 = [65, 120]
        slot3 = [120, 176]
        slot4 = [176, 231]
        slot5 = [231, len(dfftlist)]
        slotbusy = [False, False, False, False, False]

        # Set to true if we should increment delay count; else false to decrement
        addDelay = False

        for range in [slot1, slot2, slot3, slot4, slot5]:
            range_start = range[0]
            range_end = range[1]
            # define the area, we are detecting busy state
            slotdfft = dfft[range_start:range_end]
            # Check for signals higher than average by checking for "100"
            # If we have a signal, increment our channel_busy delay counter
            # so we have a smoother state toggle
            if np.sum(slotdfft[slotdfft > avg + 15]) >= 200 and not states.isTransmitting() and not states.is_receiving_codec2_signal():
                addDelay = True
                slotbusy[slot] = True
                SLOT_DELAY[slot] = min(SLOT_DELAY[slot] + DELAY_INCREMENT, MAX_DELAY)
            else:
                SLOT_DELAY[slot] = max(SLOT_DELAY[slot] - 1, 0)

                if SLOT_DELAY[slot] == 0:
                    slotbusy[slot] = False
                else:
                    slotbusy[slot] = True

            # increment slot
            slot += 1
        states.set_channel_slot_busy(slotbusy)

        if addDelay:
            # Limit delay counter to a maximum of 200. The higher this value,
            # the longer we will wait until releasing state
            states.set_channel_busy_condition_traffic(True)
            CHANNEL_BUSY_DELAY = min(CHANNEL_BUSY_DELAY + DELAY_INCREMENT, MAX_DELAY)
        else:
            # Decrement channel busy counter if no signal has been detected.
            CHANNEL_BUSY_DELAY = max(CHANNEL_BUSY_DELAY - 1, 0)
            # When our channel busy counter reaches 0, toggle state to False
            if CHANNEL_BUSY_DELAY == 0:
                states.set_channel_busy_condition_traffic(False)

        # erase queue if greater than 3
        if fft_queue.qsize() >= 1:
            fft_queue = queue.Queue()

        fft_queue.put(dfftlist[:315])  # 315 --> bandwidth 3200

    except Exception as err:
        print(f"[MDM] calculate_fft: Exception: {err}")

def terminate():
    log.warning("[SHUTDOWN] terminating audio instance...")
    if sd._initialized:
        sd._terminate()
