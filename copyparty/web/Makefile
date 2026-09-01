# run me to zopfli all the static files
# which should help on really slow connections
# but then why are you using copyparty in the first place

pk: $(addsuffix .gz, $(wildcard tl/*.js *.js *.css) \
	a/webdav-cfg.txt )
un: $(addsuffix .un, $(wildcard tl/*.gz *.gz a/*.gz))

tl/%.js.gz: tl/%.js
	sh Makefile.s1 <$< | pigz -c11 -J 34 -I 573 >$@
	pigz -dc <$@ | grep -q ^Ls
	touch -r $< $@
	rm $<

%.gz: %
	pigz -c11 -J 34 -I 573 <$< >$@
	touch -r $< $@
	rm $<

%.un: %
	pigz -d $<
