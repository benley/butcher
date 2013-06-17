# This is hilarious: using make to run pants to build butcher.
# Gotta bootstrap from somewhere I guess.

# Make sure this directory is at [...]/commons/src/python/cloudscaling before
# running this, and you'll probably want to make sure pants works first. The
# intent is to stop relying on pants at some point and have butcher be
# self-hosting.

VERSION=0.2.1
DEB_ITERATION=1

pants=../../../pants

all: deb

butcher.pex:
	$(pants) build butcher:butcher

butcher: butcher.pex
	mkdir -p bin
	cp ../../../dist/butcher.pex bin/butcher

deb: butcher
	fpm -f -t deb -s dir --prefix /usr -n butcher -v $(VERSION) --iteration $(DEB_ITERATION) --depends git -a native --description "Butcher build system" --deb-user root --deb-group root --url "http://pd.cloudscaling.com/codereview/gitweb?p=butcher.git" bin

.PHONY: butcher.pex
