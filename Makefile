all: zip

zip:
	rm -f plugin.zip plugin.rbz
	zip -r plugin.zip .
	cp plugin.zip plugin.rbz
