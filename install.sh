#!/bin/bash

mkdir -p /usr/lib/slimme-meter
for F in slimme-meter.py requirements.txt; do
    cp ${F} /usr/lib/slimme-meter/${F}
done

if [ ! -f /etc/default/slimme-meter ]; then
    cp slimme-meter.default /etc/default/slimme-meter
fi

cp slimme-meter.service /etc/systemd/system/slimme-meter.service
systemctl daemon-reload
systemctl enable slimme-meter.service

cd /usr/lib/slimme-meter
if [ ! -d .env ]; then
    python3 -m venv .env
fi

. ./.env/bin/activate
pip install -r requirements.txt
deactivate
