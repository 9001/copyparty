all: $(addsuffix .br, $(wildcard easymde*))

%.br: %
	brotli -jZ $<
