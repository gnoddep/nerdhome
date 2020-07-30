.PHONY: install-doorbell install-mqtt-to-prometheus install-mqtt-to-hue install-smartmeter

install-doorbell:
	sudo ./install/install.sh doorbell

install-mqtt-to-hue:
	sudo ./install/install.sh mqtt-to-hue

install-mqtt-to-prometheus:
	sudo ./install/install.sh mqtt-to-prometheus

install-smartmeter:
	sudo ./install/install.sh smartmeter
