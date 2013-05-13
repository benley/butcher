#!/usr/bin/python2.7
""" HI IT'S VINCE WITH SLAPCHOP """
#os.environ.update({'GIT_PYTHON_TRACE': 'full'})

# This is terrible and incomplete. Don't judge me :-P


import json
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


def parse_target(targetstr, current_repo=None):
  """Parse a build target string in the form //repo[gitref]/dir/path:targetname.

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
  log.debug('parse_target: %s -> %s', targetstr, groups)
  return groups


def resolve_target(targetstr, current_repo=None):
  """Resolve a targetstr into a "canonical-ish" version."""
  groups = parse_target(targetstr)
  if not groups['path']:
    groups['path'] = ''
  if groups['path']:
    groups['path'] = '/%s' % groups['path']
  if groups['repo'] is None:
    groups['repo'] = current_repo
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
    pp = parse_target(pin)
    pins[pp['repo']] = pp['git_ref']

  print "PINS: %s" % pins

  log.info('Building target: %s' % rtarget)
  params = parse_target(target)
  log.debug('Params: %s', params)

  try:
    repo = rstate.GetRepo(params['repo'], params['git_ref'])
  except gitrepo.GitError as err:
    log.fatal('Error while fetching //%s:', params['repo'])
    log.fatal(err)
    app.quit(1)

  if not already_built(repo, params):
    builddata = load_buildfile(repo, params)
    if 'repo' not in builddata:
      raise ButcherError('Object is missing a "repo" attribute.')

    repos_loaded = set()
    repo_queue = set()

    (reponame, subgraph, nextrepos) = parse(builddata)
    repos_loaded.add(reponame)
    repo_queue.update(nextrepos)
    repo_queue.difference_update(repos_loaded)

    while repo_queue:
      worklist = repo_queue.copy()
      for n_qrepo in worklist:
        log.info("####### %s", n_qrepo)
        if n_qrepo in pins:
          n_ref = pins[n_qrepo]
        else:
          n_ref = 'develop'
        n_repo = rstate.GetRepo(n_qrepo, n_ref)
        n_builddata = load_buildfile(n_repo)
        (n_reponame, n_subgraph, n_nextrepos) = parse(n_builddata)
        repos_loaded.add(n_reponame)
        repo_queue.discard(n_reponame)
        repo_queue.update(n_nextrepos)
        repo_queue.difference_update(repos_loaded)
        import networkx
        subgraph = networkx.compose(subgraph, n_subgraph)

    print('Repos loaded: %s' % repos_loaded)
    print('Repo queue: %s' % repo_queue)

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


def parse(builddata):
  reponame = '%s' % builddata['repo']
  subgraph = graph.ButcherGraph(name = reponame)
  nextrepos = set()
  #subgraph.add_node(reponame, {'repo': repo})
  if 'targets' in builddata:
    for target in builddata['targets']:
      targetname = '//%s:%s' % (reponame, target.pop('name'))
      t_node = nodes.node(targetname)
      subgraph.add_node(targetname, obj=t_node)
      if 'dependencies' in target:
        for dep in target['dependencies']:
          #TODO(ben): fully resolve dep name
          dep = resolve_target(dep, current_repo=reponame)
          dep_parsed = parse_target(dep)
          if dep_parsed['repo'] is None:
            dep_parsed['repo'] = reponame
          if 'repo' not in dep_parsed:
            dep_parsed['repo'] = reponame
          else:
            nextrepos.add(dep_parsed['repo'])
          d_node = nodes.node(dep)
          if dep not in subgraph.nodes():
            subgraph.add_node(dep, obj=d_node)
          subgraph.add_edge(targetname, dep)
      #subgraph.add_edge(reponame, targetname)
  return (reponame, subgraph, nextrepos)


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
