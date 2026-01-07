# run me to zopfli all the static files
# which should help on really slow connections
# but then why are you using copyparty in the first place

pk: $(addsuffix .gz, $(wildcard tl/*.js *.js *.css) \
	a/webdav-cfg.txt )
un: $(addsuffix .un, $(wildcard tl/*.gz *.gz a/*.gz))

%.gz: %
	pigz -c11 -J 34 -I 573 <$< >$@
	touch -r $< $@
	rm $<

%.un: %
	pigz -d $<
