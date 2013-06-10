<!-- vim: set wrap linebreak nolist tw=0 wrapmargin=0: -->
# Butcher

Butcher is a software build system in the spirit of [Pants][1], [Buck][2], and [Blaze][3].

Like other similar tools, Butcher encourages the creation of small reusable modules and focuses on improving efficiency and speed of build processes.  What sets Butcher apart is its integration with distributed git repositories rather than relying on large unified codebases.

[1]: https://github.com/twitter/commons/blob/master/src/python/twitter/pants/README.md "Pants"
[2]: http://facebook.github.io/buck/ "Buck"
[3]: http://google-engtools.blogspot.com/2011/08/build-in-cloud-how-build-system-works.html "Blaze"

## Limitations

### General
* Builds are currently sequential, not parallel.
* Builds use the same build area until 'butcher clean' is run, which can potentially mask or introduce bugs.

### Cache
* Caching is keyed by metahash, but retrieval is done per-file.
* Cache does not de-dupe stored objects, and it trivially could.
* Relatedly, the cache does not keep checksums of individual files for verification. It should.
* Cache is local-only, not networked at al.

## Upcoming features

