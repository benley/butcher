#!/usr/bin/python2.7
""" HI IT'S VINCE WITH SLAPCHOP """
#import os
#os.environ.update({'GIT_PYTHON_TRACE': 'full'})

# This is terrible and incomplete. Don't judge me :-P


import json
import pprint
import re
from twitter.common import log
from twitter.common import app
from cloudscaling.buildy import graph
from cloudscaling.buildy import nodes

app.add_option('--repo_baseurl', dest='repo_baseurl',
               help='Base URL to git repo colleciton.')
app.add_option('--repo_basedir', dest='repo_basedir',
               help='Directory to contain git repository cache')
app.add_option('--debug', action='store_true', dest='debug')



class ButcherError(RuntimeError):
  """Generic error class."""
  pass


def parse_target(targetstr):
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
      r'(?:$|/?(?P<path>[\w/]+)?(?::?(?P<target>\w+)?))', targetstr)
  try:
    groups = match.groupdict()
    if not groups['git_ref']:
      groups['git_ref'] = 'develop'
    if not groups['target']:
      groups['target'] = 'all'
    return groups
  except AttributeError:
    raise ButcherError('"%s" is not a valid build target.')


def resolve_target(targetstr, current_repo=None):
  """Resolve a targetstr into a "canonical-ish" version."""
  groups = parse_target(targetstr)
  if not groups['path']:
    groups['path'] = ''
  if groups['path']:
    groups['path'] = '/%s' % groups['path']
  if groups['repo'] is None:
    groups['repo'] = current_repo
  return '//%(repo)s[%(git_ref)s]%(path)s:%(target)s' % groups


@app.command
def resolve(args):
  """Just print the result of parsing a target string."""
  if not args:
    log.error('Argument required.')
    app.quit(1)
  print resolve_target(args[0])


@app.command
def build(args):
  """Build a target and its dependencies."""
  if not args:
    log.error('Argument required.')
    app.quit(1)
  target = args[0]
  rtarget = resolve_target(target)
  if rtarget != target:
    log.info('Resolved target to: %s', rtarget)
  log.info('Building target: %s' % rtarget)
  params = parse_target(rtarget)
  log.debug('Params: %s', params)

  try:
    repo = nodes.GitRepo(params['repo'])
    repo.sethead(params['git_ref'])
    #sha = repo.repo.head.commit
  except nodes.GitError as err:
    log.fatal('Error while fetching //%s:', params['repo'])
    log.fatal(err)
    app.quit(1)

  # This is where I left off:
  if not already_built(repo, params):
    builddata = load_buildfile(repo, params)
    if 'repo' not in builddata:
      raise ButcherError('Object is missing a "repo" attribute.')

    repos_loaded = set()
    repo_queue = set()

    (reponame, subgraph, nextrepos) = parse(builddata)
    repos_loaded.add(reponame)
    repo_queue.union(nextrepos)

    print('Repos loaded: %s' % repos_loaded)
    print('Repo queue: %s' % repo_queue)

    for node in subgraph.nodes():
      print "Node: %s\tHash: %s" % (node, hash(node))
    pprint.pprint(subgraph.nodes())
    for (a, b) in subgraph.edges():
      print "a: %s %s" % (a, hash(a))
      print "b: %s %s" % (b, hash(b))
    pprint.pprint(subgraph.edges())

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


def load_buildfile(repo, params):
  prefix = params['path'] or ''
  if prefix and not prefix.endswith('/'):
    prefix = prefix + '/'
  filepath = '%sOCS_BUILD.data' % prefix  # FIXME: this filename
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
  app.set_option('twitter_common_log_stderr_log_level', 'google:DEBUG')
  app.main()
