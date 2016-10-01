# Copyright 2013 Cloudscaling Inc.

"""Git repository wrapper module."""

# If you want this, it has to happen before importing git, as silly as that is:
#os.environ.update({'GIT_PYTHON_TRACE': 'full'})

import git
import gitdb
import os
from twitter.common import app
from twitter.common import log
from butcher import address

app.add_option('--repo_baseurl', dest='repo_baseurl',
               help='Base URL to git repo collection.',
               default='https://github.com/benley')
app.add_option(
    '--pin', action='append', dest='pinned_repos',
    help='Pin a repo to a particular symbolic ref. Syntax: //reponame[ref]')
app.add_option(
    '--map_repo', action='append', dest='repo_overrides',
    help=('Override the upstream location of a repo. '
          'Format: <reponame>:</path/to/repo>'))
app.add_option(
    '--default_ref', dest='default_ref', default='HEAD',
    help='Default git symbolic ref to checkout if not pinned otherwise.')

# TODO: validate repo_overrides before starting any real work.
# TODO: a way to override the working copy location?
#        (in addition to map_repo, which just changes the upstream url)


class GitError(RuntimeError):
    """Generic error class."""
    pass


class RepoState(app.Module):
    """Holds git repo state. Singleton thanks to app.Module."""
    repos = {}
    pins = {}
    origin_overrides = {}
    repo_basedir = ''

    def __init__(self):
        app.Module.__init__(self, label=__name__,
                            description='Git repo subsystem.')

    def setup_function(self):
        overrides = app.get_options().repo_overrides
        if overrides:
            for line in overrides:
                (reponame, path) = line.split(':')
                self.origin_overrides[reponame] = os.path.abspath(
                    os.path.expanduser(path))
        pins = app.get_options().pinned_repos
        for pin in (pins or []):
            ppin = address.new(pin)
            self.pins[ppin.repo] = ppin.git_ref
        self.repo_basedir = os.path.join(app.get_options().butcher_basedir,
                                         'gitrepo')

    def GetRepo(self, reponame):
        if reponame not in self.repos:
            origin = None
            if reponame in self.origin_overrides:
                origin = self.origin_overrides[reponame]
            ref = None
            if reponame in self.pins:
                ref = self.pins[reponame]
            self.repos[reponame] = GitRepo(reponame, ref, origin=origin)
        return self.repos[reponame]

    def HeadList(self):
        """Return a list of all the currently loaded repo HEAD objects."""
        return [(rname, repo.currenthead) for rname, repo in self.repos.items()
                ]


class GitRepo(object):
    """Git repository wrapper."""

    def __init__(self, name, ref=None, origin=None):
        opts = app.get_options()
        self.repo_baseurl = opts.repo_baseurl
        #log.debug('Base url: %s', self.repo_baseurl)

        self.repo_basedir = RepoState().repo_basedir
        #log.debug('Base directory: %s', self.repo_basedir)

        self.name = name
        #log.debug('Repo name: %s', self.name)

        self.ref = ref or opts.default_ref

        if origin:
            self.origin_url = origin
        else:
            self.origin_url = '%s/%s' % (self.repo_baseurl, self.name)
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
