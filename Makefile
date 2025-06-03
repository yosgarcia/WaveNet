OS := $(shell uname)

all:
ifeq ($(OS), Darwin)
	@echo "Detected macOS"
	@which brew > /dev/null || (echo "Homebrew not found! Please install it first." && exit 1)
	brew install portaudio
else ifeq ($(OS), Linux)
	@echo "Detected Linux"
	@which apt > /dev/null || (echo "This script currently supports apt-based distros only." && exit 1)
	sudo apt update
	sudo apt install -y portaudio19-dev python3-pip
else
	@echo "Unsupported OS: $(OS)"
	@exit 1
endif
	pip install -e ./DispositivoWaveNET
	pip install -e ./WaveNetCore
	pip install -e ./WaveNetAplicacion
