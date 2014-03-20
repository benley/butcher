"""Target rule types."""

from twitter.common import log
from cloudscaling.butcher import error
from cloudscaling.butcher.targets import gendeb
from cloudscaling.butcher.targets import genrule
from cloudscaling.butcher.targets import filegroup
from cloudscaling.butcher.targets import pkgfilegroup
from cloudscaling.butcher.targets import pkg_symlink
from cloudscaling.butcher.targets import virtual

TYPE_MAP = {
    'genrule': genrule.GenRule,
    'gendeb': gendeb.GenDeb,
    'filegroup': filegroup.FileGroup,
    'pkgfilegroup': pkgfilegroup.PkgFileGroup,
    'virtual': virtual.VirtualTarget,
    }

__all__ = [
    'genrule',
    'gendeb',
    'filegroup',
    'pkgfilegroup',
    ]


def new(ruletype, **kwargs):
  """Instantiate a new build rule based on kwargs.

  Appropriate args list varies with rule type.
  Minimum args required:
    [... fill this in ...]
  """
  try:
    ruleclass = TYPE_MAP[ruletype]
  except KeyError:
    raise error.InvalidRule('Unrecognized rule type: %s' % ruletype)

  try:
    return ruleclass(**kwargs)
  except TypeError:
    log.error('BADNESS. ruletype: %s, data: %s', ruletype, kwargs)
    raise
    #raise error.InvalidRule(
    #    '%s does not work that way.\nDetails: %s.\nData: %s' % (
    #        ruletype, err, kwargs))
