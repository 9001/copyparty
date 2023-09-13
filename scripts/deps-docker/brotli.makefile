all: $(addsuffix .br, $(wildcard prism* easymde*))

%.br: %
	brotli -jZ $<
