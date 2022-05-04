"""
Tests for the FreeDATA TNC state machine.
"""

import data_handler
import helpers
import static


def t_create_frame(frame_type: int, mycall: str, dxcall: str) -> bytearray:
    """
    Generate the create_session frame.
    """
    mycallsign_bytes = helpers.callsign_to_bytes(mycall)
    mycallsign = helpers.bytes_to_callsign(mycallsign_bytes)
    mycallsign_crc = helpers.get_crc_24(mycallsign)

    dxcallsign_bytes = helpers.callsign_to_bytes(dxcall)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign_bytes)
    dxcallsign_crc = helpers.get_crc_24(dxcallsign)

    frame = bytearray(14)
    frame[:1] = bytes([frame_type])
    frame[1:4] = dxcallsign_crc
    frame[4:7] = mycallsign_crc
    frame[7:13] = mycallsign_bytes

    return frame


def t_create_start_session(mycall: str, dxcall: str) -> bytearray:
    """
    Generate the create_session frame.
    """
    return t_create_frame(221, mycall, dxcall)


def t_create_session_close(mycall: str, dxcall: str) -> bytearray:
    """
    Generate the session_close frame.
    """
    return t_create_frame(223, mycall, dxcall)


def print_frame(data: bytearray):
    print(f"Type   : {int(data[0])}")
    print(f"DXCRC  : {bytes(data[1:4])}")
    print(f"CallCRC: {bytes(data[4:7])}")
    print(f"Call   : {helpers.bytes_to_callsign(data[7:13])}")


def t_tsh():
    print("In transmit_session_heartbeat")


def test_0():
    """
    Execute test to validate that receiving a session open frame sets the correct machine
    state.
    """
    t_callsign_bytes = helpers.callsign_to_bytes("AA1AA-0")
    t_callsign = helpers.bytes_to_callsign(t_callsign_bytes)
    t_callsign_crc = helpers.get_crc_24(t_callsign)
    print(f"{t_callsign=}")
    print(f"{t_callsign_crc=}")

    mycallsign_bytes = helpers.callsign_to_bytes("AA9AA-0")
    mycallsign = helpers.bytes_to_callsign(mycallsign_bytes)
    mycallsign_crc = helpers.get_crc_24(mycallsign)
    print(f"{mycallsign=}")
    print(f"{mycallsign_crc=}")

    dxcallsign_bytes = helpers.callsign_to_bytes("ZZ9ZZ-0")
    dxcallsign = helpers.bytes_to_callsign(dxcallsign_bytes)
    dxcallsign_crc = helpers.get_crc_24(dxcallsign)
    print(f"{dxcallsign=}")
    print(f"{dxcallsign_crc=}")

    assert (
        helpers.check_callsign(t_callsign, t_callsign_crc)[0] is True
    ), f"{helpers.check_callsign(t_callsign, t_callsign_crc)[0]=}"
    assert (
        helpers.check_callsign(mycallsign, mycallsign_crc)[0] is True
    ), f"{helpers.check_callsign(mycallsign, mycallsign_crc)[0]=}"
    assert (
        helpers.check_callsign(dxcallsign, dxcallsign_crc)[0] is True
    ), f"{helpers.check_callsign(dxcallsign, dxcallsign_crc)[0]=}"
    assert (
        helpers.check_callsign(mycallsign, dxcallsign_crc)[0] is False
    ), f"{helpers.check_callsign(mycallsign, dxcallsign_crc)[0]=}"


