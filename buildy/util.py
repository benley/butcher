"""Misc utility functions."""

import hashlib
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


def hash_file(fileobj, hasher=None, blocksize=65536):
  """Read from fileobj stream, return hash of its contents.

  Args:
    fileobj: File-like object with read()
    hasher: Hash object such as hashlib.sha1(). Defaults to sha1.
    blocksize: Read from fileobj this many bytes at a time.
  """
  hasher = hasher or hashlib.sha1()
  buf = fileobj.read(blocksize)
  while buf:
    hasher.update(buf)
    buf = fileobj.read(blocksize)
  return hasher

def hash_str(data, hasher=None):
  """Checksum hash a string."""
  hasher = hasher or hashlib.sha1()
  hasher.update(data)
  return hasher
