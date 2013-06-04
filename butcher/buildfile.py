"""BUILD file module.

We're using OCS_BUILD.data in place of BUILD for now.
"""

import json
import networkx
import os
import StringIO
from cloudscaling.butcher import address
from cloudscaling.butcher import buildfile_context
from cloudscaling.butcher import error
from cloudscaling.butcher import targets
from cloudscaling.butcher import gitrepo
from twitter.common import log


def load(stream, reponame, path):
  exception_list = []
  data = StringIO.StringIO(stream.read())
  for impl in (JsonBuildFile, PythonBuildFile):
    try:
      return impl(data, reponame, path)
    except ValueError as err:
      exception_list.append(err)
      data.seek(0)
  raise error.ButcherError('Unable to parse this buildfile: %s', exception_list)


class BuildFile(networkx.DiGraph):
  """Base class for build file implementations."""

  def __init__(self, stream, reponame, path=''):
    self.target = address.new(repo=reponame, path=path)
    self.address = self.target
    #TODO: finish the target->address refactor
    networkx.DiGraph.__init__(self, name=self.target)

    self._parse(stream)
    self.validate_internal_deps()

    # Add the :all node (unless it's explicitly defined in the build file...)
    #                   (note: please don't do that to yourself)
    if self.target not in self.node:
      log.debug('New target: %s', self.target)
      self.add_node(
          self.target,
          {'target_obj': targets.new(name=self.target,
                                     ruletype='virtual',
                                     deps=[x for x in self.local_targets])})

      for node in self.node:
        if node.repo == self.target.repo and node != self.target:
          log.debug('New dep: %s -> %s', self.target, node)
          self.add_edge(self.target, node)

  def get_repo(self):
    return gitrepo.RepoState().GetRepo(self.address.repo)

  @property
  def path_on_disk(self):
    return os.path.join(self.get_repo().repo.tree().abspath,
                        self.address.path)

  def _parse(self, stream):
    """Parse and load a stream's contents into the digraph."""
    raise NotImplementedError  # Must override in subclass.

  def validate_internal_deps(self):
    """Freak out if there are missing local references."""
    for node in self.node:
      if 'target_obj' not in self.node[node] and node not in self.crossrefs:
        raise error.BrokenGraph(
            'Missing target: %s referenced from %s but not defined there.' % (
            node, self.name))

  @property
  def crossrefs(self):
    """Returns a set of non-local targets referenced by this build file."""
    # TODO: memoize this?
    crefs = set()
    for node in self.node:
      if node.repo != self.target.repo or node.path != self.target.path:
        crefs.add(node)
    return crefs

  @property
  def crossref_paths(self):
    """Just like crossrefs, but all the targets are munged to :all."""
    return set([address.new(repo=x.repo, path=x.path) for x in self.crossrefs])

  @property
  def local_targets(self):
    """Iterator over the targets defined in this build file."""
    for node in self.node:
      if (node.repo, node.path) == (self.target.repo, self.target.path):
        yield node


class JsonBuildFile(BuildFile):
  """JSON OCS_BUILD.data."""

  def __init__(self, stream, reponame, path=''):
    BuildFile.__init__(self, stream, reponame, path)

  def _parse(self, stream):
    """Parse a JSON BUILD file.

    Args:
      builddata: dictionary of buildfile data
      reponame: name of the repo that it came from
      path: directory path within the repo
    """
    builddata = json.load(stream)
    log.debug('This is a JSON build file.')

    if 'targets' not in builddata:
      log.warn('Warning: No targets defined here.')
      return

    for tdata in builddata['targets']:
      # TODO: validate name
      target = address.new(target=tdata.pop('name'),
                           repo=self.target.repo,
                           path=self.target.path)
      # Duplicate target definition? Uh oh.
      if target in self.node and 'target_obj' in self.node[target]:
        raise error.ButcherError(
            'Target is defined more than once: %s', target)

      rule_obj = targets.new(name=target,
                             ruletype=tdata.pop('type'),
                             **tdata)

      log.debug('New target: %s', target)
      self.add_node(target, {'target_obj': rule_obj})

      # dep could be ":blabla" or "//foo:blabla" or "//foo/bar:blabla"
      for dep in rule_obj.composed_deps or []:
        d_target = address.new(dep)
        if not d_target.repo:  # ":blabla"
          d_target.repo = self.target.repo
        if d_target.repo == self.target.repo and not d_target.path:
          d_target.path = self.target.path
        if d_target not in self.nodes():
          self.add_node(d_target)
        log.debug('New dep: %s -> %s', target, d_target)
        self.add_edge(target, d_target)


class PythonBuildFile(BuildFile):
  """Python-based build file implementation!"""

  def __init__(self, stream, reponame, path=''):
    self.code = None
    BuildFile.__init__(self, stream, reponame, path)

  def _parse(self, stream):
    self.code = compile(stream.read(), str(self.target), 'exec')
    targets.base.BaseTarget.graphcontext = self
    # HACK ALERT: changing foreign module variables to set context...
    address.CUR_REPO = self.address.repo
    address.CUR_PATH = self.address.path
    context = buildfile_context.ParseContext(self)
    context.parse()

    for node in self.nodes():
      for dep in self.node[node]['target_obj'].composed_deps or []:
        d_target = address.new(dep)
        if not d_target.repo:
          d_target.repo = self.target.repo
        if d_target.repo == self.target.repo and not d_target.path:
          d_target.path = self.target.path
        if d_target not in self.nodes():
          self.add_node(d_target)
        log.debug('New dep: %s -> %s', node, d_target)
        self.add_edge(node, d_target)
    address.CUR_REPO = None
    address.CUR_PATH = ''
