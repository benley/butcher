"""Dealing with actually executing builds."""

import os
from twitter.common import app
from twitter.common import log

app.add_option('--build_root', dest='build_root',
               help='Base directory in which builds will be done.',
               default='/var/lib/butcher/build_root')

# TODO: this is dumb.

def BuildRoot(directory=None):
  if directory:
    buildroot = directory
  else:
    buildroot = app.get_options().build_root
  if not os.path.exists(buildroot):
    os.makedirs(buildroot)
  log.info('Buildroot: %s', buildroot)
  return buildroot


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