def test_1():
    """
    Execute test to validate that receiving a session open frame sets the correct machine
    state.
    """
    # Setup the static parameters for the connection.
    mycallsign_bytes = helpers.callsign_to_bytes("AA1AA-0")
    mycallsign = helpers.bytes_to_callsign(mycallsign_bytes)
    static.MYCALLSIGN = mycallsign
    static.MYCALLSIGN_CRC = helpers.get_crc_24(mycallsign)

    dxcallsign_bytes = helpers.callsign_to_bytes("AA9AA-0")
    dxcallsign = helpers.bytes_to_callsign(dxcallsign_bytes)
    static.DXCALLSIGN = dxcallsign
    static.DXCALLSIGN_CRC = helpers.get_crc_24(dxcallsign)

    # Create the TNC
    tnc = data_handler.DATA()

    # Replace the heartbeat transmit routine with a No-Op.
    tnc.transmit_session_heartbeat = t_tsh

    # Create packet to be 'received' by this station.
    create_frame = t_create_start_session(mycall="AA9AA-0", dxcall="AA1AA-0")
    print_frame(create_frame)
    tnc.received_session_opener(create_frame)

    assert static.ARQ_SESSION is True
    assert static.TNC_STATE == "BUSY"
    assert static.ARQ_SESSION_STATE == "connecting"

    # Create packet to be 'received' by this station.
    close_frame = t_create_session_close(mycall="AA9AA-0", dxcall="AA1AA-0")
    print_frame(close_frame)
    tnc.received_session_close(close_frame)

    assert (
        helpers.callsign_to_bytes(static.MYCALLSIGN) == mycallsign_bytes
    ), f"{static.MYCALLSIGN} != AA1AA-0"
    assert (
        helpers.callsign_to_bytes(static.DXCALLSIGN) == dxcallsign_bytes
    ), f"{static.DXCALLSIGN} != AA9AA-0"

    # assert static.ARQ_SESSION is False
    # assert static.TNC_STATE == "IDLE"
    # assert static.ARQ_SESSION_STATE == "disconnected"


def test_2():
    """
    Execute test to validate that receiving a session open frame sets the correct machine
    state.
    """
    # Setup the static parameters for the connection.
    mycallsign_bytes = helpers.callsign_to_bytes("AA1AA-0")
    mycallsign = helpers.bytes_to_callsign(mycallsign_bytes)
    static.MYCALLSIGN = mycallsign
    static.MYCALLSIGN_CRC = helpers.get_crc_24(mycallsign)

    dxcallsign_bytes = helpers.callsign_to_bytes("AA9AA-0")
    dxcallsign = helpers.bytes_to_callsign(dxcallsign_bytes)
    static.DXCALLSIGN = dxcallsign
    static.DXCALLSIGN_CRC = helpers.get_crc_24(dxcallsign)

    # Create the TNC
    tnc = data_handler.DATA()

    # Replace the heartbeat transmit routine with a No-Op.
    tnc.transmit_session_heartbeat = t_tsh

    # Create packet to be 'received' by this station.
    create_frame = t_create_start_session(mycall="AA9AA-0", dxcall="AA1AA-0")
    print_frame(create_frame)
    tnc.received_session_opener(create_frame)

    assert (
        helpers.callsign_to_bytes(static.MYCALLSIGN) == mycallsign_bytes
    ), f"{static.MYCALLSIGN} != AA1AA-0"
    assert (
        helpers.callsign_to_bytes(static.DXCALLSIGN) == dxcallsign_bytes
    ), f"{static.DXCALLSIGN} != AA9AA-0"

    assert static.ARQ_SESSION is True
    assert static.TNC_STATE == "BUSY"
    assert static.ARQ_SESSION_STATE == "connecting"

    foreigncall_bytes = helpers.callsign_to_bytes("ZZ0ZZ-0")
    # foreigncall = helpers.bytes_to_callsign(foreigncall_bytes)

    close_frame = t_create_session_close("ZZ0ZZ-0", "ZZ9ZZ-0")
    print_frame(close_frame)
    assert (
        helpers.check_callsign(static.DXCALLSIGN, bytes(close_frame[4:7]))[0] is False
    ), "Callsign matches DX checksum."
    # assert (
    #     helpers.check_callsign(foreigncall_bytes, bytes(close_frame[4:7]))[0] is True
    # ), "Callsign doesn't match checksum."
    tnc.received_session_close(close_frame)

    assert helpers.callsign_to_bytes(static.MYCALLSIGN) == helpers.callsign_to_bytes(
        "AA1AA-0"
    ), f"{static.MYCALLSIGN} != AA1AA-0"
    assert helpers.callsign_to_bytes(static.DXCALLSIGN) == helpers.callsign_to_bytes(
        "AA9AA-0"
    ), f"{static.DXCALLSIGN} != AA9AA-0"

    assert static.ARQ_SESSION is True
    assert static.TNC_STATE == "BUSY"
    assert static.ARQ_SESSION_STATE == "connecting"


def run_test():
    """
    Execute tests
    """
    total = 0
    try:
        test_0()
    except AssertionError:
        total += 1
    print("========================================================================")
    test_1()
    print("========================================================================")
    test_2()
    print("========================================================================")

    print(f"errors: {total}")


if __name__ == "__main__":
    run_test()
