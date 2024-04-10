HOST=$(shell hostname)

ifeq (${HOST}, "pop-os")
PORT=/dev/ttyACM0
else
PORT=/dev/ttyACM0
endif

all:
	echo ${HOST}

s:
	sudo screen -L ${PORT} 115200
