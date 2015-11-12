"""filegroup targets"""

import os.path
from butcher.targets import base


class FileGroupBuilder(base.BaseBuilder):
    """Builder for filegroup."""
    ruletype = 'filegroup'

    def build(self):
        pass


class FileGroup(base.BaseTarget):
    """filegroup rule."""
    rulebuilder = FileGroupBuilder
    ruletype = 'filegroup'
    required_params = [('name', str), ('srcs', list)]
    optional_params = []

    @property
    def output_files(self):
        """Returns the list of output files from this rule.

        Paths are relative to buildroot.
        """
        for item in self.source_files:
            yield os.path.join(self.address.repo, self.address.path, item)
