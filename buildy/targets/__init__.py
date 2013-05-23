"""Target rule types."""

from twitter.common import log
from cloudscaling.buildy import error
from .base import BaseTarget
from .genrule import GenRule


class UnimplementedTarget(BaseTarget):
  ruletype = 'UNKNOWN'

  def __init__(self, name, *args, **kwargs):
    log.warn('New Unimplemented %s target: name=%s, %s, %s',
             self.ruletype, name, args, kwargs)


class GenDeb(UnimplementedTarget):
  ruletype = 'gendeb'


class PkgFileGroup(UnimplementedTarget):
  ruletype = 'pkgfilegroup'


class VirtualTarget(BaseTarget):
  def __init__(self, name, deps=None):
    self.name = name
    if deps:
      self.deps = tuple(deps)
    log.debug('New virtual target: %s, deps: %s', name, deps)


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
