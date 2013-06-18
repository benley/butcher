"""Manage rubygems for our own internal use."""

import os
import subprocess
from twitter.common import app
from twitter.common import log
from cloudscaling.butcher import error

app.add_option(
    '--gemdir', dest='gem_basedir',
    help='Path to our gems directory. Defaults to living inside --basedir.')


class RubyGems(app.Module):

  def __init__(self):
    app.Module.__init__(self, label=__name__,
                        description='Rubygems wrapper.',
                        dependencies='butcher')
    self.gem_basedir = None

  def gem_bindir(self):
    return os.path.join(self.gem_basedir, 'bin')

  def setup_function(self):
    if not app.get_options().gem_basedir:
      app.set_option('gem_basedir',
                     os.path.join(app.get_options().butcher_basedir, 'gems'))
    self.gem_basedir = app.get_options().gem_basedir
    os.environ['GEM_HOME'] = self.gem_basedir
    os.environ['GEM_PATH'] = self.gem_basedir

    try:
      subprocess.check_output(['gem', '--version'])
    except (OSError, subprocess.CalledProcessError) as err:
      raise error.ButcherError('gem does not appear to be installed.')

app.register_module(RubyGems())


def install_gem(gemname, version=None, conservative=True, ri=False, rdoc=False,
                development=False, format_executable=False, force=False):
  """Install a ruby gem."""
  cmdline = ['gem', 'install', '--no-ri', '--no-rdoc']
  if conservative:
    cmdline.append('--conservative')
  if ri:
    cmdline.append('--ri')
  else:
    cmdline.append('--no-ri')
  if rdoc:
    cmdline.append('--rdoc')
  else:
    cmdline.append('--no-rdoc')
  if development:
    cmdline.append('--development')
  if format_executable:
    cmdline.append('--format-executable')
  if force:
    cmdline.append('--force')
  if version:
    cmdline.extend(['--version', version])

  cmdline.append(gemname)

  msg = 'Installing ruby gem: %s' % gemname
  if version:
    msg += ' Version requested: %s' % version
  log.debug(msg)

  try:
    subprocess.check_output(cmdline, shell=False)
  except (OSError, subprocess.CalledProcessError) as err:
    raise error.ButcherError('Gem install failed. Error was: %s. Output: %s',
                             err, err.output)


def is_installed(gemname, version=None):
  """Check if a gem is installed."""
  cmdline = ['gem', 'list', '-i', gemname]
  if version:
    cmdline.extend(['-v', version])
  try:
    subprocess.check_output(cmdline, shell=False)
    return True
  except (OSError, subprocess.CalledProcessError) as err:
    if err.returncode == 1:
      return False
    else:
      raise error.ButcherError('Failure running gem. Error was: %s. Output: %s',
                               err, err.output)


def gem_bindir():
  return RubyGems().gem_bindir()
