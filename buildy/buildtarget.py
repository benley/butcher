"""Build target representation."""

import re
from cloudscaling.buildy import error


class BuildTarget(dict):
  """A build target.

  Mostly acts like a dictionary, except when you need it to act like a string.
  """

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
      raise error.ButcherError('Invalid parameter: %s' % key)
    # TODO: value validation
    dict.__setitem__(self, key, value)

  def __repr__(self):
    if self.repo is None or self.target is None:
      raise error.ButcherError('No valid repr for this incomplete target.')

    ret = ['//%(repo)s' % dict(self)]
    if self['path']:
      ret.append('/%s' % self['path'])
    ret.append(':%(target)s' % self)
    return ''.join(ret)

  @property
  def repo(self):
    return self['repo']

  @repo.setter
  def repo(self, val):
    self['repo'] = val

  @property
  def git_ref(self):
    return self['git_ref']

  @git_ref.setter
  def git_ref(self, val):
    self['git_ref'] = val

  @property
  def path(self):
    return self['path']

  @path.setter
  def path(self, val):
    self['path'] = val

  @property
  def target(self):
    return self['target']

  @target.setter
  def target(self, val):
    self['target'] = val

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
      raise error.ButcherError('"%s" is not a valid build target.')
    #log.debug('parse_target: %s -> %s', targetstr, groups)
    return groups
