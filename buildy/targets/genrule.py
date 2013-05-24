"""genrule target"""

import subprocess
import sys
from cloudscaling.buildy import builder
from cloudscaling.buildy import error
from cloudscaling.buildy.targets import base
from twitter.common import log


class GenRuleBuilder(base.BaseBuilder):
  """Build a genrule."""

  def __init__(self, buildroot, target_obj, source_dir):
    base.BaseBuilder.__init__(self, buildroot, target_obj, source_dir)
    self.cmd = self.rule.params['cmd']
    #self.srcs_map = self.rule.params['srcs']

  def build(self):
    cmd_prefix = self.gen_srcs_shell_array()
    shellcmd = cmd_prefix + self.cmd
    log.debug('RUNNING: %s', shellcmd)
    subprocess.Popen(shellcmd, stdout=sys.stdout,
                     stderr=sys.stderr, shell=True, cwd=self.buildroot)


  def gen_srcs_shell_array(self):
    cmd = 'declare -A butcher_location=( '
    cmd += ' '.join(
        [ "['%s']='%s'" % (src, loc) for (src, loc) in self.srcs_map.items() ])
    cmd += ' ); '
    return cmd


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
