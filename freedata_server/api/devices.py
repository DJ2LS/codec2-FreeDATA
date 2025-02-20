from fastapi import APIRouter, Request
from api.common import api_response, api_abort, api_ok, validate
router = APIRouter()
import audio
import serial_ports


@router.get("/audio", summary="Get Audio Devices", tags=["Devices"], responses={
    200: {
        "description": "List of available audio input and output devices.",
        "content": {
            "application/json": {
                "example": {
                    "in": [
                        {
                            "api": "ALSA",
                            "id": "8eb1",
                            "name": "pipewire",
                            "native_index": 4
                        },
                        {
                            "api": "ALSA",
                            "id": "8e7a",
                            "name": "default",
                            "native_index": 5
                        }
                    ],
                    "out": [
                        {
                            "api": "ALSA",
                            "id": "ae79",
                            "name": "HDA Intel HDMI: 0 (hw:0,3)",
                            "native_index": 0
                        },
                        {
                            "api": "ALSA",
                            "id": "67fd",
                            "name": "HDA Intel HDMI: 1 (hw:0,7)",
                            "native_index": 1
                        },
                        {
                            "api": "ALSA",
                            "id": "b68c",
                            "name": "HDA Intel HDMI: 2 (hw:0,8)",
                            "native_index": 2
                        },
                        {
                            "api": "ALSA",
                            "id": "ba84",
                            "name": "hdmi",
                            "native_index": 3
                        },
                        {
                            "api": "ALSA",
                            "id": "8eb1",
                            "name": "pipewire",
                            "native_index": 4
                        },
                        {
                            "api": "ALSA",
                            "id": "8e7a",
                            "name": "default",
                            "native_index": 5
                        }
                    ]
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def get_audio_devices():
    """
    Retrieve a list of available audio input and output devices.

    Returns:
        dict: A JSON object containing lists of input and output audio devices.
    """
    # Uncomment the following line if using the actual function
    # dev_in, dev_out = audio.get_audio_devices()
    dev_in, dev_out = audio.fetch_audio_devices([], [])
    return {'in': dev_in, 'out': dev_out}


@router.get("/serial", summary="Get Serial Devices", tags=["Devices"], responses={
    200: {
        "description": "List of available serial devices (COM ports).",
        "content": {
            "application/json": {
                "example": [
                    {
                        "description": "n/a [26a9]",
                        "port": "/dev/ttyS4"
                    }
                ]
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Modem not running.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def get_serial_devices():
    """
    Retrieve a list of available serial devices (COM ports).

    Returns:
        list: A list of dictionaries containing serial port information.
    """
    devices = serial_ports.get_ports()
    return devices
