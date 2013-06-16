# General notes and stuff

### Here is how to use the topological sort function from twitter commons:

    from twitter.common import util
    edges = networkx.to_edgelist(depgraph)
    edges = [ tuple(x[:-1]) for x in edges ]

    for deps_ready in util.topological_sort(edges):
    print deps_ready


### Some notes that came from builder.py:

- Collect sources, put them in place (hardlinks? symlinks? copies? and aufs?)
- Collect deps, put them in place.
- WHERE? Maybe in the place they came from.

buildroot directory structure to build makeself from its genrule:

    /blabla/butcher-build
      |-  /cs-common-buildenv/third_party/makeself/makeself.sh
      \-  /cs-common-buildenv/third_party/makeself/makeself-header.sh

Then it runs: $(location makeself.sh) [blahblah] makeself

makeself genrule results:

    /blabla/butcher-build
      |-  /cs-common-buildenv/third_party/makeself/makeself.sh
      |-  /cs-common-buildenv/third_party/makeself/makeself-header.sh
      \-  /cs-common-buildenv/third_party/makeself/makeself  <--- the output file

Then to build cs-lxcrun:

    /blabla/butcher-out/cs-common-buildenv/third_party/makeself/makeself <-- dep

    /blabla/butcher-build
      |-  /cs-common-buildenv/Makefile
      |-  /cs-common-buildenv/lxc/setup_lxc.sh
      |-  /cs-common-buildenv/lxc/apparmor-profile
      \-  /cs-common-buildenv/lxc/lxc-cloudscaling-ubuntu

It runs: ``$(location makeself) [blahblah] cs-lxcrun``

Results:

    /blabla/butcher-build
      |-  /cs-common-buildenv/third_party/makeself/makeself
      |-  /cs-common-buildenv/Makefile
      |-  /cs-common-buildenv/lxc/setup_lxc.sh
      |-  /cs-common-buildenv/lxc/apparmor-profile
      |-  /cs-common-buildenv/lxc/lxc-cloudscaling-ubuntu
      \-  /cs-common-buildenv/cs-lxcrun  <--- the output file
