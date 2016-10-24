
INSTANCE = default
DOCKER ?= docker

NS = civicknowledge
VERSION = latest

REPO = metatab
NAME = metatab

DOCKER ?= docker

PORTS =  -p 80

VOLUMES= -v /data

ENV =  -eVIRTUAL_HOST=$(NAME).docker1.civicknowledge.com


.PHONY: build push shell run start stop restart reload rm rmf release test

build:
	$(DOCKER) build -t $(NS)/$(REPO):$(VERSION) .

push:
	$(DOCKER) push $(NS)/$(REPO):$(VERSION)

shell:
	$(DOCKER) run --rm  -i -t $(PORTS) $(VOLUMES) $(LINKS) $(ENV) $(NS)/$(REPO):$(VERSION) /bin/bash

run:
	$(DOCKER) run --rm --name $(NAME) $(PORTS) $(VOLUMES) $(LINKS) $(ENV) $(NS)/$(REPO):$(VERSION)

logs:
	$(DOCKER) logs -f $(NAME) 

start:
	$(DOCKER) run -d --name $(NAME) $(PORTS) $(VOLUMES) $(LINKS) $(ENV) $(NS)/$(REPO):$(VERSION)

stop:
	$(DOCKER) stop $(NAME)
	
restart: stop start

reload: build rmf start

rmf:
	$(DOCKER) rm -f $(NAME)

rm:
	$(DOCKER) rm $(NAME)

release: build
	make push -e VERSION=$(VERSION)

default: build

