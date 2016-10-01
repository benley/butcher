# Copyright 2013 Cloudscaling Inc.

"""Git repository wrapper module."""

# If you want this, it has to happen before importing git, as silly as that is:
# os.environ.update({'GIT_PYTHON_TRACE': 'full'})

import git
import gitdb
import os
from pyglib import flags
from pyglib import log
from butcher import address

FLAGS = flags.FLAGS

flags.DEFINE_string('repo_baseurl', 'Base URL to git repo collection.',
                    'https://github.com')

flags.DEFINE_multistring(
    'pin', None,
    'Pin a repo to a particular symbolic ref. '
    'Syntax: //reponame[ref]')

flags.DEFINE_multistring(
    'map_repo', None,
    'Override the upstream location of a repo. '
    'Syntax: <reponame>:</path/to/repo>')

flags.DEFINE_string(
    'default_ref', 'master',
    'Default git symbolic ref to checkout if not pinned otherwise.')

# TODO: validate repo_overrides before starting any real work.
# TODO: a way to override the working copy location?
#        (in addition to map_repo, which just changes the upstream url)


class GitError(RuntimeError):
    """Generic error class."""
    pass


class RepoState(object):
    repos = {}
    pins = {}
    origin_overrides = {}
    repo_basedir = ''
    __init_done = False

    @classmethod
    def _init(cls):
        if cls.__init_done:
            return
        for override in FLAGS.map_repo or []:
            (reponame, path) = override.split(':')
            cls.origin_overrides[reponame] = os.path.abspath(
                os.path.expanduser(path))
        for pin in FLAGS.pin or []:
            ppin = address.new(pin)
            cls.pins[ppin.repo] = ppin.git_ref
        cls.repo_basedir = os.path.join(FLAGS.basedir, 'gitrepo')
        cls.__init_done = True

    @classmethod
    def get_repo(cls, reponame):
        if not cls.__init_done:
            cls._init()

        if reponame not in cls.repos:
            origin = cls.origin_overrides.get(reponame)
            ref = cls.pins.get(reponame)
            cls.repos[reponame] = GitRepo(reponame, ref, origin)

    @classmethod
    @property
    def heads(cls):
        """A list of all the currently-loaded repo HEAD objects."""
        return [
            (rname, repo.currenthead) for rname, repo in cls.repos.items()]


class GitRepo(object):
    """Git repository wrapper."""

    def __init__(self, name, ref=None, origin=None, repo_baseurl=None):
        self.repo_baseurl = repo_baseurl or FLAGS.repo_baseurl
        # log.debug('Base url: %s', self.repo_baseurl)
        self.repo_basedir = RepoState.repo_basedir
        # log.debug('Base directory: %s', self.repo_basedir)
        self.name = name
        # log.debug('Repo name: %s', self.name)
        self.ref = ref or FLAGS.default_ref

        self.origin_url = origin or '%s/%s' % (self.repo_baseurl, self.name)
        log.debug('[%s] Origin url: %s', self.name, self.origin_url)

        self.repodir = os.path.join(self.repo_basedir, self.name)
        log.debug('[%s] Working copy: %s', self.name, self.repodir)

        try:
            self.repo = git.Repo(self.repodir)
        except git.exc.NoSuchPathError:
            self.repo = git.Repo.init(self.repodir, bare=False)
            log.debug('[%s] Repo initialized.', self.name)
        except git.exc.InvalidGitRepositoryError:
            log.error(
                "[%s] %s exists, but is not a valid git repo. Can't continue.",
                self.name, self.repodir)
            raise GitError

        self.setorigin()
        self.fetchref(self.ref)
        self.sethead(self.ref)

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
            # Probably means we don't have it cached yet.
            # So maybe we can fetch it.
            ref = self.fetchref(ref)
        log.debug('[%s] Setting head to %s', self.name, ref)
        self.repo.head.reset(ref, working_tree=True)
        log.debug('[%s] Head object: %s', self.name, self.currenthead)

    @property
    def currenthead(self):
        """Returns the current head object."""
        return self.repo.head.object

    def get_file(self, filename):
        """Get a file from the repo.

        Returns a file-like stream with the data.
        """
        log.debug('[%s]: reading: //%s/%s', self.name, self.name, filename)
        try:
            blob = self.repo.head.commit.tree/filename
            return blob.data_stream
        except KeyError as err:
            raise GitError(err)
