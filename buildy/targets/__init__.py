"""Target rule types."""

from twitter.common import log
from cloudscaling.buildy import error
from . import base
from . import genrule



class DoNothingRule(base.BaseTarget):
  def __init__(self, name, *args, **kwargs):
    log.warn('Unimplemented rule invoked: name=%s, %s, %s', name, args, kwargs)


TYPE_MAP = {
    'genrule': genrule.GenRule,
    'virtual': base.BaseTarget,
    'gendeb': DoNothingRule,
    'pkgfilegroup': DoNothingRule,
    }


def new(ruletype, *args, **kwargs):
  try:
    ruleclass = TYPE_MAP[ruletype]
  except KeyError:
    raise error.InvalidRule('Unrecognized rule type: %s' % ruletype)

  try:
    return ruleclass(**kwargs)
  except TypeError as err:
    raise
    #raise error.InvalidRule(
    #    '%s does not work that way.\nDetails: %s.\nData: %s' % (
    #        ruletype, err, kwargs))
