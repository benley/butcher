"""gendeb targets"""

import os
import re
import socket
from cloudscaling.butcher.targets import base
from cloudscaling.butcher.targets import pkgfilegroup
from cloudscaling.butcher.targets import pkg_symlink
from cloudscaling.butcher import error
from twitter.common import app
from twitter.common import log

app.add_option('--fpm_bin', dest='fpm_bin', help='Path to the fpm utility.')


class GenDebBuilder(base.BaseBuilder):
  """Builder for gendeb rules"""

  fpm_bin = app.get_options().fpm_bin or 'fpm'

  def prep(self):
    # Due to possibly-unwise cleverness in __init__.py, pylint thinks
    # pkgfilegroup and pkg_symlink are classes here, but it is wrong. They are
    # modules.
    allowed_deps = (pkgfilegroup.PkgFileGroup, pkg_symlink.PkgSymlink)
    for dep in self.rule.composed_deps:
      deprule = self.rule.subgraph.node[dep]['target_obj']
      if not isinstance(deprule, allowed_deps):
        raise error.InvalidRule(
            'In %s: gendeb rules can only depend on pkgfilegroup '
            'and/or pkg_symlink targets. Was given %s, which is a %s' % (
                self.address, repr(dep), type(deprule).__name__))
    base.BaseBuilder.prep(self)

  def build(self):
    params = self.rule.params
    deb_filename = self.rule.output_files[0]
    maintainer = params['packager'] or '<%s@%s>' % (os.getlogin(),
                                                    socket.gethostname())
    # The required args:
    cmd = [self.fpm_bin,
           '-t', 'deb',
           '--package', deb_filename,
           '--name', params['package_name'],
           '--version', params['version'],
           '--iteration', params['release'],
           '--description', params['long_description']]
    # Optional things that have default values:
    cmd.extend(['--maintainer', maintainer,
                '--epoch', params['epoch'],
                '--category', params['section'],
                '--arch', params['arch'],
                '--deb-priority', params['priority']])
    # Optional parameters:
    if params['extra_requires']:
      def repeat_flag(seq, flag):
        """repeat_flag([1, 2, 3], '-f') ==> ['-f', 1, '-f', 2, '-f', 3]"""
        for item in iter(seq):
          yield flag
          yield item
      cmd.extend(repeat_flag(self.rule.extra_requires, '--depends'))
    if params['postinst']:
      cmd.extend(['--after-install', params['postinst']])
    if params['postrm']:
      cmd.extend(['--after-remote', params['postrm']])
    if params['preinst']:
      cmd.extend(['--before-install', params['preinst']])
    if params['prerm']:
      cmd.extend(['--before-remove', params['prerm']])
    if params['extra_control_fields']:
      for field, val in params['extra_control_fields']:
        cmd.extend(['--deb-field', '%s: %s' % (field, val)])

    log.debug('Generated fpm command: %s', cmd)
    log.warn('gendeb is only partially implemented. Expect failure.')

  #def collect_srcs(self):
  #  pass


class GenDeb(base.BaseTarget):
  """gendeb rule"""

  rulebuilder = GenDebBuilder
  ruletype = 'gendeb'

  required_params = [
      ('name', str),
      ('version', (str, int)),
      ('release', (str, int)),
      ('long_description', list),
      ('short_description', str),
      ]
  optional_params = [
      ('arch', str, 'amd64'),
      ('deps', list, None),
      # Where does this go?
      #('distro', str, 'unstable'),
      ('epoch', (str, int), 0),
      ('extra_control_fields', list, None),
      ('extra_requires', list, None),
      ('packager', str, None),
      ('package_name', str, None),
      ('priority', str, 'extra'),
      ('postinst', str, None),
      ('postrm', str, None),
      ('preinst', str, None),
      ('prerm', str, None),
      ('section', str, 'misc'),
      # Not ready for these:
      #('strip', bool, False),
      #('triggers', str, None),
      ]

  def __init__(self, **kwargs):
    self.params = {}
    base.BaseTarget.__init__(self, **kwargs)
    if not self.params['package_name']:
      self.params['package_name'] = self.params['name']

  def validate_args(self):
    """Input validators for this rule type."""
    base.BaseTarget.validate_args(self)
    params = self.params
    if params['deps'] is not None:
      assert isinstance(params['deps'], list), (
          'deps must be a list, not %s' % type(params['deps']))
    if params['extra_requires'] is not None:
      assert isinstance(params['extra_requires'], list), (
          'extra_requires must be a list of strings, not %s' % type(
              params['extra_requires']))
    if params['extra_control_fields'] is not None:
      assert isinstance(params['extra_control_fields'], list), (
          'extra_control_fields must be a list of tuples, not %s' % type(
              params['extra_control_fields']))
      for elem in params['extra_control_fields']:
        assert (isinstance(elem, tuple) and len(elem) == 1), (
            'extra_control_fields must be a list of 2-element tuples. '
            'Invalid contents: %s' % elem)
    pkgname_re = '^[a-z][a-z0-9+-.]+'
    assert re.match(pkgname_re, params['package_name']), (
        'Invalid package name: %s. Must match %s' % (
            params['package_name'], pkgname_re))
    # TODO: more of this.

  @property
  def output_files(self):
    return [
        '%(package_name)s_%(version)s-%(release)s_%(arch)s.deb' % self.params]
