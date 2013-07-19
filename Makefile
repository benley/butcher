# This is hilarious: using make to run pants to build butcher.
# Gotta bootstrap from somewhere I guess.

# Make sure this directory is at [...]/commons/src/python/cloudscaling before
# running this, and you'll probably want to make sure pants works first. The
# intent is to stop relying on pants at some point and have butcher be
# self-hosting.

VERSION = 0.2.8
DEB_ITERATION = 1
ARCH ?= amd64

required_fpm_version = 0.4.37
gem_source = "http://gems.cloudscaling.com"

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
	fpm -f -t deb -s dir \
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

fpm: gems/fpm-$(required_fpm_version).gem

gems/fpm-0.4.37.gem:
	cd gems; ../tools/gem-fetch-dependencies.rb fetch fpm \
	    -v '=$(required_fpm_version)' -y \
	    --source $(gem_source)

clean:
	rm gems/*.gem bin/butcher
	rm -rf dist/

dist: butcher fpm
	mkdir -p dist/{usr/bin,/var/lib/butcher/cache}
	install -m 0755 bin/butcher dist/usr/bin/butcher
	install -m 0644 gems/*.gem dist/var/lib/butcher/cache
	GEM_HOME=$(@D)/dist/var/lib/butcher \
	    GEM_PATH=$(@D)/dist/var/lib/butcher \
	    gem install fpm -v '=$(required_fpm_version)' --no-ri --no-rdoc \
	        --clear-sources --conservative

.PHONY: butcher.pex clean dist
