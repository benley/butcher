"""gendeb targets"""

import os
import re
import socket
import subprocess
import sys
from cloudscaling.butcher.targets import base
from cloudscaling.butcher.targets import filegroup
from cloudscaling.butcher.targets import pkgfilegroup
from cloudscaling.butcher.targets import pkg_symlink
from cloudscaling.butcher import address
from cloudscaling.butcher import error
from cloudscaling.butcher import util
from twitter.common import app
from twitter.common import log

app.add_option('--fpm_bin', dest='fpm_bin', help='Path to the fpm utility.')


class GenDebBuilder(base.BaseBuilder):
  """Builder for gendeb rules"""

  fpm_bin = app.get_options().fpm_bin or 'fpm'

  def __init__(self, buildroot, target_obj, source_dir):
    base.BaseBuilder.__init__(self, buildroot, target_obj, source_dir)
    self.workdir = os.path.join(
        self.buildroot, self.address.repo, self.address.path, '__GENDEB.%s' %
        self.address.target)
    self.deb_fsroot = os.path.join(self.workdir, 'root')
    self.deb_controlroot = os.path.join(self.workdir, 'DEBIAN')
    self.deb_filelist = []
    self.controlfiles = []
    self.config_files = []

  def prep(self):
    # Due to possibly-unwise cleverness in __init__.py, pylint thinks
    # pkgfilegroup and pkg_symlink are classes here, but it is wrong. They are
    # modules.
    allowed_deps = (pkgfilegroup.PkgFileGroup, pkg_symlink.PkgSymlink)
    for dep in self.rule.composed_deps():
      deprule = self.rule.subgraph.node[dep]['target_obj']
      if not isinstance(deprule, allowed_deps):
        if isinstance(deprule, filegroup.FileGroup) and (
            deprule.address in self.rule.allowed_filegroup_targets):
          pass
        else:
          raise error.InvalidRule(
              'In %s: gendeb rules can only depend on pkgfilegroup '
              'and/or pkg_symlink targets. Was given %s, which is a %s' % (
                  self.address, repr(dep), type(deprule).__name__))
    base.BaseBuilder.prep(self)

  def build(self):
    params = self.rule.params
    # TODO: Ugh, why didn't I make output_files relative to the rule's path?
    deb_filename = self.rule.output_files[0].split(
        os.path.join(self.address.repo, self.address.path), 1)[-1]
    maintainer = params['packager'] or '<%s@%s>' % (os.getlogin(),
                                                    socket.gethostname())
    fpm_description = [params['short_description']] + params['long_description']
    # The required args:
    cmd = [self.fpm_bin, '-f',
           '-t', 'deb',
           '-s', 'dir',
           '--package', deb_filename,
           '--name', params['package_name'],
           '--version', params['version'],
           '--iteration', params['release'],
           '--description', '\n'.join(fpm_description)]
    # Optional things that have default values:
    cmd.extend([
        '--maintainer', maintainer,
        '--epoch', params['epoch'],
        '--category', params['section'],
        '--architecture', params['arch'],
        '--deb-priority', params['priority'],
        ])
    # Optional parameters:
    if params['extra_requires']:
      cmd.extend(util.repeat_flag(params['extra_requires'], '--depends'))
    if params['homepage']:
      cmd.extend(['--url', params['homepage']])

    def maintainer_script(script):
      return self.rulefor(params[script]).source_files[0]

    if params['postinst']:
      cmd.extend(['--after-install', maintainer_script('postinst')])
    if params['postrm']:
      cmd.extend(['--after-remove', maintainer_script('postrm')])
    if params['preinst']:
      cmd.extend(['--before-install', maintainer_script('preinst')])
    if params['prerm']:
      cmd.extend(['--before-remove', maintainer_script('prerm')])
    if params['extra_control_fields']:
      for field, val in params['extra_control_fields']:
        cmd.extend(['--deb-field', '%s: %s' % (field, val)])

    if self.config_files:
      cmd.extend(util.repeat_flag(self.config_files, '--config-files'))

    if self.deb_filelist:
      inputs_file = os.path.join(self.workdir, '__inputs')
      with open(inputs_file, 'w') as ifh:
        ifh.write('\n'.join(self.deb_filelist))
        ifh.write('\n')
      cmd.extend(['-C', self.deb_fsroot,
                  '--inputs', inputs_file])

    # string out those pesky integers
    cmd = [ str(x) for x in cmd ]

    log.debug('Generated fpm command: %s', cmd)
    ruledir = os.path.join(self.buildroot, self.address.repo,
                           self.address.path)
    fpm = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr,
                           cwd=ruledir)
    fpm.wait()


  #def collect_srcs(self):
  #  pass

  def collect_deps(self):
    deb_filelist = []
    for tgt in self.rule.composed_deps() or []:
      rule = self.rulefor(tgt)
      for item in rule.output_files:
        item_base = item.lstrip('/').split(
            os.path.join(rule.address.repo,
                         rule.address.path), 1)[-1].lstrip('/')
        # Maintainer scripts and such don't need to be copied into the tree:
        # (they'll be picked up from their location in situ)
        if rule.address not in self.rule.control_deps:
          deb_filelist.append(item_base)
          if 'section' in rule.params and rule.params['section'] == 'config':
            self.config_files.append(item_base)
          dst = self.deb_fsroot
          self.linkorcopy(
              os.path.join(self.buildroot, item),
              os.path.join(dst, item_base))
    self.deb_filelist = deb_filelist


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
      ('homepage', str, None),
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
    # Exceptions to the "only pkgfilegroup or pkg_symlink" restriction so
    # preinst/postinst/prerm/postrm dependencies work:
    self.allowed_filegroup_targets = set()
    self.control_deps = set()

  def validate_args(self):
    """Input validators for this rule type."""
    base.BaseTarget.validate_args(self)
    params = self.params
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

  def composed_deps(self):
    deps = []
    for dep in ['preinst', 'postinst', 'prerm', 'postrm']:
      if self.params[dep]:
        dep_addr = self.makeaddress(self.params[dep])
        deps.append(dep_addr)
        self.control_deps.add(dep_addr)
        self.allowed_filegroup_targets.add(dep_addr)
    return deps + base.BaseTarget.composed_deps(self)

  @property
  def output_files(self):
    return [os.path.join(
        self.address.repo, self.address.path,
        '%(package_name)s_%(version)s-%(release)s_%(arch)s.deb' % self.params)]
