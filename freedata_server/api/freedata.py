from fastapi import APIRouter, Request
from api.common import api_response, api_abort, api_ok, validate
from api.command_helpers import enqueue_tx_command
from message_system_db_messages import DatabaseManagerMessages
from message_system_db_attachments import DatabaseManagerAttachments
from message_system_db_beacon import DatabaseManagerBeacon
from message_system_db_station import DatabaseManagerStations
import command_message_send
import adif_udp_logger
import wavelog_api_logger


router = APIRouter()


@router.get("/messages/{message_id}", summary="Get Message by ID", tags=["FreeDATA"], responses={
    200: {"description": "Message found and returned."},
    404: {"description": "Message not found."}
})
async def get_freedata_message(message_id: str, request: Request):
    message = DatabaseManagerMessages(request.app.event_manager).get_message_by_id_json(message_id)
    return api_response(message)


@router.post("/messages", summary="Transmit Message", tags=["FreeDATA"], responses={
    200: {
        "description": "Message transmitted successfully.",
        "content": {
            "application/json": {
                "example": {
                    "destination": "XX1XXX-6",
                    "body": "Hello FreeDATA"
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
                "example": {
                    "error": "Modem not running."
                }
            }
        }
    }
})
async def post_freedata_message(request: Request):
    """
    Transmit a FreeDATA message.

    Parameters:
        request (Request): The HTTP request containing the message data in JSON format.

    Returns:
        dict: A JSON object containing the transmitted message details.
    """
    data = await request.json()
    await enqueue_tx_command(request.app, command_message_send.SendMessageCommand, data)
    return api_response(data)

@router.post("/messages/{message_id}/adif", summary="Send Message ADIF Log", tags=["FreeDATA"], responses={
    200: {
        "description": "ADIF log sent successfully.",
        "content": {
            "application/json": {
                "example": {
                    "adif_output": "ADIF data..."
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid message ID."
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Message not found."
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
async def post_freedata_message_adif_log(message_id: str, request:Request):
    adif_output = DatabaseManagerMessages(request.app.event_manager).get_message_by_id_adif(message_id)

    # if message not found do not send adif as the return then is not valid
    if not adif_output:
        return

    # Send the ADIF data via UDP
    adif_udp_logger.send_adif_qso_data(request.app.config_manager.read(), adif_output)
    wavelog_api_logger.send_wavelog_qso_data(request.app.config_manager.read(), adif_output)
    return api_response(adif_output)

@router.patch("/messages/{message_id}", summary="Update Message by ID", tags=["FreeDATA"], responses={
    200: {
        "description": "Message updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "is_read": True
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
        "description": "Message not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Message not found."
                }
            }
        }
    }
})
async def patch_freedata_message(message_id: str, request: Request):
    """
    Update a FreeDATA message by its ID.

    Parameters:
        message_id (str): The ID of the message to update.
        request (Request): The HTTP request containing the update data in JSON format.

    Returns:
        dict: A JSON object containing the updated message details.
    """
    data = await request.json()

    if data.get("action") == "retransmit":
        result = DatabaseManagerMessages(request.app.event_manager).update_message(message_id, update_data={'status': 'queued'})
        DatabaseManagerMessages(request.app.event_manager).increment_message_attempts(message_id)
    else:
        result = DatabaseManagerMessages(request.app.event_manager).update_message(message_id, update_data=data)

    return api_response(result)


@router.get("/messages", summary="Get All Messages", tags=["FreeDATA"], responses={
    200: {
        "description": "List of all messages.",
        "content": {
            "application/json": {
                "example": {
                    "total_messages": 1,
                    "messages": [
                        {
                            "id": "DXCALL-6_MYCALL-0_2024-04-12T20:39:05.302479",
                            "timestamp": "2024-04-12T20:39:05.302479",
                            "origin": "DXCALL-6",
                            "via": None,
                            "destination": "MYCALL-0",
                            "direction": "receive",
                            "body": "Hello !",
                            "attachments": [],
                            "status": "received",
                            "priority": 10,
                            "is_read": False,
                            "statistics": {
                                "total_bytes": 120,
                                "duration": 29.76698660850525,
                                "bytes_per_minute": 241,
                                "time_histogram": {
                                    "0": "2024-04-12T20:39:23.423169",
                                    "1": "2024-04-12T20:39:30.504638",
                                    "2": "2024-04-12T20:39:37.745075"
                                },
                                "snr_histogram": {
                                    "0": -6,
                                    "1": -6,
                                    "2": -6
                                },
                                "bpm_histogram": {
                                    "0": 198,
                                    "1": 265,
                                    "2": 252
                                }
                            }
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
    }
})
async def get_freedata_messages(request: Request):
    filters = {k: v for k, v in request.query_params.items() if v}
    result = DatabaseManagerMessages(request.app.event_manager).get_all_messages_json(filters=filters)
    return api_response(result)


@router.post("/messages", summary="Transmit Message", tags=["FreeDATA"], responses={
    200: {
        "description": "Message transmitted successfully.",
        "content": {
            "application/json": {
                "example": {
                    "destination": "XX1XXX-6",
                    "body": "Hello FreeDATA"
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
async def post_freedata_message(request: Request):
    """
    Transmit a FreeDATA message.

    Parameters:
        request (Request): The HTTP request containing the message data in JSON format.

    Returns:
        dict: A JSON object containing the transmitted message details.
    """
    data = await request.json()
    await enqueue_tx_command(request.app, command_message_send.SendMessageCommand, data)
    return api_response(data)



@router.delete("/messages/{message_id}", summary="Delete Message by ID", tags=["FreeDATA"], responses={
    200: {
        "description": "Message deleted successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": "DXCALL-0_MYCALL-5_2024-04-04T17:22:14.002502 deleted",
                    "status": "success"
                }
            }
        }
    },
    404: {
        "description": "Message not found.",
        "content": {
            "application/json": {
                "example": {
                    "message": "Message not found",
                    "status": "failure"
                }
            }
        }
    }
})
async def delete_freedata_message(message_id: str, request:Request):
    result = DatabaseManagerMessages(request.app.event_manager).delete_message(message_id)
    if result:
        return api_response({"message": f"{message_id} deleted", "status": "success"})
    else:
        return api_response({"message": "Message not found", "status": "failure"}, status_code=404)


@router.get("/messages/{message_id}/attachments", summary="Get Attachments by Message ID", tags=["FreeDATA"], responses={
    200: {
        "description": "List of attachments for the specified message.",
        "content": {
            "application/json": {
                "example": {
                    "attachments": [
                        {
                            "id": "attachment1",
                            "filename": "file1.txt",
                            "file_size": 1024,
                            "file_type": "text/plain",
                            "data_sha512": "abcdef1234567890..."
                        },
                        {
                            "id": "attachment2",
                            "filename": "image.png",
                            "file_size": 2048,
                            "file_type": "image/png",
                            "data_sha512": "123456abcdef7890..."
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
async def get_message_attachments(message_id: str, request:Request):
    attachments = DatabaseManagerAttachments(request.app.event_manager).get_attachments_by_message_id_json(message_id)
    return api_response(attachments)


@router.get("/messages/attachment/{data_sha512}", summary="Get Attachment by SHA512", tags=["FreeDATA"], responses={
    200: {
        "description": "Retrieve a specific attachment by its SHA512 hash.",
        "content": {
            "application/json": {
                "example": {
                    "id": "attachment1",
                    "filename": "file1.txt",
                    "file_size": 1024,
                    "file_type": "text/plain",
                    "data_sha512": "abcdef1234567890..."
                }
            }
        }
    },
    404: {
        "description": "The requested attachment was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Attachment not found."
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
async def get_message_attachment(data_sha512: str, request:Request):
    attachment = DatabaseManagerAttachments(request.app.event_manager).get_attachment_by_sha512(data_sha512)
    return api_response(attachment)


@router.get("/beacons", summary="Get Received Beacons", tags=["FreeDATA"], responses={
    200: {
        "description": "List of received beacons.",
        "content": {
            "application/json": {
                "example": {
                    "total_beacons": 2,
                    "beacons": [
                        {
                            "id": "DXCALL-0_MYCALL-5_2024-04-04T17:22:14.002502",
                            "timestamp": "2024-04-04T17:22:14.002502",
                            "origin": "DXCALL-0",
                            "via": None,
                            "destination": "MYCALL-5",
                            "direction": "receive",
                            "body": "Hello FreeDATA",
                            "attachments": [],
                            "status": "received",
                            "priority": 10,
                            "is_read": False,
                            "statistics": {
                                "total_bytes": 120,
                                "duration": 29.77,
                                "bytes_per_minute": 241,
                                "time_histogram": {
                                    "0": "2024-04-04T17:22:23.423169",
                                    "1": "2024-04-04T17:22:30.504638",
                                    "2": "2024-04-04T17:22:37.745075"
                                },
                                "snr_histogram": {
                                    "0": -6,
                                    "1": -6,
                                    "2": -6
                                },
                                "bpm_histogram": {
                                    "0": 198,
                                    "1": 265,
                                    "2": 252
                                }
                            }
                        }
                    ]
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
async def get_all_beacons(request:Request):
    beacons = DatabaseManagerBeacon(request.app.event_manager).get_all_beacons()
    return api_response(beacons)


@router.get("/beacons/{callsign}", summary="Get Beacon by Callsign", tags=["FreeDATA"], responses={
    200: {
        "description": "List of beacons from the specified callsign.",
        "content": {
            "application/json": {
                "example": {
                    "beacons": [
                        {
                            "id": "DXCALL-0_MYCALL-5_2024-04-04T17:22:14.002502",
                            "timestamp": "2024-04-04T17:22:14.002502",
                            "origin": "DXCALL-0",
                            "via": None,
                            "destination": "MYCALL-5",
                            "direction": "receive",
                            "body": "Hello FreeDATA",
                            "attachments": [],
                            "status": "received",
                            "priority": 10,
                            "is_read": False,
                            "statistics": {
                                "total_bytes": 120,
                                "duration": 29.77,
                                "bytes_per_minute": 241,
                                "time_histogram": {
                                    "0": "2024-04-04T17:22:23.423169",
                                    "1": "2024-04-04T17:22:30.504638",
                                    "2": "2024-04-04T17:22:37.745075"
                                },
                                "snr_histogram": {
                                    "0": -6,
                                    "1": -6,
                                    "2": -6
                                },
                                "bpm_histogram": {
                                    "0": 198,
                                    "1": 265,
                                    "2": 252
                                }
                            }
                        }
                    ]
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
async def get_beacons_by_callsign(callsign: str, request:Request):
    beacons = DatabaseManagerBeacon(request.app.event_manager).get_beacons_by_callsign(callsign)
    return api_response(beacons)


@router.get("/station/{callsign}", summary="Get Station Info", tags=["FreeDATA"], responses={
    200: {
        "description": "Retrieve station information by callsign.",
        "content": {
            "application/json": {
                "example": {
                    "callsign": "MYCALL-0",
                    "location": "Springfield",
                    "frequency": "14093000",
                    "mode": "PKTUSB",
                    "status": "active",
                    "additional_info": "Station details here."
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid callsign parameter."
                }
            }
        }
    },
    404: {
        "description": "The requested station was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Station not found."
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
async def get_station_info(callsign: str, request: Request):
    station = DatabaseManagerStations(request.app.event_manager).get_station(callsign)
    return api_response(station)


@router.post("/station/{callsign}", summary="Set Station Info", tags=["FreeDATA"], responses={
    200: {
        "description": "Station information updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "callsign": "MYCALL-0",
                    "location": "Springfield",
                    "frequency": "14093000",
                    "mode": "PKTUSB",
                    "status": "active",
                    "additional_info": "Updated station details."
                }
            }
        }
    },
    400: {
        "description": "Bad Request: The request was malformed or missing required parameters.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid input data."
                }
            }
        }
    },
    404: {
        "description": "The requested station was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Station not found."
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
async def set_station_info(callsign: str, request: Request):
    data = await request.json()
    result = DatabaseManagerStations(request.app.event_manager).update_station_info(callsign, new_info=data["info"])
    return api_response(result)