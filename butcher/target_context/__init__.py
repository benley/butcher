"""Importable context to be used inside BUILD files."""

# Things that don't go into the build context:
from twitter.common import log

# Breaking my own rule of only importing whole modules in order to set up a
# sublanguage parser. This is an unusual case.

# Butcher targets:
from butcher.targets.gendeb import GenDeb as gendeb
from butcher.targets.genrule import GenRule as genrule
from butcher.targets.filegroup import FileGroup as filegroup
from butcher.targets.pkgfilegroup import PkgFileGroup as pkgfilegroup
from butcher.targets.pkg_symlink import PkgSymlink as pkg_symlink
#from butcher.targets.virtual import VirtualTarget as virtual

# Other useful things to have in there:
from butcher.util import glob

__all__ = ['gendeb', 'genrule', 'filegroup', 'pkgfilegroup', 'pkg_symlink',
           'glob', 'globs', 'rglobs']


def globs(*args):
    """Deprecated: use glob() instead."""
    # TODO: use the warnings module to issue deprecation warnings.
    log.warn('globs() is deprecated; please use glob() instead.')
    return glob(*args)


def rglobs(*args):
    """Deprecated: use glob() instead."""
    log.warn('rglobs() is deprecated; please use glob() instead.')
    return glob(*args)
