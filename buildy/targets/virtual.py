"""Virtual (deps only) targets"""

from cloudscaling.buildy.targets import base
from cloudscaling.buildy import error
from twitter.common import log


class VirtualTargetBuilder(base.BaseBuilder):

  def collect_srcs(self):
    pass

  def build(self):
    log.debug('[%s] nothing to build.', self.rule.address)


class VirtualTarget(base.BaseTarget):

  rulebuilder = VirtualTargetBuilder
  ruletype = 'virtual'

  required_params = ['name', 'deps']
  optional_params = {}

  def __init__(self, **kwargs):
    base.BaseTarget.__init__(self, **kwargs)
    if not kwargs['deps']:
      raise error.InvalidRule('Virtual rules with no deps make no sense.')
    log.debug('New virtual target: %s, deps: %s',
              kwargs['name'], kwargs['deps'])

  @property
  def output_files(self):
    return None
