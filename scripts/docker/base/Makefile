self := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))


all:
# build all outdated
	bash verchk.sh


ff:
# legally comfy
	/usr/bin/time ./build-no265.sh img


zlib:
# 	build zlib-ng from source so we know how the sausage was made
#	(still only doing the archs which are officially supported/tested)

	podman build --arch amd64 -t localhost/cpp-zlibng-amd64:latest -f Dockerfile.zlibng .
	podman run --arch amd64 --rm --log-driver=none -i localhost/cpp-zlibng-amd64:latest tar -cC/z whl | tar -xv

	podman build --arch arm64 -t localhost/cpp-zlibng-amd64:latest -f Dockerfile.zlibng .
	podman run --arch arm64 --rm --log-driver=none -i localhost/cpp-zlibng-amd64:latest tar -cC/z whl | tar -xv


sh:
	@printf "\n\033[1;31mopening a shell in the most recently created docker image\033[0m\n"
	docker run --rm -it --entrypoint /bin/ash `docker images -aq | head -n 1`
