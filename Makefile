.DEFAULT: help

help:
	@echo "make help"

init:
	./runCommand.sh init func=$(FUNCTION) lang=$(LANG) || exit 2

test: 
	./runCommand.sh test func=$(FUNCTION) lang=$(LANG) || exit 2

run:
	./runCommand.sh run func=$(FUNCTION)