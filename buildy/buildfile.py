"""BUILD file module.

We're using OCS_BUILD.data in place of BUILD for now.
"""

import networkx
from cloudscaling.buildy import buildtarget
from cloudscaling.buildy import error

BuildTarget = buildtarget.BuildTarget


class BuildFile(networkx.DiGraph):
  """BUILD data."""

  def __init__(self, data, reponame, path=''):
    self.target = BuildTarget(repo=reponame, path=path)
    networkx.DiGraph.__init__(self, name=self.target)

    self._parse(data)

  def _parse(self, builddata):
    """Parse a BUILD file.

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
        if target in self.node and self.node[target]['build_data'] is not None:
          raise error.ButcherError(
              'Target is defined more than once: %s', target)

        self.add_node(target, {'build_data': tdata})

        if 'dependencies' in tdata:
          # dep could be ":blabla" or "//foo:blabla" or "//foo/bar:blabla"
          for dep in tdata.pop('dependencies'):
            d_target = BuildTarget(dep)
            if not d_target.repo:  # ":blabla"
              d_target['repo'] = self.target.repo
              d_target['path'] = self.target.path
            if d_target not in self.nodes():
              self.add_node(d_target, {'build_data': None})
            self.add_edge(target, d_target)

  @property
  def crossrefs(self):
    """Returns a set of non-local targets referenced by this build file."""
    # TODO: memoize this.
    crefs = set()
    for node in self.node:
      if node.repo != self.target.repo or node.path != self.target.path:
        crefs.add(node)
    return crefs

  def verify(self):
    """Freak out if there are missing local references."""
    for node in self.node:
      if not self.node[node]['build_data'] and node not in self.crossrefs:
        raise error.ButcherError(
            'Missing target: %s referenced from %s but not defined there.',
            node, self.name)
