# This is hilarious: using make to run pants to build butcher.
# Gotta bootstrap from somewhere I guess.

# Make sure this directory is at [...]/commons/src/python/cloudscaling before
# running this, and you'll probably want to make sure pants works first. The
# intent is to stop relying on pants at some point and have butcher be
# self-hosting.

VERSION = 0.2.9
DEB_ITERATION = 1
ARCH ?= amd64

pants ?= pants
SHELL=/bin/bash
deb_filename = butcher_$(VERSION)-$(DEB_ITERATION)_$(ARCH).deb

all: deb

butcher.pex:
	cd ../../../; $(pants) build src/python/cloudscaling/butcher:butcher

butcher: butcher.pex
	mkdir -p bin
	cp ../../../dist/butcher.pex bin/butcher

# TODO: after bootstrapping butcher, use it to build its own deb.
deb: $(deb_filename)

$(deb_filename): dist
	dist/var/lib/butcher/bin/fpm \
	    -f -t deb -s dir \
	    --prefix / \
	    -n butcher \
	    -v $(VERSION) \
	    --iteration $(DEB_ITERATION) \
	    --depends git \
	    --depends 'ruby1.9.3' \
	    --depends 'python2.7' \
	    -a native \
	    --description "Butcher build system" \
	    --deb-user root \
	    --deb-group root \
	    --url "http://pd.cloudscaling.com/codereview/gitweb?p=butcher.git" \
	    -C dist \
	    usr/ var/

bundle:
	mkdir -p dist/var/lib/butcher
	bundle package
	bundle install --local --standalone --path=dist/var/lib/butcher \
		--binstubs=dist/var/lib/butcher/bin --deployment
	install -m 0644 Gemfile Gemfile.lock dist/var/lib/butcher

clean:
	-rm -f bin/butcher
	-rm -rf dist/

dist: butcher bundle
	mkdir -p dist/{usr/bin,/var/lib/butcher/cache}
	install -m 0755 bin/butcher dist/usr/bin/butcher

.PHONY: butcher.pex clean dist bundle
