"""Base target."""

import os
import shutil
from cloudscaling.buildy import error
from twitter.common import log


class BaseBuilder(object):

  def __init__(self, buildroot, target_obj, source_dir):
    self.source_dir = source_dir    # Where the git repo is checked out
    self.rule = target_obj          # targets.something object
    self.address = target_obj.name  # Build address
    self.buildroot = os.path.join(buildroot, self.address.repo)
    if not os.path.exists(self.buildroot):
      os.makedirs(self.buildroot)
    # TODO: some rule types don't have srcs.
    #       Should probably use an intermediate subclass.
    self.srcs_map = {}

  def collect_srcs(self):
    for src in self.rule.params['srcs']:
      srcpath = os.path.join(self.source_dir, self.address.path, src)
      dstdir = os.path.join(self.buildroot, self.address.path)
      if not os.path.exists(dstdir):
        os.makedirs(dstdir)
      shutil.copy2(srcpath, dstdir)
      self.srcs_map[src] = os.path.join(dstdir, src)

  def collect_deps(self):
    pass

  def prep(self):
    self.collect_srcs()
    self.collect_deps()

  def build(self):
    log.warn('UNIMPLEMENTED: pretending to build %s', self.address)


class BaseTarget(object):
  """Abstract base class for build targets."""

  rulebuilder = BaseBuilder
  ruletype = None

  required_params = ['name']
  optional_params = {}

  def __init__(self, **kwargs):
    self.name = kwargs['name']
    self.params = {}
    try:
      for param in self.required_params:
        self.params[param] = kwargs.pop(param)
    except KeyError:
      raise error.InvalidRule(
          'While loading %s: Required parameter \'%s\' not given.' % (
              self.name, param))
    for param in self.optional_params:
      if param in kwargs:
        self.params[param] = kwargs.pop(param)
      else:
        self.params[param] = self.optional_params[param]

    if kwargs:
      raise error.InvalidRule(
          'While loading %s: Unknown parameter(s): %s' % (
              self.name, ', '.join(kwargs.keys())))
