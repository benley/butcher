Butcher
=======

**OBSOLETE**: you don't want to use this. Use `Bazel <https://bazel.io/>`_
instead.

This was a project I worked on in 2013 at Cloudscaling_. The goal was to have a
build system for projects spanning multiple source repositories, with a rule
language and operational semantics similar to `Bazel's BUILD files`_ and an
emphasis on correctness and repeatability. Bazel was not yet released to the
public at that time, and I was not aware of any other build systems that were
neatly integrated with a version control system, or which directly addressed
cross-project source dependencies, so I started afresh.

Butcher makes various assumptions that make it impractical to use as-is:

- Assumes that all your sources are in git repositories
- Assumes all your git repositories share the same base url, unless you map
  them all to URLs with ``--map_repo``
- Assumes that all the projects you want to build have butcher-style
  BUILD files in their source repo

I was a relatively inexperienced programmer back then, so Butcher is also rife
with design decisions that I would make very differently now, were I to start a
project like this again. Nevertheless, I did learn a lot from this project, and
Butcher was quite useful as an internal build tool at Cloudscaling_ for our
various projects.

Butcher target addresses are very much like Bazel's `target labels`_ with an
additional syntax for specifying a git ref in a remote repository:

::

    //repo_name[git_ref]/dir/in/project:target

If the ``[git_ref]`` part of an address is omitted, butcher will use the
value specified with ``--default_ref`` on the commandline. By default
that is ``HEAD``, which usually implies ``master`` in a remote git
repository.

To associate any ``//repo_name`` with an actual git repository URL, use
another commandline flag: ``--map_repo=<repo_name>:<git@url.here:etc/etc>``.

Bazel has a much better and more thorough design for working with remote
project repositories; compare to the bazel docs about `working with external
dependencies`_ for more information.

There are a few types of build rules implemented in Butcher. Most of these have
reasonably good documentation as docstrings in their implementation classes,
and it should be fairly obvious how one might implement additional rule types
after looking through a few of the existing rules.

- genrule_ runs arbitrary shell commands as a build step that produces the
  stated outputs.  This includes a Makefile-like sublanguage for cmdline
  expansion when defining targets (`see the source for details
  <https://github.com/benley/butcher/blob/master/butcher/targets/genrule.py#L64>`_)

- gendeb_ packages the output of other rules into Debian packages. This
  assumes that you have fpm_ installed locally, which is not ideal.

- filegroup_ collects files (sources, or outputs of other rules)
  and gives them a collective name, which can then be used as an input to
  other rules.

- pkgfilegroup_ is similar to filegroup, but it adds metadata that is
  specifically useful as inputs to rules like gendeb, and a map for setting
  file ownership and permissions of the files in the eventual output package.

- pkg_symlink_ appears to be unfinished, but it should be a way of putting a
  symlink in a gendeb package.

- virtual_ targets can be used to group a bunch of other targets together as a
  single buildable address.

.. _genrule: https://github.com/benley/butcher/blob/master/butcher/targets/genrule.py#L177
.. _gendeb: https://github.com/benley/butcher/blob/master/butcher/targets/gendeb.py#L222
.. _fpm: https://github.com/jordansissel/fpm
.. _filegroup: https://github.com/benley/butcher/blob/master/butcher/targets/filegroup.py#L15
.. _pkgfilegroup: https://github.com/benley/butcher/blob/master/butcher/targets/pkgfilegroup.py#L38
.. _pkg_symlink: https://github.com/benley/butcher/blob/master/butcher/targets/pkg_symlink.py#L10
.. _virtual: https://github.com/benley/butcher/blob/master/butcher/targets/virtual.py#L18

Butcher's original project README follows below:

--------------

Butcher is a software build system in the spirit of Pants_, Buck_, and Blaze_.

Like other similar tools, Butcher encourages the creation of small reusable
modules and focuses on improving efficiency and speed of build processes. What
sets Butcher apart is its integration with distributed git repositories rather
than relying on large unified codebases.

Butcher uses a build cache to speed up incremental builds and avoid repeated
work. The cache stores objects based on a combined checksum (referred to in the
code and documentation as a *metahash*) of all the inputs used to produce them,
and dedupes objects by each file's own checksum. This system makes extensive
use of hardlinks, so it is beneficial for Butcher to have its various working
directories (cache, git clients, build area) on the same filesystem.

Limitations
-----------

General
~~~~~~~

-  Builds are currently sequential, not parallel.
-  Builds use the same build area until 'butcher clean' is run, which
   can potentially mask or introduce bugs.

Cache
~~~~~

-  Caching is keyed by metahash, but retrieval is done per-file.
-  The cache does not keep checksums of individual files for
   verification. It should.
-  Cache is local-only, not networked at all.

Upcoming features
-----------------

-  Everything

.. _Bazel's BUILD files: https://www.bazel.io/versions/master/docs/build-ref.html
.. _Cloudscaling: https://cloudscaling.com/
.. _target labels: https://www.bazel.io/versions/master/docs/build-ref.html#labels
.. _working with external dependencies: https://www.bazel.io/versions/master/docs/external.html
.. _Pants: http://pantsbuild.github.io/
.. _Buck: http://facebook.github.io/buck/
.. _Blaze: http://google-engtools.blogspot.com/2011/08/build-in-cloud-how-build-system-works.html
