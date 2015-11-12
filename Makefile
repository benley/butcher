# This is hilarious: using make to run pants to build butcher.
# Gotta bootstrap from somewhere I guess.

# Make sure pants works before running this.  The intent is to stop relying on
# pants at some point and have butcher be self-hosting.

VERSION = $(shell tools/python_getvar.py src/butcher/BUILD BUTCHER_VERSION)
DEB_ITERATION = 1
ARCH ?= amd64

pants ?= pants
SHELL=/bin/bash
deb_filename = dist/butcher_$(VERSION)-$(DEB_ITERATION)_$(ARCH).deb

all: deb

dist/butcher.pex:
	$(pants) build src/butcher:butcher

# TODO: after bootstrapping butcher, use it to build its own deb.
deb: $(deb_filename)

$(deb_filename): dist
	dist/deb/var/lib/butcher/bin/fpm \
	    -p $(deb_filename) \
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
	    --url "https://github.com/benley/butcher" \
	    -C dist/deb \
	    usr/ var/

bundle:
	mkdir -p dist/deb/var/lib/butcher
	bundle package
	bundle install --local --standalone --path=dist/deb/var/lib/butcher \
		--binstubs=dist/deb/var/lib/butcher/bin --deployment
	install -m 0644 Gemfile Gemfile.lock dist/deb/var/lib/butcher

clean:
	-rm -rf dist/

dist: dist/butcher.pex bundle
	mkdir -p dist/deb/{usr/bin,/var/lib/butcher/cache}
	install -m 0755 dist/butcher.pex dist/deb/usr/bin/butcher

.PHONY: clean dist bundle
