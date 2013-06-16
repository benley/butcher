"""Importable context to be used inside BUILD files."""

# Breaking my own rule of only importing whole modules in order to set up a
# sublanguage parser. This is an unusual case.

# Butcher targets:
from cloudscaling.butcher.targets.gendeb import GenDeb as gendeb
from cloudscaling.butcher.targets.genrule import GenRule as genrule
from cloudscaling.butcher.targets.filegroup import FileGroup as filegroup
from cloudscaling.butcher.targets.pkgfilegroup import PkgFileGroup as pkgfilegroup
from cloudscaling.butcher.targets.pkg_symlink import PkgSymlink as pkg_symlink
#from cloudscaling.butcher.targets.virtual import VirtualTarget as virtual

# Other useful things to have in there:
from glob import glob
from cloudscaling.butcher.util import globs, rglobs
