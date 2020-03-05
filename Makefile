.DEFAULT: help

help:
	@echo "make help"

test: 
	./runCommand.sh $(FUNCTION)