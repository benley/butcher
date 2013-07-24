# Butcher

This repo is currently structured to be a submodule of [twitter commons][1],
and it relies on Pants to bootstrap itself.

To build it, check out commons and rename this repo to
commons/src/python/cloudscaling/. Then you can run:

    pants build src/python/cloudscaling/butcher:butcher

This emits dist/butcher.pex, which is a self-contained executable copy
of butcher and its Python dependencies.

There is also a Makefile present, and if you have [Bundler][2] (tested with
1.2, anything newer will likely work fine) installed, you can run make to
produce a deb package.

[1]: https://github.com/twitter/commons "twitter commons"
[2]: http://bundler.io/ "Bundler"
