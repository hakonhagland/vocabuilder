#ROOT := $(dir $(lastword $(MAKEFILE_LIST)))
ROOT := $(shell pwd)
DOCKERDIR := $(ROOT)/docker

.PHONY: docker-image run-docker-image coverage docs mypy test flake8
.PHONY: black-check black publish-to-pypi

docker-image:
	"$(DOCKERDIR)"/build-docker.sh "$(DOCKERDIR)"

run-docker-image:
	docker run -it python-vocabuilder

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

black-check:
	black --diff --color src/ tests/

black:
	black src/ tests/

publish-to-pypi:
	poetry publish --build
