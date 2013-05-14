# Copyright 2013 Cloudscaling Inc. All Rights Reserved.

"""Git repository wrapper module."""

# If you want this, it has to happen before importing git, as silly as that is:
#os.environ.update({'GIT_PYTHON_TRACE': 'full'})

import git
import gitdb
import os
from twitter.common import app
from twitter.common import log

app.add_option('--repo_baseurl', dest='repo_baseurl',
               help='Base URL to git repo colleciton.')
app.add_option('--repo_basedir', dest='repo_basedir',
               help='Directory to contain git repository cache')


class GitError(RuntimeError):
  """Generic error class."""
  pass


class GitRepo(object):
  """Git repository wrapper."""
  defaults = {
      'repo_baseurl': 'ssh://pd.cloudscaling.com:29418',
      'repo_basedir': '/var/cache/butcher',
      }

  def __init__(self, name, ref='develop'):
    opts = app.get_options()
    self.repo_baseurl = opts.repo_baseurl or self.defaults['repo_baseurl']
    #log.debug('Base url: %s', self.repo_baseurl)

    self.repo_basedir = opts.repo_basedir or self.defaults['repo_basedir']
    #log.debug('Base directory: %s', self.repo_basedir)

    self.name = name
    #log.debug('Repo name: %s', self.name)

    self.origin_url = '%s/%s' % (self.repo_baseurl, self.name)
    log.debug('[%s] Fetching from: %s', self.name, self.origin_url)

    self.repodir = os.path.join(self.repo_basedir, self.name)
    log.debug('[%s] Repo dir: %s', self.name, self.repodir)

    try:
      self.repo = git.Repo(self.repodir)
    except git.exc.NoSuchPathError:
      self.repo = git.Repo.init(self.repodir, bare=False)
      log.debug('[%s] Repo initialized.', self.name)
    except git.exc.InvalidGitRepositoryError:
      log.error("[%s] %s exists, but is not a valid git repo. Can't continue.",
                self.name, self.repodir)
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
        log.debug('[%s] Changing origin url. Old: %s New: %s',
                  self.name, origin.url, self.origin_url)
        origin.config_writer.set('url', self.origin_url)
    except AttributeError:
      origin = self.repo.create_remote('origin', self.origin_url)
      log.debug('[%s] Created remote "origin" with URL: %s',
                self.name, origin.url)

  def fetchall(self):
    """Fetch all refs from the upstream repo."""
    try:
      self.repo.remotes.origin.fetch()
    except git.exc.GitCommandError as err:
      raise GitError(err)

  def fetchref(self, ref):
    """Fetch a particular git ref."""
    log.debug('[%s] Fetching ref: %s', self.name, ref)
    fetch_info = self.repo.remotes.origin.fetch(ref).pop()
    return fetch_info.ref

  def sethead(self, ref):
    """Set head to a git ref."""
    log.debug('[%s] Setting to ref %s', self.name, ref)
    try:
      ref = self.repo.rev_parse(ref)
    except gitdb.exc.BadObject:
      # Probably means we don't have it yet.
      ref = self.fetchref(ref)
    log.debug('[%s] Setting head to %s', self.name, ref)
    self.repo.head.reset(ref, working_tree=True)
    log.debug('[%s] Head object: %s', self.name, self.currenthead)

  @property
  def currenthead(self):
    """Returns the current head object."""
    return self.repo.head.object


