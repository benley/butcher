"""Target rule types."""

from twitter.common import log
from cloudscaling.buildy import error
from .base import BaseTarget
from .gendeb import GenDeb
from .genrule import GenRule
from .filegroup import FileGroup
from .pkgfilegroup import PkgFileGroup
from .unimplemented import UnimplementedTarget
from .virtual import VirtualTarget


TYPE_MAP = {
    'genrule': GenRule,
    'gendeb': GenDeb,
    'filegroup': FileGroup,
    'pkgfilegroup': PkgFileGroup,
    'virtual': VirtualTarget,
    }


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
