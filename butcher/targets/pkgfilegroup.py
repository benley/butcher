"""pkgfilegroup targets

ONLY PARTIALLY IMPLEMENTED!

Works so far:
  - collects output files from rules given in srcs, emits them as its own
    outputs

Not yet implemented:
  - set attributes
  - put output files in the prefixed directory (should this happen here?)
"""

import os
import shutil
from cloudscaling.butcher import address
from cloudscaling.butcher.targets import base


class PkgFileGroupBuilder(base.BaseBuilder):
  """Builder for pkgfilegroup"""
  ruletype = 'pkgfilegroup'

  def build(self):
    for dep in self.rule.composed_deps:
      dep_rule = self.rule.subgraph.node[dep]['target_obj']
      for dep_file in dep_rule.output_files:
        src = os.path.join(self.buildroot, dep_rule.address.path, dep_file)
        dst = self.rule.translate_path(dep_file, dep_rule)
        output_dst = os.path.join(self.buildroot, dst)
        output_dstdir = os.path.dirname(output_dst)
        if not os.path.exists(output_dstdir):
          os.makedirs(output_dstdir)
        shutil.copy2(src, output_dstdir)
        #TODO: attrs


class PkgFileGroup(base.BaseTarget):
  """pkgfilegroup rule"""
  rulebuilder = PkgFileGroupBuilder
  ruletype = 'pkgfilegroup'

  required_params = [
      ('name', str),
      ('prefix', str),
      ('srcs', list)]
  optional_params = [
      ('attr', list, None),
      ('section', str, None),  # one of ('', 'doc', 'config')
      ('strip_prefix', str,  None)]

  def translate_path(self, dep_file, dep_rule):
    """Translate dep_file from dep_rule into this rule's output path."""
    dst_base = dep_file.split(os.path.join(dep_rule.address.repo,
                                           dep_rule.address.path), 1)[-1]
    if self.params['strip_prefix']:
      dst_base = dep_file.split(self.params['strip_prefix'], 1)[-1]
    return os.path.join(self.address.repo, self.address.path,
                        self.params['prefix'].lstrip('/'),
                        dst_base.lstrip('/'))

  @property
  def output_files(self):
    """Returns the list of output files from this rule.

    Paths are given relative to buildroot.
    """
    for dep in self.subgraph.successors(self.address):
      dep_rule = self.subgraph.node[dep]['target_obj']
      for dep_file in dep_rule.output_files:
        out = self.translate_path(dep_file, dep_rule).lstrip('/')
        yield out

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
    """pkgfilegroup doesn't have normal sources.

    This rule's srcs are actually handled as dependencies, which are then
    collected during the build phase.
    """
    return None
