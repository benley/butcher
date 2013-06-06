"""genrule target"""

import os
import subprocess
import sys
import stat
from cloudscaling.butcher import error
from cloudscaling.butcher.targets import base
from twitter.common import log


class GenRuleBuilder(base.BaseBuilder):
  """Build a genrule."""

  def __init__(self, buildroot, target_obj, source_dir):
    base.BaseBuilder.__init__(self, buildroot, target_obj, source_dir)
    self.cmd = self.rule.params['cmd']

  def build(self):
    path_to_this_rule = os.path.join(self.buildroot, self.rule.address.repo,
                                     self.rule.address.path)
    shellcmd = 'BUILDROOT="%s"; RULEDIR="%s"; %s' % (
        self.buildroot, path_to_this_rule, self.cmd)
    log.debug('[%s]: Running in a shell:\n  %s', self.rule.name, shellcmd)
    proc = subprocess.Popen(shellcmd, shell=True, cwd=path_to_this_rule,
                            stdout=sys.stdout, stderr=sys.stderr)
    returncode = proc.wait()
    if returncode != 0:
      raise error.TargetBuildFailed(self.rule.name,
                                    'cmd returned %s.' % (returncode))
    elif self.rule.params['executable']:
      # GenRule.__init__ already ensured that there is only one output file if
      # executable=1 is set.
      built_outfile = os.path.join(self.buildroot, self.rule.output_files[0])
      built_outfile_stat = os.stat(built_outfile)
      os.chmod(built_outfile, built_outfile_stat.st_mode | stat.S_IEXEC)

  def _metahash(self):
    """Include genrule cmd in the metahash."""
    if self._cached_metahash:
      return self._cached_metahash
    mhash = base.BaseBuilder._metahash(self)
    log.debug('[%s]: Metahash input: cmd="%s"', self.address, self.cmd)
    mhash.update(self.cmd)
    self._cached_metahash = mhash
    return mhash


class GenRule(base.BaseTarget):
  """genrule target"""

  rulebuilder = GenRuleBuilder
  ruletype = 'genrule'

  required_params = [('name', str), ('cmd', str), ('outs', list)]
  optional_params = [('srcs', list, None),
                     ('deps', list, None),
                     ('executable', bool, False)]

  def __init__(self, **kwargs):
    base.BaseTarget.__init__(self, **kwargs)

    if len(self.params['outs']) > 1 and self.params['executable']:
      raise error.InvalidRule(
          'executable=1 is only allowed when there is one output file.')

  @property
  def output_files(self):
    """Returns the list of output files from this rule, relative to buildroot.

    In this case it's simple (for now) - the output files are enumerated in the
    rule definition.
    """
    outs = [os.path.join(self.address.repo, self.address.path, x)
            for x in self.params['outs']]
    return outs
