"""genrule target"""

from cloudscaling.buildy import error
from cloudscaling.buildy.targets import base

class GenRule(base.BaseTarget):
  """genrule target"""

  def __init__(self, name, cmd, outs, srcs=None, deps=None, executable=False):
    base.BaseTarget.__init__(self, name)
    self.cmd = cmd
    self.outs = tuple(outs)
    if srcs:
      self.srcs = tuple(srcs)
    if deps:
      self.deps = tuple(deps)
    else:
      self.deps = None
    if len(outs) > 1 and executable:
      raise error.ButcherError(
          'executable=1 is only allowed when there is one output file.')
    self.executable = executable
