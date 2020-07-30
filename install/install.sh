#!/bin/bash

CWD=$(dirname $0)
SERVICE=$1

if [ "${SERVICE}" = "" ]; then
    echo "Which service must be installed?"
    exit 1
fi

mkdir -p /usr/lib/nerdhome
for F in ${SERVICE}.py requirements*.txt; do
    cp ${CWD}/../${F} /usr/lib/nerdhome/${F}
done

for M in Nerdman Doorbell Adafruit_TSL2561; do
    rm -rf /usr/lib/nerdhome/${M}
    cp -a ${CWD}/../${M} /usr/lib/nerdhome/${M}
    chown -R root:root /usr/lib/nerdhome/${M}
done

if [ -f ${CWD}/${SERVICE}.default ]; then
    if [ ! -f /etc/default/${SERVICE} ]; then
        cp ${CWD}/${SERVICE}.default /etc/default/${SERVICE}
    fi
fi

mkdir -p /etc/nerdhome
for SRC in ${CWD}/../${SERVICE}.*.dist; do
    DEST=$(echo ${SRC} | sed -e "s/\.dist$//")
    if [ ! -f ${DEST} ]; then
        cp ${SRC} ${DEST}
    fi
done

cp ${CWD}/${SERVICE}.service /etc/systemd/system/${SERVICE}.service
systemctl daemon-reload
systemctl enable ${SERVICE}.service

cd /usr/lib/nerdhome
if [ ! -d .env ]; then
    python3 -m venv .env
fi

. ./.env/bin/activate
python -m pip install wheel
pip install -r requirements.txt

MODEL=$(cat /proc/cpuinfo | grep "^Model")
if echo ${MODEL} | grep -q "Raspberry Pi"; then
    pip install -r requirements-rpi.txt
fi

deactivate
