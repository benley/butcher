"""pkg_symlink targets."""

from butcher.targets import base


class PkgSymlinkBuilder(base.BaseBuilder):
    pass


class PkgSymlink(base.BaseTarget):
    rulebuilder = PkgSymlinkBuilder
    ruletype = 'pkg_symlink'

    required_params = [
        ('name', str),
        ('link_name', str),
        ('link_target', str)]
    optional_params = [
        ('mode', int, None),
        ('owner', str, None),
        ('group', str, None)]
