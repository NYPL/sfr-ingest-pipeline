.DEFAULT: help

help:
	@echo "make help"

test: 
	./runCommand.sh test $(FUNCTION)

run:
	./runCommand.sh run $(FUNCTION)