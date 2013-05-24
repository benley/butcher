"""Target rule types."""

from twitter.common import log
from cloudscaling.buildy import builder
from cloudscaling.buildy import error
from .base import BaseTarget
from .gendeb import GenDeb
from .genrule import GenRule
from .pkgfilegroup import PkgFileGroup
from .unimplemented import UnimplementedTarget
from .virtual import VirtualTarget


TYPE_MAP = {
    'genrule': GenRule,
    'virtual': VirtualTarget,
    'gendeb': GenDeb,
    'pkgfilegroup': PkgFileGroup,
    }


def new(ruletype, **kwargs):
  try:
    ruleclass = TYPE_MAP[ruletype]
  except KeyError:
    raise error.InvalidRule('Unrecognized rule type: %s' % ruletype)

  try:
    return ruleclass(**kwargs)
  except TypeError as err:
    log.error('BADNESS. ruletype: %s, data: %s', ruletype, kwargs)
    raise
    #raise error.InvalidRule(
    #    '%s does not work that way.\nDetails: %s.\nData: %s' % (
    #        ruletype, err, kwargs))
