# Butcher

This repo is currently structured to be a submodule of [twitter commons][1],
and it relies on Pants to bootstrap itself.

To build it, check out commons and rename this repo to
commons/src/python/cloudscaling/. Then you can run:

    pants build src/python/cloudscaling/butcher:butcher

This emits dist/butcher.pex, which is a self-contained executable copy
of butcher and its Python dependencies.

[1]: https://github.com/twitter/commons "twitter commons"
