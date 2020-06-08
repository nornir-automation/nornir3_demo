SRC=_src
DST=../

HUGO_IMAGE=nornir3_demo_hugo:latest
HUGO_VERSION=v0.72.0
DOCKER_HUGO=docker run \
	 -it \
	-v $(PWD)/docs:/src \
	-p 1313:1313 \
	$(HUGO_IMAGE)

HUGO_OPTS=--source $(SRC) --destination $(DST)
HUGO_TEST_OPTS=-D -E -F --disableFastRender --bind 0.0.0.0

.PHONY: hugo-docker-image
hugo-docker-image:
	docker build \
		--build-arg HUGO_VERSION=$(HUGO_VERSION) \
		--build-arg USER=$(shell id -un) \
		--build-arg USERID=$(shell id -u) \
		--build-arg GROUP=$(shell id -gn) \
		--build-arg GROUPID=$(shell id -g) \
		-t $(HUGO_IMAGE) \
		-f Dockerfile.hugo \
		.

.PHONY: docker-serve
docker-serve: clean
	$(DOCKER_HUGO) hugo serve \
		$(HUGO_TEST_OPTS) \
		$(HUGO_OPTS)

.PHONY: docker-gen
docker-gen: clean
	$(DOCKER_HUGO) hugo \
		$(HUGO_OPTS)

.PHONY: start
start:
	$(DOCKER_HUGO) hugo new site nornir3_demo

.PHONY: clean
clean:
	cd docs/ && \
	find -maxdepth 1 -not \(\
		-name '.*' -or \
		-name '_src' \
		\) -print0 | xargs -0  -I {} rm -rf {}
