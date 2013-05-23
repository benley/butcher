"""genrule target"""

from cloudscaling.buildy import error
from cloudscaling.buildy.targets import base

class GenRule(base.BaseTarget):
  """genrule target"""
  def __init__(self, name, srcs, cmd, outs, deps=None, executable=False):
    base.BaseTarget.__init__(self, name)
    self.name = name
    self.srcs = tuple(srcs)
    self.cmd = cmd
    self.outs = tuple(outs)
    if deps:
      self.deps = tuple(deps)
    else:
      self.deps = None
    if len(outs) > 1 and executable:
      raise error.ButcherError(
          'executable=1 is only allowed when there is one output file.')
    self.executable = executable
