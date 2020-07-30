.PHONY: install-slimme-meter install-nerdhome install-mqtt-to-influxdb install-mqtt-to-prometheus install-mqtt-to-hue

install-slimme-meter:
	sudo ./install/install.sh slimme-meter

install-nerdhome:
	sudo ./install/install.sh nerdhome

install-mqtt-to-influxdb:
	sudo ./install/install.sh mqtt-to-influxdb

install-mqtt-to-hue:
	sudo ./install/install.sh mqtt-to-hue

install-mqtt-to-prometheus:
	sudo ./install/install.sh mqtt-to-prometheus
