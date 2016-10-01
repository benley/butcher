"""pkgfilegroup targets

Mostly implemented. Remaining functionality may be left to consumers of this
rule.

Works so far:
  - collects output files from rules given in srcs, emits them as its own
    outputs
  - Applies strip_prefix, puts files in the prefixed directory structure.

Not yet implemented:
  - set attributes
"""

import os
from butcher import address
from butcher.targets import base


class PkgFileGroupBuilder(base.BaseBuilder):
    """Builder for pkgfilegroup"""
    ruletype = 'pkgfilegroup'

    def build(self):
        for dep in self.rule.composed_deps():
            dep_rule = self.rule.subgraph.node[dep]['target_obj']
            for dep_file in dep_rule.output_files:
                src = os.path.join(self.buildroot, dep_file)
                dst = self.rule.translate_path(dep_file, dep_rule)
                output_dst = os.path.join(self.buildroot, dst)
                output_dstdir = os.path.dirname(output_dst)
                if not os.path.exists(output_dstdir):
                    os.makedirs(output_dstdir)
                self.linkorcopy(src, output_dst)
                #TODO: attrs


class PkgFileGroup(base.BaseTarget):
    """pkgfilegroup rule"""
    rulebuilder = PkgFileGroupBuilder
    ruletype = 'pkgfilegroup'

    required_params = [('name', str),
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

        Paths are generated from the outputs of this rule's dependencies, with
        their paths translated based on prefix and strip_prefix.

        Returned paths are relative to buildroot.
        """
        for dep in self.subgraph.successors(self.address):
            dep_rule = self.subgraph.node[dep]['target_obj']
            for dep_file in dep_rule.output_files:
                yield self.translate_path(dep_file, dep_rule).lstrip('/')

    def composed_deps(self):
        for dep in self.params['srcs']:
            yield self.makeaddress(dep)

    @property
    def source_files(self):
        """pkgfilegroup doesn't have normal sources.

        This rule's srcs are actually handled as dependencies, which are then
        collected during the build phase.
        """
        return None
