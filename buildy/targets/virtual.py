"""Virtual (deps only) targets"""

from . import BaseTarget
from .base import BaseBuilder
from twitter.common import log


class VirtualTargetBuilder(BaseBuilder):

  def collect_srcs(self):
    pass


class VirtualTarget(BaseTarget):

  rulebuilder = VirtualTargetBuilder
  ruletype = 'virtual'

  required_params = ['name', 'deps']
  optional_params = {}

  def __init__(self, **kwargs):
    BaseTarget.__init__(self, **kwargs)
    log.debug('New virtual target: %s, deps: %s',
              kwargs['name'], kwargs['deps'])
