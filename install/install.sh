#!/bin/bash

CWD=$(dirname $0)
SERVICE=$1

if [ "${SERVICE}" = "" ]; then
    echo "Which service must be installed?"
    exit 1
fi

mkdir -p /usr/lib/nerdhome
for F in ${SERVICE}.py requirements.txt; do
    cp ${CWD}/../${F} /usr/lib/nerdhome/${F}
done

for M in Nerdman Doorbell Adafruit_TSL2561; do
    rm -rf /usr/lib/nerdhome/${M}
    cp -a ${CWD}/../${M} /usr/lib/nerdhome/${M}
    chown -R root:root /usr/lib/nerdhome/${M}
done

if [ ! -f /etc/default/${SERVICE} ]; then
    cp ${CWD}/${SERVICE}.default /etc/default/${SERVICE}
fi

cp ${CWD}/${SERVICE}.service /etc/systemd/system/${SERVICE}.service
systemctl daemon-reload
systemctl enable ${SERVICE}.service

cd /usr/lib/nerdhome
if [ ! -d .env ]; then
    python3 -m venv .env
fi

. ./.env/bin/activate
pip install -r requirements.txt
deactivate
