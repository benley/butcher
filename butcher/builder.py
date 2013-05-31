# There used to be code here, but it got moved. Now it's just notes.

# Collect sources, put them in place (hardlinks? symlinks? copies? and aufs?)
# Collect deps, put them in place.
# - WHERE? Maybe in the place they came from.

# buildroot directory structure to build makeself from its genrule:
# /blabla/butcher-build
#   |-  /cs-common-buildenv/third_party/makeself/makeself.sh
#   \-  /cs-common-buildenv/third_party/makeself/makeself-header.sh

# Then it runs: $(location makeself.sh) [blahblah] makeself

# makeself genrule results:
# /blabla/butcher-build
#   |-  /cs-common-buildenv/third_party/makeself/makeself.sh
#   |-  /cs-common-buildenv/third_party/makeself/makeself-header.sh
#   \-  /cs-common-buildenv/third_party/makeself/makeself  <--- the output file

# Then to build cs-lxcrun:
# /blabla/butcher-out/cs-common-buildenv/third_party/makeself/makeself <-- dep

# /blabla/butcher-build
#   |-  /cs-common-buildenv/Makefile
#   |-  /cs-common-buildenv/lxc/setup_lxc.sh
#   |-  /cs-common-buildenv/lxc/apparmor-profile
#   \-  /cs-common-buildenv/lxc/lxc-cloudscaling-ubuntu

# It runs: $(location makeself) [blahblah] cs-lxcrun
# Results:
# /blabla/butcher-build
#   |-  /cs-common-buildenv/third_party/makeself/makeself
#   |-  /cs-common-buildenv/Makefile
#   |-  /cs-common-buildenv/lxc/setup_lxc.sh
#   |-  /cs-common-buildenv/lxc/apparmor-profile
#   |-  /cs-common-buildenv/lxc/lxc-cloudscaling-ubuntu
#   \-  /cs-common-buildenv/cs-lxcrun  <--- the output file
