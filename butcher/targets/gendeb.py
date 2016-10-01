"""gendeb targets"""

import hashlib
import os
import pwd
import re
import socket
import subprocess
import sys
from butcher.targets import base
from butcher.targets import filegroup
from butcher.targets import pkgfilegroup
from butcher.targets import pkg_symlink
from butcher import error
from butcher import util
from twitter.common import app
from twitter.common import log


app.add_option(
    '--fpm_bin', dest='fpm_bin', default='fpm',
    help='Path to the fpm binary.')


class GenDebSetup(app.Module):
    """Pre-run requirements to be set up before the build process starts."""
    def __init__(self):
        app.Module.__init__(self, label=__name__,
                            description='gendeb')

    def setup_function(self):
        """twitter.comon.app runs this before any global main() function."""
        fpm_path = app.get_options().fpm_bin
        if not os.path.exists(fpm_path):
            log.warn('Could not find fpm; gendeb cannot function.')
        else:
            GenDebBuilder.fpm_bin = fpm_path

app.register_module(GenDebSetup())


class GenDebBuilder(base.BaseBuilder):
    """Builder for gendeb rules"""

    # Path to the fpm binary.
    fpm_bin = None

    def __init__(self, buildroot, target_obj, source_dir):
        base.BaseBuilder.__init__(self, buildroot, target_obj, source_dir)
        self.workdir = os.path.join(
            self.buildroot, self.address.repo, self.address.path,
            '__GENDEB_%s' % self.address.target)
        self.deb_fsroot = os.path.join(self.workdir, 'root')
        self.deb_controlroot = os.path.join(self.workdir, 'DEBIAN')
        self.deb_filelist = []
        self.controlfiles = []
        self.config_files = []
        self.params = self.rule.params

    def prep(self):
        allowed_deps = (pkgfilegroup.PkgFileGroup, pkg_symlink.PkgSymlink)
        for dep in self.rule.composed_deps():
            deprule = self.rule.subgraph.node[dep]['target_obj']
            if not isinstance(deprule, allowed_deps):
                if (isinstance(deprule, filegroup.FileGroup)
                        and deprule.address
                        in self.rule.allowed_filegroup_targets):
                    pass
                else:
                    raise error.InvalidRule(
                        'In %s: gendeb rules can only depend on pkgfilegroup '
                        'and/or pkg_symlink targets. Was given %s, '
                        'which is a %s' % (self.address, repr(dep),
                                           type(deprule).__name__))
        base.BaseBuilder.prep(self)

    def build(self):
        params = self.params
        deb_filename = os.path.basename(self.rule.output_files[0])
        maintainer = params['packager'] or '<%s@%s>' % (
            pwd.getpwuid(os.getuid()).pw_name, socket.gethostname())
        fpm_description = [params['short_description']
                           ] + params['long_description']
        # The required args:
        cmd = [self.fpm_bin, '-f',
               '-t', 'deb',
               '-s', 'dir',
               '--package', deb_filename,
               '--name', params['package_name'],
               '--version', params['version'],
               '--iteration', params['release'],
               '--deb-user', params['files_owner'],
               '--deb-group', params['files_group'],
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
        if params['conflicts']:
            cmd.extend(util.repeat_flag(params['conflicts'], '--conflicts'))
        if params['homepage']:
            cmd.extend(['--url', params['homepage']])

        maintainer_script = lambda x: (self.rulefor(params[x])
                                           .source_files.next())
        # See that next()? source_files is a generator.
        # Otherwise that would be [0].

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
        cmd = [str(x) for x in cmd]

        log.debug('Generated fpm command: %s', cmd)
        ruledir = os.path.join(self.buildroot, self.address.repo,
                               self.address.path)
        fpm = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr,
                               cwd=ruledir)
        fpm.wait()
        with open(os.path.join(self.buildroot, self.rule.output_files[1]),
                  'w') as changesfile:
            changesfile.write(self.genchanges())

    #def collect_srcs(self):
    #    pass

    def genchanges(self):
        """Generate a .changes file for this package."""
        chparams = self.params.copy()
        debpath = os.path.join(self.buildroot, self.rule.output_files[0])
        chparams.update({
            'fullversion': '{epoch}:{version}-{release}'.format(**chparams),
            'metahash': self._metahash().hexdigest(),
            'deb_sha1': util.hash_file(debpath, hashlib.sha1()).hexdigest(),
            'deb_sha256': util.hash_file(debpath, hashlib.sha256()
                                         ).hexdigest(),
            'deb_md5': util.hash_file(debpath, hashlib.md5()).hexdigest(),
            'deb_bytes': os.stat(debpath).st_size,
            # TODO: having to do this split('/')[-1] is absurd:
            'deb_filename': debpath.split('/')[-1],
            })

        output = '\n'.join([
            'Format: 1.8',
            # Static date string for repeatable builds:
            'Date: Tue, 01 Jan 2013 00:00:00 -0700',
            'Source: {package_name}',
            'Binary: {package_name}',
            'Architecture: {arch}',
            'Version: {fullversion}',
            'Distribution: {distro}',
            'Urgency: {urgency}',
            'Maintainer: {packager}',
            'Description: ',
            ' {package_name} - {short_description}',
            'Changes: ',
            ' {package_name} ({fullversion}) {distro}; urgency={urgency}',
            ' .',
            ' * Built by Butcher - metahash for this build is {metahash}',
            'Checksums-Sha1: ',
            ' {deb_sha1} {deb_bytes} {deb_filename}',
            'Checksums-Sha256: ',
            ' {deb_sha256} {deb_bytes} {deb_filename}',
            'Files: ',
            ' {deb_md5} {deb_bytes} {section} {priority} {deb_filename}',
            ''  # Newline at end of file.
            ]).format(**chparams)

        return output

    def collect_deps(self):
        deb_filelist = []
        for tgt in self.rule.composed_deps() or []:
            rule = self.rulefor(tgt)
            for item in rule.output_files:
                item_base = item.lstrip('/').split(
                    os.path.join(rule.address.repo,
                                 rule.address.path), 1)[-1].lstrip('/')
                # Maintainer scripts and such don't need to be copied
                # into the tree:
                # (they'll be picked up from their location in situ)
                if rule.address not in self.rule.control_deps:
                    deb_filelist.append(item_base)
                    if ('section' in rule.params
                            and rule.params['section'] == 'config'):
                        self.config_files.append('/%s' % item_base)
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
        ('conflicts', list, None),
        ('deps', list, None),
        ('distro', str, 'unstable'),
        ('epoch', (str, int), 0),
        ('extra_control_fields', list, None),
        ('extra_requires', list, None),
        ('files_owner', str, 'root'),
        ('files_group', str, 'root'),
        ('homepage', str, None),
        ('packager', str, None),
        ('package_name', str, None),
        ('priority', str, 'extra'),
        ('postinst', str, None),
        ('postrm', str, None),
        ('preinst', str, None),
        ('prerm', str, None),
        ('section', str, 'misc'),
        ('urgency', str, 'low'),
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
        return [
            os.path.join(
                self.address.repo, self.address.path,
                '{package_name}_{version}-{release}_{arch}.deb'.format(
                    **self.params)),
            os.path.join(
                self.address.repo, self.address.path,
                '{package_name}_{version}-{release}_{arch}.changes'.format(
                    **self.params))
            ]
