#!/usr/bin/python2.7
# Copyright 2013 Cloudscaling Inc. All Rights Reserved.
#
# This is experimental and incomplete. Don't judge me :-P

"""Butcher: a distributed build system."""

__author__ = 'Benjamin Staffin <ben@cloudscaling.com>'

# If you want this, it has to happen before importing gitrepo:
#os.environ.update({'GIT_PYTHON_TRACE': 'full'})

import networkx
import os
import pprint
import shutil
from twitter.common import log
from twitter.common import app
from cloudscaling.buildy import buildfile
from cloudscaling.buildy import address
from cloudscaling.buildy import cache
from cloudscaling.buildy import error
from cloudscaling.buildy import gitrepo
from cloudscaling.buildy import util

app.add_option('--debug', action='store_true', dest='debug')
app.add_option('--basedir', dest='butcher_basedir',
               help='Base directory for butcher to work in.',
               default=os.path.join(util.user_homedir(), '_butcher.data'))
app.add_option('--build_root', dest='build_root', help=(
    'Base directory in which builds will be done. If unspecified, makes a '
    'build directory inside of the butcher basedir.'))

RepoState = gitrepo.RepoState


class Butcher(app.Module):
  """Butcher!"""

  def __init__(self):
    app.Module.__init__(self, label='butcher',
                        description='Butcher build system.',
                        dependencies='twitter.common.log')
    self.repo_state = RepoState()
    self.graph = networkx.DiGraph()
    # TODO: there isn't really a good reason to keep all the separate subgraphs.
    self.subgraphs = {}
    self.failure_log = []  # Build failure exceptions get kept in here.
    self.buildroot = None

  def setup_function(self):
    """Runs prior to the global main function."""
    log.options.LogOptions.set_stderr_log_level('google:INFO')
    if app.get_options().debug:
      log.options.LogOptions.set_stderr_log_level('google:DEBUG')
    if not app.get_options().build_root:
      app.set_option(
          'build_root', os.path.join(app.get_options().butcher_basedir, 'build'))
    self.buildroot = app.get_options().build_root
    if not os.path.exists(self.buildroot):
      os.makedirs(self.buildroot)

  def Clean(self):
    """Clear the contents of the build area."""
    if os.path.exists(self.buildroot):
      log.info('Clearing the build area.')
      log.debug('Deleting: %s', self.buildroot)
      shutil.rmtree(self.buildroot)
      os.makedirs(self.buildroot)

  def Build(self, explicit_target):
    if explicit_target not in self.graph.nodes():
      raise error.NoSuchTargetError('No rule defined for %s' % explicit_target)

    # Get the subgraph of only the things we need built.
    # (yes, topological sort accomplishes that)
    buildgraph = self.graph.subgraph(
        networkx.topological_sort(self.graph, nbunch=[explicit_target]))
    #if app.get_options().debug:
    #  log.debug('Buildgraph edges:\n%s', pprint.pformat(buildgraph.edges()))
    #  log.debug('Buildgraph nodes:\n%s', pprint.pformat(buildgraph.node))

    # TODO: this should be parallelized.

    # Caching notes:
    # - topological sort:
    #   - (that is, start at the root of the tree)
    #   - For each node,
    #     - IF nothing depends on it (i.e. it has no predecessors)
    #       AND it is not the explicit build target,
    #       - Remove it from the build tree (which may create more orphans to
    #         deal with in a later iteration)
    #     - ELSEIF it is in the build cache,
    #       - Mark it as built
    #       - Remove it from the build tree (which may create orphans to deal
    #         with in a later iteration)
    #     - ELSE:
    #       - Build it!
    #       - Send its outputs to the build cache
    #       - If it was the explicit build target, exit the loop.
    #       - Otherwise, remove it from the build tree and continue
    # - Next, if the explicit target hasn't already been built at this point,
    #   - Do a fresh *reverse* topological sort of the build graph, so nodes
    #     get built before the things that depend upon them.
    #   - Iterate over that list:
    #     - Build each node
    #     - Send it to the build cache
    #     - Remove it from the build tree
    # ... and at the end of all that the requested thing has been built.

    # This is probably going to end up iterating over all the nodes twice,
    # followed by a recursive build process that could technically accomplish
    # the same thing, but this method will reduce recursion depth. Not sure if
    # that will ever actually matter.

    # Iterate from the top of the tree, pruning based on cached/built status.
    #buildlist = networkx.topological_sort(buildgraph)
    #for node in buildlist:
    #  if node != explicit_target and not buildgraph.predecessors(node):
    #    # It's an orphaned node and we don't need it.
    #    buildgraph.remove_node(node)
    #    continue
    #  if self.already_built(node):
    #    # It's already built (or cached)
    #    buildgraph.remove_node(node)
    #    if node == explicit_target:
    #      # The explicitly requested target has already been built. Groovy.
    #      node_rule.get_from_cache()
    #      buildlist = []
    #      break

    # Now that we've pruned the tree, start building from the _bottom_.
    buildlist = networkx.topological_sort(buildgraph)
    buildlist.reverse()
    if buildlist:  # but sure there's actually anything left to do first.
      for node in buildlist:
        try:
          node_obj = buildgraph.node[node]['target_obj']
          node_builder = node_obj.rulebuilder(
              self.buildroot, node_obj,
              # TODO: this is absurd:
              self.repo_state.GetRepo(node.repo).repo.tree().abspath)
          node_builder.prep()
          try:
            node_builder.get_from_cache()
            log.info('[%s]: cache hit', node)
          except cache.CacheMiss as err:
            log.debug('[%s]: cache miss: %s', node, err)
            log.info('[%s]: Building.', node)
            node_builder.build()
            node_builder.collect_outs()
        except error.BuildFailure as err:
          log.error('[%s]: failed: %s', node, err)
          self.failure_log.append(err)
          break
        else:
          log.debug('[%s]: Build succeeded.', node)
          buildgraph.remove_node(node)

    if buildgraph.nodes():  # If the list isn't empty, the build failed.
      raise error.OverallBuildFailure('Build failed due to previous errors.')
    else:
      log.info('Success.', explicit_target)
      log.info('Outputs:')
      for item in self.graph.node[explicit_target]['target_obj'].output_files:
        log.info('  %s', os.path.join(self.buildroot, item))

  def LoadGraph(self, startingpoint):
    s_tgt = address.new(startingpoint, target='all')
    log.info('Loading graph starting at %s', s_tgt)
    s_subgraph = buildfile.load(self.load_buildfile(s_tgt),
                                s_tgt.repo, s_tgt.path)
    self.subgraphs[s_tgt] = s_subgraph
    self.graph = networkx.compose(self.graph, s_subgraph)

    while self.paths_wanted:
      log.debug('Loaded so far: %s', self.paths_loaded)
      log.debug('Unresolved nodes: %s', self.missing_nodes)
      n_tgt = self.paths_wanted.pop()
      if n_tgt in self.paths_loaded:
        mlist = ', '.join([ str(x) for x in self.missing_nodes ])
        raise error.BrokenGraph('Broken graph! Missing targets: %s' % mlist)
      n_subgraph = buildfile.load(self.load_buildfile(n_tgt),
                                  n_tgt.repo, n_tgt.path)
      self.subgraphs[n_tgt] = n_subgraph
      # Replace "missing" nodes with actual nodes:
      for node in self.missing_nodes.intersection(n_subgraph.nodes()):
        self.graph.node[node].update(n_subgraph.node[node])
      # Add the new nodes (attributes in self.graph take precedence here):
      self.graph = networkx.compose(self.graph, n_subgraph)

    # Traverse the graph and attach subgraphs to each node
    for node in self.graph.node:
      node_attrs = self.graph.node[node]
      subgraph = self.graph.subgraph(
          networkx.topological_sort(self.graph, nbunch=[node]))
      node_attrs['target_obj'].subgraph = subgraph

  @property
  def paths_loaded(self):
    """List of paths already visited and loaded."""
    return self.subgraphs.keys()

  @property
  def paths_wanted(self):
    """The set of paths where we expect to find missing nodes."""
    return set([ address.new(b, target='all') for b in self.missing_nodes ])

  @property
  def missing_nodes(self):
    """The set of build targets known as dependencies but not yet defined."""
    missing = set()
    for target_addr, target_attrs in self.graph.node.items():
      if 'target_obj' not in target_attrs:
        missing.add(target_addr)
    return missing

  def load_buildfile(self, target):
    """Pull a build file from git."""
    log.info('Loading: %s', target)
    filepath = os.path.join(target.path, 'OCS_BUILD.data')
    try:
      repo = self.repo_state.GetRepo(target.repo)
      return repo.get_file(filepath)
    except gitrepo.GitError as err:
      log.error('Failed loading %s: %s', target, err)
      raise error.BrokenGraph('Sadface.')

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
  print(address.new(args[0]))


@app.command
def build(args):
  """Build a target and its dependencies."""

  if not args:
    log.error('Target required.')
    app.quit(1)

  target = address.new(args[0])
  log.info('Resolved target to: %s', target)

  try:
    bb = Butcher()
    bb.LoadGraph(target)
    bb.Build(target)
  except (gitrepo.GitError,
          error.BrokenGraph,
          error.NoSuchTargetError) as err:
    log.fatal(err)
    app.quit(1)
  except error.OverallBuildFailure as err:
    log.fatal(err)
    log.fatal('Error list:')
    [ log.fatal('  [%s]: %s', e.node, e) for e in bb.failure_log ]


@app.command
def clean(args):
  """Akin to make clean"""
  bb = Butcher()
  bb.Clean()


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
    bb = Butcher()
    bb.LoadGraph(target)
  except error.BrokenGraph as lolno:
    log.fatal(lolno)
    app.quit(1)

  a = networkx.to_agraph(bb.graph)
  a.draw(out, prog='dot')
  log.info('Graph written to %s', out)


if __name__ == '__main__':
  app.register_module(Butcher())
  app.register_module(gitrepo.RepoState())
  app.register_module(cache.CacheManager())
  app.interspersed_args(True)
  app.main()
