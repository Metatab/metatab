
NS = civicknowledge.com
VERSION = latest

REPO = tox
NAME = tox
INSTANCE = default
DOCKER ?= docker

.PHONY: test build push shell run start stop restart reload rm rmf release
CWD = $(notdir $(shell pwd))

VOLUMES=-v $(abspath $(CWD)/../../..):/code

test:
	$(DOCKER) run --rm --name $(NAME) $(PORTS) $(VOLUMES) $(ENV) $(NS)/$(REPO):$(VERSION) tox

build:
	$(DOCKER) build -t $(NS)/$(REPO):$(VERSION) .

push:
	$(DOCKER) push $(NS)/$(REPO):$(VERSION)

shell:
	$(DOCKER) run --rm -i -t $(PORTS) $(VOLUMES) $(ENV) $(NS)/$(REPO):$(VERSION) /bin/bash

logs:
	$(DOCKER) logs -f $(NAME) 

rmf:
	$(DOCKER) rm -f $(NAME)

rm:
	$(DOCKER) rm $(NAME)

release: build
	make push -e VERSION=$(VERSION)

default: test