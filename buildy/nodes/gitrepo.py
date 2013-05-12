import git
import gitdb
import os
from twitter.common import app
from twitter.common import log
from .generic import GenericNode

app.add_option('--repo_baseurl', dest='repo_baseurl',
               help='Base URL to git repo colleciton.')
app.add_option('--repo_basedir', dest='repo_basedir',
               help='Directory to contain git repository cache')


class GitError(RuntimeError):
  """Generic error class."""
  pass


class GitRepo(GenericNode):
  """Manage git repositories."""
  defaults = {
      'repo_baseurl': 'ssh://pd.cloudscaling.com:29418',
      'repo_basedir': '/var/cache/butcher',
      }

  def __init__(self, reponame, ref='develop'):
    GenericNode.__init__(self, name=reponame)
    opts = app.get_options()
    self.repo_baseurl = opts.repo_baseurl or self.defaults['repo_baseurl']
    log.debug('Base url: %s', self.repo_baseurl)

    self.repo_basedir = opts.repo_basedir or self.defaults['repo_basedir']
    log.debug('Base directory: %s', self.repo_basedir)

    self.reponame = reponame
    log.debug('Repo name: %s', self.reponame)

    self.origin_url = '%s/%s' % (self.repo_baseurl, self.reponame)
    log.debug('Trusted origin URL: %s', self.origin_url)

    self.repodir = os.path.join(self.repo_basedir, self.reponame)
    log.debug('Repo dir: %s', self.repodir)

    try:
      self.repo = git.Repo(self.repodir)
    except git.exc.NoSuchPathError:
      self.repo = git.Repo.init(self.repodir, bare=False)
      log.info('Repo initialized.')
    except git.exc.InvalidGitRepositoryError:
      log.error("%s exists, but is not a valid git repo. Can't continue.",
                self.repodir)
      raise GitError

    self.setorigin()
    self.fetchall()
    if ref:
      self.sethead(ref)

  def setorigin(self):
    """Set the 'origin' remote to the upstream url that we trust."""
    try:
      origin = self.repo.remotes.origin
      if origin.url != self.origin_url:
        log.debug('Changing origin url. Old: %s New: %s', origin.url,
                  self.origin_url)
        origin.config_writer.set('url', self.origin_url)
    except AttributeError:
      origin = self.repo.create_remote('origin', self.origin_url)
      log.debug('Created remote "origin" with URL: %s', origin.url)

  def fetchall(self):
    try:
      self.repo.remotes.origin.fetch()
    except git.exc.GitCommandError as err:
      raise GitError(err)

  def fetchref(self, ref):
    """Fetch a particular git ref."""
    log.debug('Fetching ref: %s', ref)
    fetch_info = self.repo.remotes.origin.fetch(ref).pop()
    return fetch_info.ref

  def sethead(self, ref):
    """Set head to a git ref."""
    log.debug('Setting to ref %s', ref)
    try:
      ref = self.repo.rev_parse(ref)
    except gitdb.exc.BadObject:
      # Probably means we don't have it yet.
      ref = self.fetchref(ref)
    log.debug('Setting head to %s', ref)
    self.repo.head.reset(ref, working_tree=True)
    log.debug('Head object: %s', self.currenthead)

  @property
  def currenthead(self):
    return self.repo.head.object


