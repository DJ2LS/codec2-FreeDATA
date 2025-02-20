from fastapi import APIRouter, Request
from api.common import api_response, api_abort, api_ok, validate
from api.command_helpers import enqueue_tx_command
import command_cq
import command_beacon
import command_ping
import command_fec
import command_test
import command_arq_raw
import api_validations as validations

router = APIRouter()


@router.get("/state", summary="Get Modem State", tags=["Modem"], responses={
    200: {
        "description": "Current modem state information.",
        "content": {
            "application/json": {
                "example": {
                    "activities": {
                        "161dd75ef3b5847a": {
                            "activity_type": "ARQ_BURST_ACK",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "session_id": 105,
                            "snr": 4,
                            "timestamp": 1713034266
                        },
                        "168e90799d13b7b4": {
                            "activity_type": "ARQ_SESSION_INFO_ACK",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "session_id": 105,
                            "snr": -3,
                            "timestamp": 1713034248
                        },
                        "2218b849e937d36d": {
                            "activity_type": "QRV",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "gridsquare": "JP15OW",
                            "origin": "SOMECALL-1",
                            "snr": 2,
                            "timestamp": 1713034200
                        },
                        "3fb424827f4632ab": {
                            "activity_type": "BEACON",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "gridsquare": "JP22AI",
                            "origin": "CALLSIGN-1",
                            "snr": -8,
                            "timestamp": 1713034455
                        },
                        "743222d1dd64ce9d": {
                            "activity_type": "ARQ_SESSION_OPEN_ACK",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "origin": "CALL-1",
                            "session_id": 105,
                            "snr": -2,
                            "timestamp": 1713034243
                        },
                        "7589edf6bf23ceed": {
                            "activity_type": "ARQ_BURST_ACK",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "session_id": 105,
                            "snr": 2,
                            "timestamp": 1713034275
                        },
                        "9d2c5a98fe0f9894": {
                            "activity_type": "QRV",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "gridsquare": "JP12AW",
                            "origin": "CALLME-1",
                            "snr": 5,
                            "timestamp": 1713034178
                        },
                        "f85609dced4ea40a": {
                            "activity_type": "ARQ_BURST_ACK",
                            "direction": "received",
                            "frequency": "14093000",
                            "frequency_offset": 0,
                            "session_id": 105,
                            "snr": 0,
                            "timestamp": 1713034257
                        }
                    },
                    "audio_dbfs": -7.915304862713354,
                    "channel_busy_slot": [False, False, True, False, False],
                    "is_away_from_key": False,
                    "is_beacon_running": True,
                    "is_modem_busy": False,
                    "is_modem_running": True,
                    "radio_frequency": "14093000",
                    "radio_mode": "PKTUSB",
                    "radio_status": True,
                    "s_meter_strength": "20",
                    "type": "state"
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
async def get_modem_state(request:Request):
    """
    Retrieve the current state of the modem.

    Returns:
        dict: A JSON object containing modem state information.
    """
    return request.app.state_manager.sendState()


@router.post("/cqcqcq", summary="Send CQ Command", tags=["Modem"], responses={
    200: {
        "description": "CQ command sent successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": "ok"
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
async def post_cqcqcq(request:Request):
    """
    Trigger the modem to send a CQ.

    Returns:
        dict: A JSON object indicating success.

    Raises:
        HTTPException: If the modem is not running.
    """
    if not request.app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    await enqueue_tx_command(request.app, command_cq.CQCommand)
    return api_ok()


@router.post("/beacon", summary="Enable/Disable Modem Beacon", tags=["Modem"], responses={
    200: {
        "description": "Beacon status updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "enabled": True,
                    "away_from_key": False
                }
            }
        }
    },
    400: {
        "description": "Invalid input parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Incorrect value for 'enabled' or 'away_from_key'. Should be bool."
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
async def post_beacon(request: Request):
    """
    Enable or disable the modem beacon.

    Parameters:
        request (Request): The HTTP request containing the following JSON keys:
            - 'enabled' (bool): True to enable the beacon, False to disable.
            - 'away_from_key' (bool): True if away from key, False otherwise.

    Returns:
        dict: A JSON object indicating the beacon status.

    Raises:
        HTTPException: If parameters are invalid or modem is not running.
    """
    data = await request.json()
    if not isinstance(data.get('enabled'), bool) or not isinstance(data.get('away_from_key'), bool):
        api_abort("Incorrect value for 'enabled' or 'away_from_key'. Should be bool.", 400)
    if not request.app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    request.app.state_manager.set('is_beacon_running', data['enabled'])
    request.app.state_manager.set('is_away_from_key', data['away_from_key'])
    if not request.app.state_manager.getARQ() and data['enabled']:
        await enqueue_tx_command(request.app, command_beacon.BeaconCommand, data)
    return api_response({"enabled": data['enabled'], "away_from_key": data['away_from_key']})


@router.post("/ping_ping", summary="Trigger Modem to PING a Station", tags=["Modem"], responses={
    200: {
        "description": "Ping command sent successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": True
                }
            }
        }
    },
    400: {
        "description": "Invalid input parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid 'dxcall' parameter."
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
async def post_ping(request: Request):
    """
    Trigger the modem to send a PING to a station.

    Parameters:
        request (Request): The HTTP request containing the following JSON key:
            - 'dxcall' (str): Callsign of the station to ping.

    Returns:
        dict: A JSON object indicating success.

    Raises:
        HTTPException: If parameters are invalid or modem is not running.
    """
    data = await request.json()
    if not request.app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    dxcall = data.get('dxcall')
    if not dxcall or not validations.validate_freedata_callsign(dxcall):
        api_abort("Invalid 'dxcall' parameter.", 400)
    await enqueue_tx_command(request.app, command_ping.PingCommand, data)
    return api_response({"message": True})


@router.post("/send_test_frame", summary="Send Test Frame", tags=["Modem"], responses={
    200: {
        "description": "Test frame sent successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": "ok"
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
async def post_send_test_frame(request:Request):
    """
    Trigger the modem to send a test frame.

    Returns:
        dict: A JSON object indicating success.

    Raises:
        HTTPException: If the modem is not running.
    """
    if not request.app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    await enqueue_tx_command(request.app, command_test.TestCommand)
    return api_ok()

@router.post("/fec_transmit", summary="FEC Transmit", tags=["Modem"], responses={
    200: {
        "description": "FEC frame transmitted successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": "FEC transmission started."
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
    500: {
        "description": "Internal Server Error: An unexpected error occurred on the server.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Internal server error."
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
async def post_send_fec_frame(request: Request):
    """
    Trigger the modem to transmit a Forward Error Correction (FEC) frame.

    Parameters:
        request (Request): The HTTP request containing transmission parameters in JSON format.

    Returns:
        dict: A JSON object indicating success.

    Raises:
        HTTPException: If the modem is not running, the request is malformed, or an internal error occurs.
    """
    if not request.app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)

    try:
        data = await request.json()
    except Exception:
        api_abort("Invalid parameters.", 400)

    # Validate required parameters (adjust based on actual requirements)
    if 'message' not in data:
        api_abort("Invalid parameters: 'message' field is required.", 400)

    # Enqueue the FEC transmission command
    try:
        await enqueue_tx_command(request.app, command_fec.FecCommand, data)
        return api_response({"message": "FEC transmission started."})
    except Exception as e:
        # Log the exception if necessary
        api_abort("Internal server error.", 500)


from fastapi import HTTPException

@router.get("/fec_is_writing", summary="Indicate User is Typing (FEC)", tags=["Modem"], responses={
    501: {
        "description": "Feature not implemented.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Feature not implemented yet."
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
async def get_fec_is_writing(request:Request):
    """
    Trigger the modem to inform over RF that the user is typing a message.

    Returns:
        dict: A JSON object indicating that the feature is not implemented.

    Raises:
        HTTPException: If the modem is not running or the feature is not implemented.
    """
    if not request.app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)

    # Since the feature is not implemented yet, return a 501 Not Implemented error
    raise HTTPException(status_code=501, detail="Feature not implemented yet.")


@router.post("/start", summary="Start Modem", tags=["Modem"], responses={
    200: {
        "description": "Modem started successfully.",
        "content": {
            "application/json": {
                "examples": {
                    "modem_started": {
                        "summary": "Modem Started",
                        "value": {
                            "modem": "started"
                        }
                    },
                    "message_ok": {
                        "summary": "Message OK",
                        "value": {
                            "message": "ok"
                        }
                    }
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
    500: {
        "description": "Internal Server Error: An unexpected error occurred on the server.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Internal server error."
                }
            }
        }
    }
})
async def post_modem_start(request: Request):
    """
    Trigger the modem to start.

    Parameters:
        request (Request): The HTTP request
    Returns:
        dict: A JSON object indicating the modem has started.

    Raises:
        HTTPException: If parameters are invalid or an error occurs.
    """

    try:
        if not request.app.state_manager.is_modem_running:
            request.app.modem_service.put("start")
            return api_response({"modem": "started"})
        else:
            api_abort("Modem already running", 503)
    except Exception as e:
        api_abort(f"Internal server error. {e}", 500)


@router.post("/stop", summary="Stop Modem", tags=["Modem"], responses={
    200: {
        "description": "Modem stopped successfully.",
        "content": {
            "application/json": {
                "examples": {
                    "modem_stopped": {
                        "summary": "Modem Stopped",
                        "value": {
                            "modem": "stopped"
                        }
                    },
                    "message_ok": {
                        "summary": "Message OK",
                        "value": {
                            "message": "ok"
                        }
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
async def post_modem_stop(request:Request):
    """
    Trigger the modem to stop.

    Returns:
        dict: A JSON object indicating the modem has stopped.

    Raises:
        HTTPException: If the modem is not running or an error occurs.
    """
    #if not request.app.state_manager.is_modem_running:
    #    api_abort("Modem not running", 503)

    try:
        request.app.modem_service.put("stop")
        return api_response({"modem": "stopped"})
    except Exception as e:
        api_abort(f"Internal server error. {e}", 500)



@router.post("/send_arq_raw", summary="Send ARQ Raw Data", tags=["Modem"], responses={
    200: {
        "description": "ARQ raw data sent successfully.",
        "content": {
            "application/json": {
                "example": {
                    "data": "RnJlZURBVEEgaXMgdGhlIGJlc3Qh",
                    "dxcall": "XX1XXX-6",
                    "type": "raw"
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
async def post_send_arq_raw(request: Request):
    """
    Send ARQ raw data to a specified station.

    Parameters:
        request (Request): The HTTP request containing the following JSON keys:
            - 'dxcall' (str): Callsign of the station to send data to.
            - 'type' (str): Data type ('raw', 'raw_lzma', 'raw_gzip').
            - 'data' (str): Base64 encoded data to send.

    Returns:
        dict: A JSON object echoing the sent data.

    Raises:
        HTTPException: If parameters are invalid or modem is not running/busy.
    """
    if not request.app.state_manager.is_modem_running:
        api_abort("Modem not running.", 503)
    if request.app.state_manager.is_modem_busy:
        api_abort("Modem Busy.", 503)
    data = await request.json()
    dxcall = data.get('dxcall')
    data_type = data.get('type')
    raw_data = data.get('data')
    if not dxcall or not validations.validate_freedata_callsign(dxcall):
        api_abort("Invalid 'dxcall' parameter.", 400)
    if data_type not in ['raw', 'raw_lzma', 'raw_gzip']:
        api_abort("Invalid 'type' parameter.", 400)
    if not raw_data:
        api_abort("Missing 'data' parameter.", 400)
    await enqueue_tx_command(request.app, command_arq_raw.SendARQRawCommand, data)
    return api_response({
        "data": raw_data,
        "dxcall": dxcall,
        "type": data_type
    })


@router.post("/stop_transmission", summary="Stop Transmission", tags=["Modem"], responses={
    200: {
        "description": "Transmission stopped successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": "ok"
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid request."
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
    500: {
        "description": "Internal Server Error: An unexpected error occurred on the server.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Internal server error."
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
async def post_modem_stop_transmission(request:Request):
    """
    Stop the current transmission.

    Returns:
        dict: A JSON object indicating success.

    Raises:
        HTTPException: If the modem is not running or an error occurs.
    """
    if not request.app.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    if request.app.state_manager.getARQ():
        try:
            for session in request.app.state_manager.arq_irs_sessions.values():
                # session.abort_transmission()
                session.transmission_aborted()
            for session in request.app.state_manager.arq_iss_sessions.values():
                session.abort_transmission(send_stop=False)
                session.transmission_aborted()
        except Exception as e:
            print(f"Error during transmission stopping: {e}")
    return api_ok()



