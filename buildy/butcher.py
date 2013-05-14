#!/usr/bin/python2.7
""" HI IT'S VINCE WITH SLAPCHOP """
#os.environ.update({'GIT_PYTHON_TRACE': 'full'})

# This is terrible and incomplete. Don't judge me :-P


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

  def __init__(self, *args, **kwargs):
    dict.__init__(self, {'repo': None, 'git_ref': '',
                         'path': '', 'target': 'all'})
    self.update(*args, **kwargs)

  def update(self, iterable=None, **kwargs):
    if iterable:
      if '__iter__' in type(iterable).__dict__:
        if 'keys' in type(iterable).__dict__:
          for k in iterable:
            self[k] = iterable[k]
        else:
          for (k, v) in iterable: self[k] = v
      else:
        self.update(self.__parse_target(iterable))
    for k in kwargs:
      self[k] = kwargs[k]

  # TODO: __getitem__ and __setitem__ and maybe __repr__
  # See http://stackoverflow.com/a/2390997

  def __str__(self):
    if None in self.values():
      # TODO: does this make sense?
      return 'INCOMPLETE'
    ret = ['//%(repo)s' % dict(self)]
    if self['path']:
      ret.append('/%s' % self['path'])
    ret.append(':%(target)s' % self)
    return ''.join(ret)

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
  print resolve_target(args[0])

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
  rstate = RepoState()

  if not args:
    log.error('Argument required.')
    app.quit(1)
  target = args[0]
  rtarget = resolve_target(target)
  if rtarget != target:
    log.info('Resolved target to: %s', rtarget)

  pins = {}
  for pin in app.get_options().pinned_repos:
    ppin = Target(pin)
    pins[ppin['repo']] = ppin['git_ref']

  print "PINS: %s" % pins

  log.info('Building target: %s' % rtarget)
  params = Target(target)
  #params = parse_target(target)
  #log.debug('Params: %s', params)

  if not already_built(params['repo'], params):
    log.info('####### Loading repo: %s', params['repo'])
    try:
      repo = rstate.GetRepo(params['repo'], params['git_ref'])
    except gitrepo.GitError as err:
      log.fatal('Error while fetching //%s:', params['repo'])
      log.fatal(err)
      app.quit(1)

    builddata = load_buildfile(repo, params)

    repos_loaded = set()
    repo_queue = set()

    (subgraph, nextrepos) = parse(builddata, repo.name, params['path'])
    repos_loaded.add(repo.name)
    repo_queue.update(nextrepos)
    repo_queue.difference_update(repos_loaded)

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

    print('REPO STATE:')
    print rstate.HeadList()

    print('graph:')
    print subgraph.node
    print('edges:')
    print subgraph.edge

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
    for target in builddata['targets']:
      targetname = resolve_target(target.pop('name'), reponame, path)
      #t_node = nodes.node(targetname)
      #subgraph.add_node(targetname, obj=t_node)
      subgraph.add_node(targetname, {'build_data': target})
      if 'dependencies' in target:
        for dep in target['dependencies']:
          #TODO(ben): fully resolve dep name
          dep = resolve_target(dep, current_repo=reponame)
          dep_parsed = Target(dep)
          if dep_parsed['repo'] is None:
            dep_parsed['repo'] = reponame
          if 'repo' not in dep_parsed:
            dep_parsed['repo'] = reponame
          else:
            nextrepos.add(dep_parsed['repo'])
          #d_node = nodes.node(dep)
          if dep not in subgraph.nodes():
            #subgraph.add_node(dep, obj=d_node)
            subgraph.add_node(dep, {'build_data': target})
          subgraph.add_edge(targetname, dep)
      #subgraph.add_edge(reponame, targetname)
  return (subgraph, nextrepos)


def load_buildfile(repo, params=None):
  if params:
    prefix = params['path'] or ''
  else:
    prefix = ''
  filepath = os.path.join(prefix, 'OCS_BUILD.data')
  log.debug('Repo %s: loading buildfile: %s', repo.name, filepath)
  blob = repo.repo.head.commit.tree/filepath
  data = blob.data_stream.read()
  return json.loads(data)


def already_built(repo, params):
  """Stub. Always returns False."""
  # FIXME: implement or obviate.
  _ = repo
  _ = params
  return False


if __name__ == '__main__':
  app.register_module(ButcherLogSubsystem())
  app.main()
