#!/usr/bin/python2.7
# Copyright 2013 Cloudscaling Inc. All Rights Reserved.
#
# This is experimental and incomplete. Don't judge me :-P

"""Butcher: a distributed build system."""

__author__ = 'Benjamin Staffin <ben@cloudscaling.com>'

# If you want this, it has to happen before importing gitrepo:
#os.environ.update({'GIT_PYTHON_TRACE': 'full'})

import json
import networkx
import os
import pprint
from twitter.common import log
from twitter.common import app
from cloudscaling.buildy import buildfile
from cloudscaling.buildy import buildtarget
from cloudscaling.buildy import error
from cloudscaling.buildy import graph
from cloudscaling.buildy import gitrepo
from cloudscaling.buildy import nodes

app.add_option('--debug', action='store_true', dest='debug')
app.add_option('--pin', action='append', dest='pinned_repos')

BuildFile = buildfile.BuildFile
BuildTarget = buildtarget.BuildTarget
RepoState = gitrepo.RepoState


class ButcherLogSubsystem(app.Module):
  """This is just here to override logging options at runtime."""

  def __init__(self):
    app.Module.__init__(self, __name__, description='Butcher logging subsystem',
                        dependencies='twitter.common.log')

  def setup_function(self):
    """Runs prior to the main function."""
    log.options.LogOptions.set_stderr_log_level('google:INFO')
    if app.get_options().debug:
      log.options.LogOptions.set_stderr_log_level('google:DEBUG')


class Butcher(object):
  """Butcher."""

  def __init__(self, target=None):
    # TODO: pins should go in RepoState, don't you think?
    self.repo_state = RepoState()
    self.pins = {}
    pins = app.get_options().pinned_repos
    for pin in (pins or []):
      ppin = BuildTarget(pin)
      self.pins[ppin.repo] = ppin.git_ref

    self.graph = networkx.DiGraph()
    self.subgraphs = {}
    if target:
      self.LoadGraph(target)

  def Build(self, target):
    log.info('Building target: %s' % target)
    log.info('(not yet implemented)')
    # This is where it gets interesting now.
    # Decorate nodes with buildcache status
    # Depth first search:
    #  - find unbuilt leaves with satisfied deps or no deps.
    #  - enqueue them for build
    # Continue until the final target is built.

    # Also:
    # - deal with storing build outputs somewhere
    # - a way to retrieve prebuilt objects from BCS or equivalent

    # Get the subgraph of only the things we need built.
    buildgraph = self.graph.subgraph(
        networkx.topological_sort(self.graph, nbunch=[target]))
    if app.get_options().debug:
      log.debug('Buildgraph edges:')
      pprint.pprint(buildgraph.node)
      log.debug('Buildgraph nodes:')
      pprint.pprint(buildgraph.edges())

    # TODO: this should be parallelized.

  def LoadGraph(self, startingpoint):
    s_tgt = BuildTarget(startingpoint)
    log.info('Loading graph starting at %s', s_tgt)
    s_tgt.target = 'all'  # This is being used for repo, ref, path - not target.
    s_repo = self.repo_state.GetRepo(s_tgt.repo, s_tgt.git_ref)
    s_data = self.load_buildfile(s_repo, s_tgt.path)
    s_subgraph = BuildFile(s_data, s_tgt.repo, s_tgt.path)
    self.subgraphs[s_tgt] = s_subgraph
    self.graph = networkx.compose(self.graph, s_subgraph)

    while self.paths_wanted:
      log.debug('Loaded so far: %s', self.paths_loaded)
      log.debug('Unresolved nodes: %s', self.missing_nodes)
      n_tgt = self.paths_wanted.pop()
      if n_tgt in self.paths_loaded:
        mlist = ', '.join([ str(x) for x in self.missing_nodes ])
        raise error.BrokenGraph('Broken graph! Missing targets: %s' % mlist)
      # TODO: This pinning stuff really doesn't belong here.
      if n_tgt.repo in self.pins:
        n_tgt.git_ref = self.pins[n_tgt.repo]
      else:
        n_tgt.git_ref = 'develop'
      n_repo = self.repo_state.GetRepo(n_tgt.repo, n_tgt.git_ref)
      n_subgraph = BuildFile(self.load_buildfile(n_repo, n_tgt.path),
                             n_tgt.repo, n_tgt.path)
      self.subgraphs[n_tgt] = n_subgraph
      # Replace "missing" nodes with actual nodes:
      for node in self.missing_nodes.intersection(n_subgraph.nodes()):
        self.graph.node[node].update(n_subgraph.node[node])
      # Add the new nodes (attributes in self.graph take precedence here):
      self.graph = networkx.compose(self.graph, n_subgraph)

  @property
  def paths_loaded(self):
    """List of paths already visited and loaded."""
    return self.subgraphs.keys()

  @property
  def paths_wanted(self):
    """The set of paths where we expect to find missing nodes."""
    return set([ BuildTarget(b, target='all') for b in self.missing_nodes ])

  @property
  def missing_nodes(self):
    """The set of build targets known as dependencies but not yet defined."""
    missing = set()
    for k, v in self.graph.node.items():
      if 'build_data' not in v:
        missing.add(k)
    return missing

  def load_buildfile(self, repo, path=''):
    """Pull a json build file from git and return it as a dictionary."""
    log.info('Loading: %s', BuildTarget(repo=repo.name, path=path))
    filepath = os.path.join(path, 'OCS_BUILD.data')
    return json.load(repo.get_file(filepath))


  def already_built(self, target):
    """Stub. Always returns False."""
    # FIXME: implement or obviate.
    # This may end up in a cache server interface class.
    _ = target.repo
    return False


@app.command
def resolve(args):
  """Just print the result of parsing a target string."""
  if not args:
    log.error('Exactly 1 argument is required.')
    app.quit(1)
  print(BuildTarget(args[0]))


@app.command
def build(args):
  """Build a target and its dependencies."""

  if not args:
    log.error('Target required.')
    app.quit(1)

  target = BuildTarget(args[0])
  log.info('Resolved target to: %s', target)

  try:
    bb = Butcher()
    bb.LoadGraph(target)
    bb.Build(target)
  except error.BrokenGraph as lolno:
    log.fatal(lolno)
    app.quit(1)


@app.command
def dump(args):
  """Load the build graph for a target and dump it to stdout."""
  try:
    bb = Butcher(args[0])
  except error.BrokenGraph as lolno:
    log.fatal(lolno)
    app.quit(1)
  print "Nodes:"
  pprint.pprint(bb.graph.node)
  print "Edges:"
  pprint.pprint(bb.graph.edge)


@app.command
def draw(args):
  """Load the build graph for a target and render it to an image."""
  if len(args) != 2:
    log.error('Two arguments required: [build target] [output file]')
    app.quit(1)

  target = args[0]
  out = args[1]

  try:
    bb = Butcher(target)
  except error.BrokenGraph as lolno:
    log.fatal(lolno)
    app.quit(1)

  a = networkx.to_agraph(bb.graph)
  a.draw(out, prog='dot')
  log.info('Graph written to %s', out)


if __name__ == '__main__':
  app.register_module(ButcherLogSubsystem())
  app.interspersed_args(True)
  app.main()
