#ROOT := $(dir $(lastword $(MAKEFILE_LIST)))
ROOT := $(shell pwd)
DOCKERDIR := $(ROOT)/docker

.PHONY: docker-image run-docker-image coverage docs mypy test flake8

docker-image:
	docker build -t python-vocabuilder $(DOCKERDIR)

run-docker-image:
	docker run -v "$(ROOT)":/root/vocabuilder -it python-vocabuilder

coverage:
	coverage run -m pytest tests
	coverage report -m

docs:
	cd "$(ROOT)"/docs && make html

mypy:
	mypy src/ tests/

test:
	pytest tests/

flake8:
	flake8 src/ tests/
