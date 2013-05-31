"""gendeb targets"""

from cloudscaling.butcher.targets import base
from cloudscaling.butcher.targets import base
from cloudscaling.butcher import error


class GenDebBuilder(base.BaseBuilder):
  """Builder for gendeb rules"""

  #def collect_srcs(self):
  #  pass


class GenDeb(base.BaseTarget):
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
    base.BaseTarget.__init__(self, **kwargs)
