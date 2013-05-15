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
from cloudscaling.buildy import error
from cloudscaling.buildy import graph
from cloudscaling.buildy import gitrepo
from cloudscaling.buildy import nodes
from cloudscaling.buildy import buildtarget

app.add_option('--debug', action='store_true', dest='debug')
app.add_option('--pin', action='append', dest='pinned_repos')

BuildTarget = buildtarget.BuildTarget


class ButcherLogSubsystem(app.Module):
  """This is just here to override logging options at runtime."""

  def __init__(self):
    app.Module.__init__(self, __name__, description='Butcher logging subsystem',
                        dependencies='twitter.common.log')

  def setup_function(self):
    """Runs prior to the main function."""
    if app.get_options().debug:
      log.options.LogOptions.set_stderr_log_level('google:DEBUG')


class Butcher(object):
  """Butcher."""

  def __init__(self):
    self.graph = networkx.DiGraph()


class RepoState(object):
  """Hold git repo state."""
  def __init__(self):
    self.repos = {}

  def GetRepo(self, reponame, ref=None):
    if reponame not in self.repos:
      self.repos[reponame] = gitrepo.GitRepo(reponame, ref)
      return self.repos[reponame]

  def HeadList(self):
    return [(rname, repo.currenthead) for rname, repo in self.repos.items()]


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

  rstate = RepoState()
  pins = {}
  for pin in app.get_options().pinned_repos:
    ppin = BuildTarget(pin)
    pins[ppin.repo] = ppin.git_ref

  log.debug('Pinned refs: %s', pins)

  log.info('Building target: %s' % target)

  if not already_built(target):
    log.info('####### Loading repo: %s', target.repo)
    try:
      repo = rstate.GetRepo(target.repo, target.git_ref)
    except gitrepo.GitError as err:
      log.fatal('Error while fetching //%s:', target.repo)
      log.fatal(err)
      app.quit(1)

    builddata = load_buildfile(repo, target.path)

    repos_loaded = set()
    repo_queue = set()
    build_queue = set()

    (subgraph, nextrepos) = parse(builddata, repo.name, target.path)
    repos_loaded.add(repo.name)
    repo_queue.update(nextrepos)
    repo_queue.difference_update(repos_loaded)
    if target.target == 'all':
      for tgt in subgraph.nodes():
        if tgt.repo == repo.name:
          build_queue.add(tgt)

    while repo_queue:
      log.debug('Repos loaded: %s', ', '.join(repos_loaded))
      log.debug('Repo queue: %s', ', '.join(repo_queue))
      worklist = repo_queue.copy()
      for n_reponame in worklist:
        log.info("####### Loading repo: %s", n_reponame)
        if n_reponame in pins:
          n_ref = pins[n_reponame]
        else:
          n_ref = 'develop'
        n_repo = rstate.GetRepo(n_reponame, n_ref)
        n_builddata = load_buildfile(n_repo)
        (n_subgraph, n_nextrepos) = parse(n_builddata, n_repo.name)
        repos_loaded.add(n_reponame)
        repo_queue.discard(n_reponame)
        repo_queue.update(n_nextrepos)
        repo_queue.difference_update(repos_loaded)
        subgraph = networkx.compose(subgraph, n_subgraph)

    log.debug('Repos loaded: %s', ', '.join(repos_loaded))
    log.debug('Repo queue: %s', ', '.join(repo_queue))
    log.debug('Build queue: %s', ', '.join([str(x) for x in build_queue]))

    print('REPO STATE:')
    print rstate.HeadList()

    print('graph:')
    pprint.pprint(subgraph.node)
    print('edges:')
    pprint.pprint(subgraph.edge)

    # Load dependency graph by recursively parsing BUILD files
    # Decorate nodes with buildcache status
    # Depth first search:
    #  - find unbuilt leaves with satisfied deps or no deps.
    #  - enqueue them for build
    # Continue until the final target is built.

  # Also:
  # - deal with storing build outputs somewhere
  # - a way to retrieve prebuilt objects from BCS or equivalent


def parse(builddata, reponame, path=None):
  """Parse a BUILD file.

  Args:
    builddata: dictionary of buildfile data
    reponame: name of the repo that it came from
    path: directory path within the repo

  Returns:
    (DiGraph of this BUILD file, list of repos it refers to)
  """
  subgraph = networkx.DiGraph()
  nextrepos = set()
  #subgraph.add_node(reponame, {'repo': repo})
  if 'targets' in builddata:
    for tdata in builddata['targets']:
      target = BuildTarget(target=tdata.pop('name'), repo=reponame, path=path)
      #t_node = nodes.node(targetname)
      #subgraph.add_node(targetname, obj=t_node)
      subgraph.add_node(target, {'build_data': tdata})
      if 'dependencies' in tdata:
        for dep in tdata['dependencies']:
          dep_parsed = BuildTarget(dep)
          if not dep_parsed.repo:
            dep_parsed['repo'] = reponame
          if not dep_parsed.path:
            dep_parsed['path'] = path
          nextrepos.add(dep_parsed.repo)
          #d_node = nodes.node(dep)
          if dep_parsed not in subgraph.nodes():
            #subgraph.add_node(dep, obj=d_node)
            subgraph.add_node(dep_parsed, {'build_data': {}})
          subgraph.add_edge(target, dep_parsed)
      #subgraph.add_edge(reponame, targetname)
  return (subgraph, nextrepos)


def load_buildfile(repo, path=''):
  filepath = os.path.join(path, 'OCS_BUILD.data')
  return json.load(repo.get_file(filepath))


def already_built(target):
  """Stub. Always returns False."""
  # FIXME: implement or obviate.
  _ = target.repo
  return False


if __name__ == '__main__':
  app.register_module(ButcherLogSubsystem())
  app.interspersed_args(True)
  app.main()
