.DEFAULT: help
help:
	@echo "make help"
	@echo "    display this help statement"
	@echo "make test"
	@echo "    run pytest unit tests"
	@echo "make build-layer"
	@echo "    build new version of AWS Lambda Layer and deploy to AWS"
	@echo "    select branch to build with as BRANCH=[branch_name]
	@echo "make rebuild-docker"
	@echo "    rebuild docker image with supplied keys at the provided name"
	@echo "    This should use the following variables:"
	@echo "    ACCESS_KEY=[aws_access_key]"
	@echo "    SECRET_KEY=[aws_secret_access_key]"
	@echo "    REGION=[aws_region]"
	@echo "make lint"
	@echo "    lint package with flake8"

test:
	pytest

ifeq ($(BRANCH),)
BRANCH = master
endif
build-layer:
	@echo "Building AWS Layer from Branch: $(BRANCH)
	docker run -e GIT_URL=git+https://github.com/NYPL/sfr-db-core.git@$(BRANCH)#egg=sfrCore -e LAYER_NAME=sfr-db-core-python-36-37-dev sfrcore

rebuild-docker:
	docker build -t sfrcore --build-arg accesskey=$(ACCESS_KEY) --build-arg secretkey=$(SECRET_KEY) --build-arg region=$(REGION) sfrCore

lint:
	flake8
