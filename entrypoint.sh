#!/usr/bin/env bash

echo "Starting pulseaudio"
pulseaudio --exit-idle-time=-1 --daemon &

if [ -z "${RIGCTLD_ARGS+x}" ]; then
    echo "No RIGCTLD_ARGS set, not starting rigctld"
else
    echo "Starting rigctld with args ${RIGCTLD_ARGS}"
    rigctld ${RIGCTLD_ARGS} &
fi

echo "Starting FreeDATA server"
python3 /app/FreeDATA/freedata_server/server.py
