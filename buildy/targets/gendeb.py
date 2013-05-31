"""gendeb targets"""

from .base import BaseBuilder
from .base import BaseTarget
from cloudscaling.buildy import error


class GenDebBuilder(BaseBuilder):
  """Builder for gendeb rules"""

  #def collect_srcs(self):
  #  pass


class GenDeb(BaseTarget):
  """gendeb rule"""

  rulebuilder = GenDebBuilder
  ruletype = 'gendeb'

  required_params = [
      'name', 'version', 'long_description', 'short_description']
  optional_params = {
      'deps': None,
      'arch': 'all',
      'packager': None,
      'extra_requires': None,
      'package_name': None,
      'distro': 'unstable',
      'section': 'misc',
      'priority': 'extra',
      'extra_control_fields': None,
      'preinst': None,
      'postinst': None,
      'prerm': None,
      'postrm': None,
      'triggers': None,
      'strip': False,
      }

  def __init__(self, **kwargs):
    self.params = {}
    BaseTarget.__init__(self, **kwargs)
