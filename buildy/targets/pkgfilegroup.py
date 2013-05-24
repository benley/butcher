"""pkgfilegroup targets"""

from .base import BaseBuilder
from .base import BaseTarget

class PkgFileGroupBuilder(BaseBuilder):
  ruletype = 'pkgfilegroup'


class PkgFileGroup(BaseTarget):
  rulebuilder = PkgFileGroupBuilder
  ruletype = 'pkgfilegroup'

  required_params = ['name', 'prefix']
  optional_params = {
      'srcs': None,
      'attr': None,
      'section': None,  # one of ('', 'doc', 'config')
      'strip_prefix': None,
      }
