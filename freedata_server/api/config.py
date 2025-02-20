from fastapi import APIRouter, Request
from api.common import api_response, api_abort, api_ok, validate
import api_validations as validations
router = APIRouter()

@router.get("/", summary="Get Modem Configuration", tags=["Configuration"], responses={
    200: {
        "description": "Current modem configuration settings.",
        "content": {
            "application/json": {
                "example": {
                    "AUDIO": {
                        "input_device": "2fc0",
                        "output_device": "3655",
                        "rx_audio_level": 0,
                        "tx_audio_level": 2
                    },
                    "MESSAGES": {
                        "enable_auto_repeat": True
                    },
                    "MODEM": {
                        "enable_morse_identifier": False,
                        "enable_socket_interface": False,
                        "maximum_bandwidth": 2438,
                        "tx_delay": 200
                    },
                    "NETWORK": {
                        "modemaddress": "",
                        "modemport": 5000
                    },
                    "RADIO": {
                        "control": "rigctld",
                        "data_bits": 8,
                        "model_id": 1001,
                        "ptt_port": "ignore",
                        "ptt_type": "USB",
                        "serial_dcd": "NONE",
                        "serial_dtr": "OFF",
                        "serial_handshake": "ignore",
                        "serial_port": "/dev/cu.Bluetooth-Incoming-Port",
                        "serial_speed": 38400,
                        "stop_bits": 1
                    },
                    "RIGCTLD": {
                        "arguments": "",
                        "command": "",
                        "ip": "127.0.0.1",
                        "path": "",
                        "port": 4532
                    },
                    "SOCKET_INTERFACE": {
                        "cmd_port": 0,
                        "data_port": 0,
                        "enable": False,
                        "host": ""
                    },
                    "STATION": {
                        "enable_explorer": True,
                        "enable_stats": True,
                        "mycall": "LA3QMA",
                        "mygrid": "JP20ql",
                        "myssid": 0,
                        "ssid_list": [0,1,2,3,4,5,6,7,8,9],
                        "respond_to_cq": True,
                    },
                    "TCI": {
                        "tci_ip": "127.0.0.1",
                        "tci_port": 50001
                    }
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
    }
})
async def get_config(request: Request):
    """
    Retrieve the current modem configuration.

    Returns:
        dict: The modem configuration settings.
    """
    return request.app.config_manager.read()


@router.post("/", summary="Update Modem Configuration", tags=["Configuration"], responses={
    200: {
        "description": "Modem configuration updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "AUDIO": {
                        "input_device": "2fc0",
                        "output_device": "3655",
                        "rx_audio_level": 0,
                        "tx_audio_level": 2
                    },
                    # ...
                }
            }
        }
    },
    400: {
        "description": "Invalid configuration data.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid config"
                }
            }
        }
    },
    500: {
        "description": "Error writing configuration.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Error writing config"
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
    }
})
async def post_config(request: Request):
    """
    Update the modem configuration with new settings.

    Parameters:
        request (Request): The HTTP request containing the new configuration in JSON format.

    Returns:
        dict: The updated modem configuration.

    Raises:
        HTTPException: If the provided configuration is invalid or an error occurs while writing the config.
    """
    config = await request.json()
    print(config)
    if not validations.validate_remote_config(config):
        api_abort("Invalid config", 400)
    if request.app.config_manager.read() == config:
        return config
    set_config = request.app.config_manager.write(config)
    if not set_config:
        api_abort("Error writing config", 500)
    request.app.modem_service.put("restart")
    return set_config
