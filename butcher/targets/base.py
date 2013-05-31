"""Base target."""

import io
import networkx
import os
import shutil
from cloudscaling.butcher import address
from cloudscaling.butcher import cache
from cloudscaling.butcher import error
from cloudscaling.butcher import gitrepo
from cloudscaling.butcher import util
from twitter.common import log


class BaseBuilder(object):
  """Base class for rule self-builders."""

  def __init__(self, buildroot, target_obj, source_dir):
    self.source_dir = source_dir    # Where the git repo is checked out
    self.rule = target_obj          # targets.something object
    self.address = target_obj.name  # Build address
    self.buildroot = buildroot
    self.cachemgr = cache.CacheManager()
    if not os.path.exists(self.buildroot):
      os.makedirs(self.buildroot)
    # TODO: some rule types don't have srcs.
    #       Should probably use an intermediate subclass.
    self.srcs_map = {}
    self.deps_map = {}

  def collect_srcs(self):
    for src in self.rule.source_files or []:
      srcpath = os.path.join(self.source_dir, self.address.path, src)
      dstpath = os.path.join(self.buildroot, self.address.repo,
                             self.address.path, src)
      dstdir = os.path.dirname(dstpath)
      log.debug('[%s]: Collect srcs: %s -> %s', self.rule.address, srcpath,
                dstpath)
      if not os.path.exists(dstdir):
        os.makedirs(dstdir)
      shutil.copy2(srcpath, dstdir)
      self.srcs_map[src] = dstpath

  def collect_deps(self):
    pass
    # Holy crap, this whole function is unnecessary with the current design.
    # A rule's dependencies are built before the rule (duh) and the outputs
    # thereof go into the same buildroot that this one uses, so the files will
    # already be in place.

    #if 'deps' not in self.rule.params:
    #  return
    #for dep in self.rule.composed_deps or []:
    #  dep_rule = self.rule.subgraph.node[dep]['target_obj']
    #  for item in dep_rule.output_files:
    #   srcpath = os.path.join(self.buildroot, item)
    #   dstpath = os.path.join(self.buildroot, item)
    #   dstdir = os.path.dirname(dstpath)
    #   log.debug('[%s]: Collecting deps: %s -> %s',
    #             self.address, item, dstpath)
    #   if not os.path.exists(dstdir):
    #     os.makedirs(dstdir)
    #   shutil.copy2(srcpath, dstdir)
    #   self.deps_map[item] = dstpath

  def _metahash(self):
    """Checksum hash of all the inputs to this rule.

    Output is invalid until collect_srcs and collect_deps have been run.

    In theory, if this hash doesn't change, the outputs won't change either,
    which makes it useful for caching.
    """
    log.debug('[%s]: Metahash input: %s', self.address, unicode(self.address))
    mhash = util.hash_str(unicode(self.address))
    for src in self.rule.source_files or []:
      log.debug('[%s]: Metahash input: %s', self.address, src)
      mhash = util.hash_file(open(self.srcs_map[src], 'rb'), hasher=mhash)
    for dep in self.rule.composed_deps or []:
      dep_rule = self.rule.subgraph.node[dep]['target_obj']
      for item in dep_rule.output_files:
        log.debug('[%s]: Metahash input: %s', self.address, item)
        item_path = os.path.join(self.buildroot, item)
        mhash = util.hash_file(open(item_path, 'rb'),
                               hasher=mhash)
    return mhash

  def collect_outs(self):
    """Collect and store the outputs from this rule."""
    # TODO: this should probably live in CacheManager.
    for outfile in self.rule.output_files or []:
      outfile_built = os.path.join(self.buildroot, outfile)

      #git_sha = gitrepo.RepoState().GetRepo(self.address.repo).repo.commit()
      # TODO: git_sha enough is insufficient. More factors to include in hash:
      # - commit/state of source repo of all dependencies (or all input files?)
      #   - Actually I like that idea: hash all the input files!
      # - versions of build tools used (?)
      metahash = self._metahash()
      log.debug('[%s]: Metahash: %s', self.address, metahash.hexdigest())
      # TODO: record git repo state and buildoptions in cachemgr
      # TODO: move cachemgr to outer controller(?)
      self.cachemgr.putfile(outfile_built, self.buildroot, metahash)

  def prep(self):
    self.collect_srcs()
    self.collect_deps()

  def is_cached(self):
    try:
      for item in self.rule.output_files:
        log.info(item)
        self.cachemgr.in_cache(item, self._metahash())
    except cache.CacheMiss:
      log.info('[%s]: Not cached.', self.address)
      return False
    else:
      log.info('[%s]: found in cache.', self.address)
      return True

  def get_from_cache(self):
    """See if this rule has already been built and cached."""
    for item in self.rule.output_files:
      dstpath = os.path.join(self.buildroot, item)
      self.cachemgr.get_obj(item, self._metahash(), dstpath)

  def build(self):
    """Build the rule. Must be overridden by inheriting class."""
    raise NotImplementedError(self.rule.address)


class BaseTarget(object):
  """Partially abstract base class for build targets."""

  rulebuilder = BaseBuilder
  ruletype = None

  required_params = ['name']
  optional_params = {}

  def __init__(self, **kwargs):
    """Initialize the build rule.

    Args:
      **kwargs: Assorted parameters; see subclass implementations for details.
    """
    self.name = kwargs['name']
    self.address = address.new(self.name)
    self.subgraph = networkx.DiGraph()
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
          '[%s]: Unknown parameter(s): %s' % (
              self.name, ', '.join(kwargs.keys())))

  @property
  def output_files(self):
    """Returns the list of output files from this rule.

    Should be overridden by inheriting class.
    Paths are relative to buildroot.
    """
    raise NotImplementedError('[%s]: Implementation is broken.' % self.address)

  @property
  def composed_deps(self):
    """Dependencies of this build target."""
    if 'deps' in self.params:
      param_deps = self.params['deps'] or []
      deps = [ address.new(dep) for dep in param_deps ]
      for dep in deps:
        if dep.repo is None:
          dep.repo = self.address.repo
      return deps
    else:
      return None

  @property
  def source_files(self):
    """This rule's source files."""
    if 'srcs' in self.params:
      return self.params['srcs']
