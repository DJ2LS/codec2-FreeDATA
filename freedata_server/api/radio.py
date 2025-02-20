from fastapi import APIRouter, Request
from api.common import api_response, api_abort, api_ok, validate
from api.command_helpers import enqueue_tx_command
import command_transmit_sine

router = APIRouter()



@router.get("/", summary="Get Radio Parameters", tags=["Radio"], responses={
    200: {
        "description": "Current radio parameters.",
        "content": {
            "application/json": {
                "example": {
                    "radio_frequency": "14093000",
                    "radio_mode": "PKTUSB",
                    "radio_rf_level": 100,
                    "radio_status": True,
                    "radio_swr": 0,
                    "radio_tuner": False,
                    "s_meter_strength": "20"
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
async def get_radio(request: Request):
    """
    Retrieve current radio parameters.

    Returns:
        dict: A JSON object containing radio parameters.
    """
    return request.app.state_manager.get_radio_status()


@router.post("/", summary="Set Radio Parameters", tags=["Radio"], responses={
    200: {
        "description": "Radio parameters updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "radio_frequency": "14093000",
                    "radio_mode": "PKTUSB",
                    "radio_rf_level": 100,
                    "radio_status": True,
                    "radio_swr": 0,
                    "radio_tuner": True,
                    "s_meter_strength": "20"
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid parameters."
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
async def post_radio(request: Request):
    """
    Set radio parameters.

    Parameters:
        request (Request): The HTTP request containing the radio parameters in JSON format.

    Returns:
        dict: A JSON object containing the updated radio parameters.
    """
    data = await request.json()
    radio_manager = request.app.radio_manager
    if "radio_frequency" in data:
        radio_manager.set_frequency(data['radio_frequency'])
    if "radio_mode" in data:
        radio_manager.set_mode(data['radio_mode'])
    if "radio_rf_level" in data:
        radio_manager.set_rf_level(int(data['radio_rf_level']))
    if "radio_tuner" in data:
        radio_manager.set_tuner(data['radio_tuner'])
    return api_response(data)


@router.post("/tune", summary="Enable/Disable Radio Tuning", tags=["Radio"], responses={
    200: {
        "description": "Radio tuning status updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "enable_tuning": True
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid parameters."
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
        "description": "Modem not running or busy.",
        "content": {
            "application/json": {
                "examples": {
                    "modem_not_running": {
                        "summary": "Modem Not Running",
                        "value": {
                            "error": "Modem not running."
                        }
                    },
                    "modem_busy": {
                        "summary": "Modem Busy",
                        "value": {
                            "error": "Modem Busy."
                        }
                    }
                }
            }
        }
    }
})
async def post_radio_tune(request: Request):
    """
    Trigger the modem to inform over RF that the user is typing a message.

    Parameters:
        request (Request): The HTTP request containing the following JSON key:
            - 'enable_tuning' (bool): True to enable tuning, False to disable.

    Returns:
        dict: A JSON object echoing the tuning status.

    Raises:
        HTTPException: If the modem is not running/busy or if parameters are invalid.
    """
    data = await request.json()
    if "enable_tuning" in data:
        if data['enable_tuning']:
            if not request.app.state_manager.is_modem_running:
                api_abort("Modem not running", 503)
            await enqueue_tx_command(request.app, command_transmit_sine.TransmitSine)
        else:
            request.app.service_manager.modem.stop_sine()
    else:
        request.app.service_manager.modem.stop_sine()

    return api_response(data)
