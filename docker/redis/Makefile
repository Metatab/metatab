
DOCKER ?= docker

NAME = numbering-redis

REPO = redis
VERSION = alpine

PORTS =  -p 6379:6379

RUN_OPTS = --appendonly yes

#VOLUMES= -v /share/CACHEDEV1_DATA/docker/docker-fs:/var/docker-fs
VOLUMES= 
ENV =
LINKS = --link $(NAME):redis # Only for CLI and shells

.PHONY: build push shell run start stop restart reload rm rmf release

build:
	$(DOCKER) build -t $(REPO):$(VERSION) .

push:
	$(DOCKER) push $(REPO):$(VERSION)

shell:
	$(DOCKER) run --rm -i -t $(LINKS) $(ENV) $(REPO):$(VERSION) /bin/bash

cli:
	$(DOCKER) run --rm -i -t $(LINKS) $(ENV) $(REPO):$(VERSION) redis-cli -h redis -p 6379

#cli:
#    $(DOCKER) run --rm -i -t $(LINKS) $(PORTS) $(VOLUMES) $(ENV) $(REPO):$(VERSION) redis-cli -h redis -p 6379

run:
	$(DOCKER) run --rm --name $(NAME)  $(PORTS) $(VOLUMES) $(ENV) $(REPO):$(VERSION) $(RUN_OPTS)

logs:
	$(DOCKER) logs -f $(NAME) 

start:
	$(DOCKER) run -d --name $(NAME) $(PORTS) $(VOLUMES) $(ENV) $(REPO):$(VERSION) $(RUN_OPTS)

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