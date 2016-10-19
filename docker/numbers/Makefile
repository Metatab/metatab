
INSTANCE = default
DOCKER ?= docker

NS = civicknowledge
VERSION = latest

REPO = numbers
NAME = numbers

DOCKER ?= docker

PORTS =  -p 80

VOLUMES= -v /data


# UNREGISTERED_KEY ?= fe78d179-8e61-4cc5-ba7b-263d8d3602b9
# REGISTERED_KEY ?= fe78d179-8e61-4cc5-ba7b-263d8d3602ba
# AUTHORITATIVE_KEY ?= fe78d179-8e61-4cc5-ba7b-263d8d3602bb
# ENV =  -eUNREGISTERED_KEY=$(UNREGISTERED_KEY) -eREGISTERED_KEY=$(REGISTERED_KEY) \
-eAUTHORITATIVE_KEY=$(AUTHORITATIVE_KEY) -eVIRTUAL_HOST=$(NAME).docker1.civicknowledge.com

ENV = -eVIRTUAL_HOST=$(NAME).docker1.civicknowledge.com

LINKS = --link numbering-redis:redis

.PHONY: build push shell run start stop restart reload rm rmf release

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