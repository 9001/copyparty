all: $(addsuffix .gz, $(wildcard *.js *.css))

%.gz: %
	pigz -11 -I 2048 $<

# pigz -11 -J 34 -I 100 -F < $< > $@.first
