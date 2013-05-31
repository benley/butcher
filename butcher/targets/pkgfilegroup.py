"""pkgfilegroup targets

ONLY PARTIALLY IMPLEMENTED!

Works so far:
  - collects output files from rules given in srcs, emits them as its own
    outputs

Not yet implemented:
  - set attributes
  - put output files in the prefixed directory (should this happen here?)
"""

from cloudscaling.butcher import address
from cloudscaling.butcher.targets import base


class PkgFileGroupBuilder(base.BaseBuilder):
  """Builder for pkgfilegroup"""
  ruletype = 'pkgfilegroup'

  def build(self):
    pass


class PkgFileGroup(base.BaseTarget):
  """pkgfilegroup rule"""
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
    """Returns the list of output files from this rule.

    Paths are given relative to buildroot.
    """
    outs = []
    for dep in self.subgraph.successors(self.address):
      dep_rule = self.subgraph.node[dep]['target_obj']
      outs.extend(dep_rule.output_files)
    return outs

  @property
  def composed_deps(self):
    for dep in self.params['srcs']:
      dep_addr = address.new(dep)
      if not dep_addr.repo:
        dep_addr.repo = self.address.repo
        if not dep_addr.path:
          dep_addr.path = self.address.path
      yield dep_addr

  @property
  def source_files(self):
    """pkgfilegroup doesn't exactly have sources.

    This rule's srcs are actually handled as dependencies, which are then
    collected during the build phase.
    """
    return None
