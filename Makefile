.PHONY: install-doorbell install-mqtt-to-influxdb install-mqtt-to-prometheus install-mqtt-to-hue

install-doorbell:
	sudo ./install/install.sh doorbell

install-mqtt-to-influxdb:
	sudo ./install/install.sh mqtt-to-influxdb

install-mqtt-to-hue:
	sudo ./install/install.sh mqtt-to-hue

install-mqtt-to-prometheus:
	sudo ./install/install.sh mqtt-to-prometheus
