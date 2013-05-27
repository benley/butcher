"""Base target."""

import os
import shutil
from cloudscaling.buildy import buildtarget
from cloudscaling.buildy import cache
from cloudscaling.buildy import error
from twitter.common import log


class BaseBuilder(object):
  """Base class for rule self-builders."""

  def __init__(self, buildroot, target_obj, source_dir):
    self.source_dir = source_dir    # Where the git repo is checked out
    self.rule = target_obj          # targets.something object
    self.address = target_obj.name  # Build address
    self.buildroot = os.path.join(buildroot, self.address.repo)
    self.cachemgr = cache.CacheManager()
    if not os.path.exists(self.buildroot):
      os.makedirs(self.buildroot)
    # TODO: some rule types don't have srcs.
    #       Should probably use an intermediate subclass.
    self.srcs_map = {}  # <-- Nothing appears to use this?

  def collect_srcs(self):
    for src in self.rule.params['srcs']:
      srcpath = os.path.join(self.source_dir, self.address.path, src)
      dstpath = os.path.join(self.buildroot, self.address.path, src)
      dstdir = os.path.dirname(dstpath)
      log.debug('[%s]: Collect srcs: %s -> %s', self.rule.address, srcpath,
                dstpath)
      if not os.path.exists(dstdir):
        os.makedirs(dstdir)
      shutil.copy2(srcpath, dstdir)
      self.srcs_map[src] = os.path.join(dstdir, src)

  def collect_deps(self):
    pass

  def collect_outs(self):
    for outfile in self.rule.output_files:
      outfile_built = os.path.join(self.buildroot, self.rule.address.path,
                                   outfile)

      # TODO: record git repo state and buildoptions in cachemgr
      self.cachemgr.putfile(outfile_built, self.buildroot, self.rule, 'fake')

  def prep(self):
    self.collect_srcs()
    self.collect_deps()

  def build(self):
    """Build the rule. Must be overriden by inheriting class."""
    raise NotImplementedError


class BaseTarget(object):
  """Abstract base class for build targets."""

  rulebuilder = BaseBuilder
  ruletype = None

  required_params = ['name']
  optional_params = {}

  def __init__(self, **kwargs):
    self.name = kwargs['name']
    self.address = buildtarget.BuildTarget(self.name)
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

  @property
  def output_files(self):
    """Returns the list of output files from this rule.

    Should be overridden by inheriting class.
    Paths must be relative to the location of the build rule.
    """
    raise NotImplementedError
