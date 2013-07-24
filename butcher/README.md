# Butcher

Butcher is a software build system in the spirit of [Pants][1], [Buck][2], and
[Blaze][3].

Like other similar tools, Butcher encourages the creation of small reusable
modules and focuses on improving efficiency and speed of build processes.  What
sets Butcher apart is its integration with distributed git repositories rather
than relying on large unified codebases.

Butcher uses a build cache to speed up incremental builds and avoid repeated
work. The cache stores objects based on a combined checksum (referred to in the
code and documentation as a _metahash_) of all the inputs used to produce them,
and dedupes objects by each file's own checksum. This system makes extensive use
of hardlinks, so it is beneficial for Butcher to have its various working
directories (cache, git clients, build area) on the same filesystem.

## Limitations

### General
* Builds are currently sequential, not parallel.
* Builds use the same build area until 'butcher clean' is run, which can
  potentially mask or introduce bugs.

### Cache
* Caching is keyed by metahash, but retrieval is done per-file.
* The cache does not keep checksums of individual files for verification. It
  should.
* Cache is local-only, not networked at al.

## Upcoming features
* Everything

[1]: https://github.com/twitter/commons/blob/master/src/python/twitter/pants/README.md "Pants"
[2]: http://facebook.github.io/buck/ "Buck"
[3]: http://google-engtools.blogspot.com/2011/08/build-in-cloud-how-build-system-works.html "Blaze"
