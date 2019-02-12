all: zip

zip:
	rm -f plugin.zip plugin.rbz
	zip -x *.git* -x *Makefile* -r plugin.zip .
	cp plugin.zip plugin.rbz
