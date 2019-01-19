all: zip

zip:
	rm -f plugin.zip plugin.rbz
	zip --exclude .git/ -r plugin.zip .
	cp plugin.zip plugin.rbz
