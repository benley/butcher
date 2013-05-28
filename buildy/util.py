"""Misc utility functions."""

import os


def user_homedir(username=None):
  """Returns a user's home directory.

  If no username is specified, returns the current user's homedir.
  """
  if username:
    return os.path.expanduser('~%s/' % username)
  elif 'HOME' in os.environ:
    return os.environ['HOME']
  elif os.name == 'posix':
    return os.path.expanduser('~/')
  else:
    raise RuntimeError(
        'This function is bollocks and its author should most likely be sacked')
