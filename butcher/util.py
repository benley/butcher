"""Miscellaneous utility functions."""

import fnmatch
import glob2
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


def hash_file(filename, hasher=None, blocksize=65536):
  """Checksum a file, optionally updating an existing hash.

  Args:
    filename: Path to the file.
    hasher: Hash object such as hashlib.sha1(). Defaults to sha1.
    blocksize: Read from the file this many bytes at a time.
  """
  return hash_stream(open(filename, 'rb'), hasher, blocksize)


def hash_stream(fileobj, hasher=None, blocksize=65536):
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


def repeat_flag(seq, flag):
  """Intersperse flag as a predecessor to each element of seq.

  Example:
  seq = ['foo', 'bar', 'bas']
  flag = '--word'
  print repeat_flag(seq, flag)
    ==>  ['--word', 'foo', '--word', 'bar', '--word', 'bas']
  """
  for item in iter(seq):
    yield flag
    yield item


def glob(*args):
  """Returns list of paths matching one or more wildcard patterns."""
  if len(args) is 1 and isinstance(args[0], list):
    args = args[0]
  matches = []
  for pattern in args:
    for item in glob2.glob(pattern):
      matches.append(item)
  return matches
