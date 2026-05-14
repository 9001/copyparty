self := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

.PHONY: i min im ac iv dj clean hclean purge sh

all: ac

i:
	rm -rf i
	mkdir i
	tar -cC../../dist    copyparty-sfx.py          | tar -xvCi
	tar -cC../..         bin/mtag                  | tar -xvCi
#   # use stock ffmpeg because ./base/Makefile requires podman;
#   # beware: https://github.com/9001/copyparty/blob/hovudstraum/docs/bad-codecs.md
	touch i/stock_ffmpeg

min: i
	docker build -t copyparty/min:latest -f Dockerfile.min .

im: i
	docker build -t copyparty/im:latest -f Dockerfile.im .

ac: i
	docker build -t copyparty/ac:latest -f Dockerfile.ac --build-arg ADD_PKG=ffmpeg .

iv: i
	docker build -t copyparty/iv:latest -f Dockerfile.iv --build-arg ADD_PKG=ffmpeg .

dj: i
	docker build -t copyparty/dj:latest -f Dockerfile.dj --build-arg ADD_PKG=ffmpeg .

clean:
	-docker kill `docker ps -q`
	-docker rm   `docker ps -qa`
	-docker rmi -f `docker images -a | awk '/<none>/{print$$3}'`

hclean:
	-docker kill `docker ps -q`
	-docker rm   `docker ps -qa`
	-docker rmi  `docker images -a | awk '!/^alpine/&&NR>1{print$$3}'`

purge:
	-docker kill `docker ps -q`
	-docker rm   `docker ps -qa`
	-docker rmi  `docker images -qa`

sh:
	@printf "\n\033[1;31mopening a shell in the most recently created docker image\033[0m\n"
	docker run --rm -it --entrypoint /bin/ash `docker images -aq | head -n 1`
