.DEFAULT: help

help:
	@echo "make help"

init:
	./runCommand.sh init func=$(FUNCTION) lang=$(LANG)

test: 
	./runCommand.sh test func=$(FUNCTION) lang=$(LANG)

run:
	./runCommand.sh run func=$(FUNCTION)