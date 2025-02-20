import requests
import re
import structlog

def send_wavelog_qso_data(config, wavelog_data):
    """
    Sends wavelog QSO data to the specified server via API call.

    Parameters:
    server_host:port (str)
    server_api_key (str)
    wavelog_data (str): wavelog-formatted ADIF QSO data.
    """

    log = structlog.get_logger()

    # If False then exit the function
    wavelog = config['QSO_LOGGING'].get('enable_adif_wavelog', 'False')

    if not wavelog:
        return  # exit as we don't want to log Wavelog

    wavelog_host = config['QSO_LOGGING'].get('adif_wavelog_host', 'http://localhost/')
    wavelog_api_key = config['QSO_LOGGING'].get('adif_wavelog_api_key', '')

    # check if the last part in the HOST URL from the config is correct
    if wavelog_host.endswith("/"):
        url = wavelog_host + "index.php/api/qso"
    else:
        url = wavelog_host + "/" + "index.php/api/qso"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    data = {
        "key": wavelog_api_key,
        "station_profile_id": "1",
        "type": "adif",
        "string": wavelog_data
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an error for bad status codes
        log.info(f"[CHAT] Wavelog API: {wavelog_data}")
    except requests.exceptions.RequestException as e:
        log.warning(f"[WAVELOG ADIF API EXCEPTION]: {e}")
