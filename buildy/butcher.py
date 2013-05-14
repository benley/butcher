#!/usr/bin/python2.7
# Copyright 2013 Cloudscaling Inc. All Rights Reserved.
#
# This is terrible and incomplete. Don't judge me :-P

"""Butcher: a distributed build system."""

__author__ = 'Benjamin Staffin <ben@cloudscaling.com>'

# If you want this, it has to happen before importing gitrepo:
#os.environ.update({'GIT_PYTHON_TRACE': 'full'})

import json
import networkx
import os
import pprint
import re
from twitter.common import log
from twitter.common import app
from cloudscaling.buildy import graph
from cloudscaling.buildy import gitrepo
from cloudscaling.buildy import nodes

app.add_option('--debug', action='store_true', dest='debug')
app.add_option('--pin', action='append', dest='pinned_repos')


class ButcherLogSubsystem(app.Module):
  """This is just here to override logging options at runtime."""

  def __init__(self):
    app.Module.__init__(self, __name__, description='Butcher logging subsystem',
                        dependencies='twitter.common.log')

  def setup_function(self):
    """Runs prior to the main function."""
    if app.get_options().debug:
      log.options.LogOptions.set_stderr_log_level('google:DEBUG')


class ButcherError(RuntimeError):
  """Generic error class."""
  pass


class Butcher(object):
  """Butcher."""

  def __init__(self):
    self.graph = networkx.DiGraph()


class Target(dict):
  """A build target."""

  # The components that make up a build target:
  params = ('repo', 'git_ref', 'path', 'target')

  def __init__(self, *args, **kwargs):
    dict.__init__(self, {'repo': None, 'git_ref': '',
                         'path': '', 'target': 'all'})
    self.update(*args, **kwargs)

  def __hash__(self):
    return hash(self.__repr__())

  def __eq__(self, other):
    return repr(self) == repr(other)

  def update(self, iterable=None, **kwargs):
    if iterable:
      if '__iter__' in type(iterable).__dict__:
        if 'keys' in type(iterable).__dict__:
          for k in iterable:
            self[k] = iterable[k]
        else:
          for (k, val) in iterable:
            self[k] = val
      else:
        self.update(self.__parse_target(iterable))
    for k in kwargs:
      self[k] = kwargs[k]

  def __setitem__(self, key, value):
    if key not in ('repo', 'git_ref', 'path', 'target'):
      raise ButcherError('Invalid parameter: %s' % key)
    # TODO: value validation
    dict.__setitem__(self, key, value)

  def __repr__(self):
    if self.repo is None or self.target is None:
      raise ButcherError('No valid repr for this incomplete target.')

    ret = ['//%(repo)s' % dict(self)]
    if self['path']:
      ret.append('/%s' % self['path'])
    ret.append(':%(target)s' % self)
    return ''.join(ret)

  @property
  def repo(self):
    return self['repo']

  @property
  def git_ref(self):
    return self['git_ref']

  @property
  def path(self):
    return self['path']

  @property
  def target(self):
    return self['target']

  @staticmethod
  def __parse_target(targetstr, current_repo=None):
    """Parse a build target string in the form //repo[gitref]/dir/path:target.

    These are all valid:
      //repo
      //repo[a038fi31d9e8bc11582ef1b1b1982d8fc]
      //repo[a039aa30853298]:foo
      //repo/dir
      //repo[a037928734]/dir
      //repo/dir/path
      //repo/dir/path:foo
      :foo
      dir/path
      dir/path:foo
      dir:foo

    Returns: {'repo': '//reponame',
              'git_ref': 'a839a38fd...',
              'path': 'dir/path',
              'target': 'targetname}
    """
    match = re.match(
        r'^(?://(?P<repo>[\w-]+)(?:\[(?P<git_ref>.*)\])?)?'
        r'(?:$|/?(?P<path>[\w/-]+)?(?::?(?P<target>[\w-]+)?))', targetstr)
    try:
      groups = match.groupdict()
      if not groups['repo']:
        groups['repo'] = current_repo
      if not groups['git_ref']:
        groups['git_ref'] = 'develop'
      if not groups['target']:
        groups['target'] = 'all'
      if not groups['path']:
        groups['path'] = ''
    except AttributeError:
      raise ButcherError('"%s" is not a valid build target.')
    #log.debug('parse_target: %s -> %s', targetstr, groups)
    return groups


def resolve_target(targetstr, current_repo=None, path=None):
  """Resolve a targetstr into a "canonical-ish" version."""
  groups = Target(targetstr)

  if not groups['path']:  # It comes out None if missing.
    groups['path'] = ''
  if groups['path']:
    groups['path'] = '/%s' % groups['path']
  elif path:
    if not path.startswith('/'):
      groups['path'] = '/%s' % path
    else:
      groups['path'] = path

  if not groups['repo']:
    if current_repo:
      groups['repo'] = current_repo
    else:
      raise ButcherError('Can\'t resolve "%s" without the current repo name.')
  #return '//%(repo)s[%(git_ref)s]%(path)s:%(target)s' % groups
  return '//%(repo)s%(path)s:%(target)s' % groups


@app.command
def resolve(args):
  """Just print the result of parsing a target string."""
  if not args:
    log.error('Argument required.')
    app.quit(1)
  print(Target(args[0]))


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
def build(args):
  """Build a target and its dependencies."""

  if not args:
    log.error('Target required.')
    app.quit(1)

  target = Target(args[0])
  log.info('Resolved target to: %s', target)

  rstate = RepoState()
  pins = {}
  for pin in app.get_options().pinned_repos:
    ppin = Target(pin)
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
      target = Target(target=tdata.pop('name'), repo=reponame, path=path)
      #t_node = nodes.node(targetname)
      #subgraph.add_node(targetname, obj=t_node)
      subgraph.add_node(target, {'build_data': tdata})
      if 'dependencies' in tdata:
        for dep in tdata['dependencies']:
          dep_parsed = Target(dep)
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
  log.debug('Repo %s: loading buildfile: /%s', repo.name, filepath)
  blob = repo.repo.head.commit.tree/filepath
  data = blob.data_stream.read()
  return json.loads(data)


def already_built(target):
  """Stub. Always returns False."""
  # FIXME: implement or obviate.
  _ = target.repo
  return False


if __name__ == '__main__':
  app.register_module(ButcherLogSubsystem())
  app.main()
