# Butcher

*OBSOLETE: you don't want to use this.  Use [Bazel][4] instead.*

This was a project I worked on in 2013 at a now-defunct startup.  The goal was to have a build system for projects spanning multiple source repositories, with a rule language and operational semantics similar to [Bazel's BUILD files][5].  Bazel was not yet released to the public at that time, and I was not aware of any other build systems that were neatly integrated with a version control system, or which directly addressed cross-project source dependencies, so I started afresh.

Butcher makes various assumptions that make it impractical to use as-is:
- Assumes that all your source is in a git repo
- Assumes all your git repositories share the same base url
- Assumes that all the projects you want to build have butcher-style BUILD files in their source repo

I was a relatively inexperienced programmer back then, so Butcher is also rife with design decisions that I would make very differently now, were I to start a project like this again.  Nevertheless, I did learn a lot from this project, and Butcher was very useful as an internal build tool at [Cloudscaling][https://cloudscaling.com/] for our various projects at the time.

Butcher target addresses are very much like Bazel's [target labels][6], with an additional syntax for specifying a git ref in a remote repository:

```
//repo_name[git_ref]/dir/in/project:target
```

If the `[git_ref]` part of an address is omitted, butcher will use the value specified with `--default_ref` on the commandline. By default that is `HEAD`, which usually implies `master` in a remote git repository.

To associate any `//repo_name` with an actual git repository URL, use another commandline flag: `--map_repo=<repo_name>:<git@url.here:etc/etc>`.

Bazel has a much better and more thorough design for working with remote project repositories; compare to the bazel docs about [working with external dependencies][7] for more information.

Butcher's original project README follows below:

------------

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
* Cache is local-only, not networked at all.

## Upcoming features
* Everything

[1]: https://github.com/twitter/commons/blob/master/src/python/twitter/pants/README.md "Pants"
[2]: http://facebook.github.io/buck/ "Buck"
[3]: http://google-engtools.blogspot.com/2011/08/build-in-cloud-how-build-system-works.html "Blaze"
[4]: https://www.bazel.io/ "Bazel"
[5]: https://www.bazel.io/versions/master/docs/build-ref.html "Bazel's BUILD files"
[6]: https://www.bazel.io/versions/master/docs/build-ref.html#labels "Bazel target labels"
[7]: https://www.bazel.io/versions/master/docs/external.html
