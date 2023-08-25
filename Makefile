#ROOT := $(dir $(lastword $(MAKEFILE_LIST)))
ROOT := $(shell pwd)
DOCKERDIR := $(ROOT)/docker

.PHONY: docker-image run-docker-image

docker-image:
	docker build -t python-vocabuilder $(DOCKERDIR)

run-docker-image:
	docker run -v "$(ROOT)":/root/vocabuilder -it python-vocabuilder
