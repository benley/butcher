"""pkgfilegroup targets

ONLY PARTIALLY IMPLEMENTED!

Works so far:
  - collects output files from rules given in srcs, emits them as its own
    outputs

Not yet implemented:
  - set attributes
  - put output files in the prefixed directory (should this happen here?)
"""

import os.path
from cloudscaling.buildy import address
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
    return [ address.Address(x) for x in self.params['srcs'] ]

  @property
  def source_files(self):
    """pkgfilegroup doesn't exactly have sources.

    This rule's srcs are actually handled as dependencies, which are then
    collected during the build phase.
    """
    return None
