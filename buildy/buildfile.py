"""BUILD file module.

We're using OCS_BUILD.data in place of BUILD for now.
"""

import json
import networkx
from cloudscaling.buildy import buildtarget
from cloudscaling.buildy import error
from cloudscaling.buildy import gitrepo
from twitter.common import log

BuildTarget = buildtarget.BuildTarget


def load(stream, reponame, path):
  for impl in (JsonBuildFile, PythonBuildFile):
    try:
      return impl(stream, reponame, path)
    except ValueError:
      raise error.ButcherError('Unable to parse this buildfile.')


class BuildFile(networkx.DiGraph):
  """Base class for build file implementations."""

  def __init__(self, stream, reponame, path=''):
    self.target = BuildTarget(repo=reponame, path=path)
    networkx.DiGraph.__init__(self, name=self.target)

    self._parse(stream)
    self.verify()

  def _parse(self, builddata):
    raise NotImplementedError

  def verify(self):
    """Freak out if there are missing local references."""
    for node in self.node:
      if 'build_data' not in self.node[node] and node not in self.crossrefs:
        raise error.BrokenGraph(
            'Missing target: %s referenced from %s but not defined there.' % (
            node, self.name))

  @property
  def crossrefs(self):
    """Returns a set of non-local targets referenced by this build file."""
    # TODO: memoize this.
    crefs = set()
    for node in self.node:
      if node.repo != self.target.repo or node.path != self.target.path:
        crefs.add(node)
    return crefs

  @property
  def crossref_paths(self):
    """Just like crossrefs, but all the targets are munged to :all."""
    return set([BuildTarget(repo=x.repo, path=x.path) for x in self.crossrefs])


class JsonBuildFile(BuildFile):
  """JSON OCS_BUILD.data."""

  def __init__(self, data, reponame, path=''):
    BuildFile.__init__(self, data, reponame, path)

    datadict = json.load(data)
    log.debug('This is a JSON build file.')
    self._parse(datadict)
    self.verify()

  def _parse(self, builddata):
    """Parse a JSON BUILD file.

    Args:
      builddata: dictionary of buildfile data
      reponame: name of the repo that it came from
      path: directory path within the repo
    """
    if 'targets' in builddata:
      for tdata in builddata['targets']:
        target = BuildTarget(target=tdata.pop('name'),
                             repo=self.target.repo, path=self.target.path)

        # Duplicate target definition? Uh oh.
        if target in self.node and 'build_data' in self.node[target]:
          raise error.ButcherError(
              'Target is defined more than once: %s', target)

        log.debug('New target: %s', target)
        self.add_node(target, {'build_data': tdata})

        if 'deps' in tdata:
          # dep could be ":blabla" or "//foo:blabla" or "//foo/bar:blabla"
          for dep in tdata.pop('deps'):
            d_target = BuildTarget(dep)
            if not d_target.repo:  # ":blabla"
              d_target.repo = self.target.repo
            if d_target.repo == self.target.repo and not d_target.path:
              d_target.path = self.target.path
            if d_target not in self.nodes():
              self.add_node(d_target)
            log.debug('New dep: %s -> %s', target, d_target)
            self.add_edge(target, d_target)
    # Add the :all node (unless it's explicitly defined in the build file...)
    if self.target not in self.node:
      self.add_node(self.target, {'build_data': {'type': 'virtual'}})
      for node in self.node:
        if node.repo == self.target.repo and node != self.target:
          self.add_edge(self.target, node)


class PythonBuildFile(BuildFile):
  """Python-based build file implementation!"""

  def _parse(self, stream):
    code = compile(stream.read(), self.target, 'exec')
