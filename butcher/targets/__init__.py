"""Target rule types."""

from twitter.common import log
from cloudscaling.butcher import error
from cloudscaling.butcher.targets.gendeb import GenDeb as gendeb
from cloudscaling.butcher.targets.genrule import GenRule as genrule
from cloudscaling.butcher.targets.filegroup import FileGroup as filegroup
from cloudscaling.butcher.targets.pkgfilegroup import PkgFileGroup as pkgfilegroup
from cloudscaling.butcher.targets.virtual import VirtualTarget as virtual


TYPE_MAP = {
    'genrule': genrule,
    'gendeb': gendeb,
    'filegroup': filegroup,
    'pkgfilegroup': pkgfilegroup,
    'virtual': virtual,
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
