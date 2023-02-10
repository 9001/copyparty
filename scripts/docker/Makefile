self := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

all:
	-service docker start
	-systemctl start docker
	
	rm -rf i
	mkdir i
	tar -cC../.. dist/copyparty-sfx.py bin/mtag | tar -xvCi
	
	docker build -t copyparty/min:latest -f Dockerfile.min .
	echo 'scale=1;'`docker save copyparty/min:latest | pigz -c | wc -c`/1024/1024 | bc

#	docker build -t copyparty/min-pip:latest -f Dockerfile.min.pip .
#	echo 'scale=1;'`docker save copyparty/min-pip:latest | pigz -c | wc -c`/1024/1024 | bc

	docker build -t copyparty/im:latest -f Dockerfile.im .
	echo 'scale=1;'`docker save copyparty/im:latest | pigz -c | wc -c`/1024/1024 | bc

	docker build -t copyparty/iv:latest -f Dockerfile.iv .
	echo 'scale=1;'`docker save copyparty/iv:latest | pigz -c | wc -c`/1024/1024 | bc

	docker build -t copyparty/ac:latest -f Dockerfile.ac .
	echo 'scale=1;'`docker save copyparty/ac:latest | pigz -c | wc -c`/1024/1024 | bc

	docker build -t copyparty/dj:latest -f Dockerfile.dj .
	echo 'scale=1;'`docker save copyparty/dj:latest | pigz -c | wc -c`/1024/1024 | bc

	docker image ls

push:
	docker push copyparty/min
	docker push copyparty/im
	docker push copyparty/iv
	docker push copyparty/ac
	docker push copyparty/dj
	docker image tag copyparty/min:latest ghcr.io/9001/copyparty-min:latest
	docker image tag copyparty/im:latest ghcr.io/9001/copyparty-im:latest
	docker image tag copyparty/iv:latest ghcr.io/9001/copyparty-iv:latest
	docker image tag copyparty/ac:latest ghcr.io/9001/copyparty-ac:latest
	docker image tag copyparty/dj:latest ghcr.io/9001/copyparty-dj:latest
	docker push ghcr.io/9001/copyparty-min:latest
	docker push ghcr.io/9001/copyparty-im:latest
	docker push ghcr.io/9001/copyparty-iv:latest
	docker push ghcr.io/9001/copyparty-ac:latest
	docker push ghcr.io/9001/copyparty-dj:latest

clean:
	-docker kill `docker ps -q`
	-docker rm   `docker ps -qa`
	-docker rmi  `docker images -a | awk '/^<none>/{print$$3}'`

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
