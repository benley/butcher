"""pkgfilegroup targets"""

from cloudscaling.buildy import buildtarget
from cloudscaling.buildy.targets import base
from twitter.common import log

class PkgFileGroupBuilder(base.BaseBuilder):
  ruletype = 'pkgfilegroup'

  def build(self):
    pass

class PkgFileGroup(base.BaseTarget):
  rulebuilder = PkgFileGroupBuilder
  ruletype = 'pkgfilegroup'

  required_params = ['name', 'prefix', 'srcs']
  optional_params = {
      'attr': None,
      'section': None,  # one of ('', 'doc', 'config')
      'strip_prefix': None,
      }

  @property
  def output_files(self):
    """Returns the list of output files from this rule."""
    outs = []
    for dep in self.subgraph.successors(self.address):
      outs.extend(self.subgraph.node[dep]['target_obj'].output_files)
    log.debug('OUTSSSSSS: %s', outs)
    log.warn('This is not going to work yet.')
    # The paths are relative to each rule's address, but what we need is ...
    # not that. Need them relative to buildroot, I think.
    return outs

  @property
  def composed_deps(self):
    return [ buildtarget.BuildTarget(x) for x in self.params['srcs'] ]

  @property
  def source_files(self):
    """pkgfilegroup doesn't exactly have sources.

    This rule's srcs are actually handled as dependencies, which are then
    collected during the build phase.
    """
    return None
