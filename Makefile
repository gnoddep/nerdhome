.PHONY: install-slimme-meter install-doorbell

install-slimme-meter:
	sudo ./install/install.sh slimme-meter

install-doorbell:
	sudo ./install/install.sh doorbell

install-mqtt-to-influxdb:
	sudo ./install/install.sh mqtt-to-influxdb
