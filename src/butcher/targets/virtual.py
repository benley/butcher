"""Virtual (deps only) targets"""

from butcher.targets import base
from butcher import error
from twitter.common import log


class VirtualTargetBuilder(base.BaseBuilder):
    """Builder for virtual (deps only) rules."""

    def collect_srcs(self):
        pass

    def build(self):
        log.debug('[%s] nothing to build.', self.rule.address)


class VirtualTarget(base.BaseTarget):
    """Virtual (deps only) rule."""

    rulebuilder = VirtualTargetBuilder
    ruletype = 'virtual'

    required_params = [('name', str), ('deps', list)]
    optional_params = []

    def __init__(self, **kwargs):
        base.BaseTarget.__init__(self, **kwargs)
        if not kwargs['deps']:
            raise error.InvalidRule(
                'Virtual rules with no deps make no sense.')
        log.debug('New virtual target: %s, deps: %s',
                  kwargs['name'], kwargs['deps'])

    @property
    def output_files(self):
        """Returns all output files from all of the current module's rules."""
        for dep in self.subgraph.successors(self.address):
            dep_rule = self.subgraph.node[dep]['target_obj']
            for out_file in dep_rule.output_files:
                yield out_file
