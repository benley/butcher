"""genrule target"""

import os
import subprocess
import sys
import stat
from cloudscaling.buildy import error
from cloudscaling.buildy.targets import base
from twitter.common import log


class GenRuleBuilder(base.BaseBuilder):
  """Build a genrule."""

  def __init__(self, buildroot, target_obj, source_dir):
    base.BaseBuilder.__init__(self, buildroot, target_obj, source_dir)
    self.cmd = self.rule.params['cmd']

  def build(self):
    shellcmd = 'BUILDROOT=%s; %s' % (self.buildroot, self.cmd)
    shellcwd = os.path.join(self.buildroot, self.rule.address.path)
    log.debug('[%s]: Running in a shell:\n   %s', self.rule.name, shellcmd)
    proc = subprocess.Popen(shellcmd, stdout=sys.stdout,
                            stderr=sys.stderr, shell=True, cwd=shellcwd)
    returncode = proc.wait()
    if returncode != 0:
      raise error.TargetBuildFailed(
          self.rule.name,
          'cmd returned %s.' % (returncode))
    elif self.rule.params['executable']:
      # GenRule.__init__ already ensured that there is only one output file if
      # executable=1 is set.
      built_outfile = os.path.join(self.buildroot, self.rule.address.path,
                                  self.rule.output_files[0])
      built_outfile_stat = os.stat(built_outfile)
      os.chmod(built_outfile, built_outfile_stat.st_mode | stat.S_IEXEC)


class GenRule(base.BaseTarget):
  """genrule target"""

  rulebuilder = GenRuleBuilder
  ruletype = 'genrule'

  required_params = ['name', 'cmd', 'outs']
  optional_params = {
      'srcs': None,
      'deps': None,
      'executable': False,
      }

  def __init__(self, **kwargs):
    base.BaseTarget.__init__(self, **kwargs)

    if len(self.params['outs']) > 1 and self.params['executable']:
      raise error.InvalidRule(
          'executable=1 is only allowed when there is one output file.')

  @property
  def output_files(self):
    """Returns the list of output files from this rule.

    In this case it's simple (for now) - the output files are enumerated in the
    rule definition.
    """
    return self.params['outs']
