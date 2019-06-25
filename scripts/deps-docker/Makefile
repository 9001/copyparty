self := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
vend := $(self)/../../copyparty/web/deps

all:
	service docker start
	
	docker build -t build-copyparty-deps .
	
	rm -rf $(vend)
	mkdir $(vend)

	echo "tar -cC /z dist" | \
	docker run --rm -i build-copyparty-deps:latest | \
	tar -xvC $(vend) --strip-components=1

	chown -R `stat $(self) -c %u:%g` $(vend)

sh:
	@printf "\n\033[1;31mopening a shell in the most recently created docker image\033[0m\n"
	docker run --rm -it `docker images -aq | head -n 1` /bin/bash
