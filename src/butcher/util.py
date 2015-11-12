"""Miscellaneous utility functions."""

import collections
import glob2
import hashlib
import os
import shutil
from butcher import error
from twitter.common import log


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
        raise RuntimeError('This function has failed at life.')


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
    """Returns list of paths matching one or more wildcard patterns.

    Args:
      include_dirs: Include directories in the output
    """
    if len(args) is 1 and isinstance(args[0], list):
        args = args[0]
    matches = []
    for pattern in args:
        for item in glob2.glob(pattern):
            if not os.path.isdir(item):
                matches.append(item)
    return matches


def flatten(listish):
    """Flatten an arbitrarily-nested list of strings and lists.

    Works for any subclass of basestring and any type of iterable.
    """
    for elem in listish:
        if (isinstance(elem, collections.Iterable)
                and not isinstance(elem, basestring)):
            for subelem in flatten(elem):
                yield subelem
        else:
            yield elem


def linkorcopy(src, dst):
    """Hardlink src file to dst if possible, otherwise copy."""
    if not os.path.isfile(src):
        raise error.ButcherError('linkorcopy called with non-file source. '
                                 '(src: %s  dst: %s)' % src, dst)
    elif os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    elif os.path.exists(dst):
        os.unlink(dst)
    elif not os.path.exists(os.path.dirname(dst)):
        os.makedirs(os.path.dirname(dst))

    try:
        os.link(src, dst)
        log.debug('Hardlinked: %s -> %s', src, dst)
    except OSError:
        shutil.copy2(src, dst)
        log.debug('Couldn\'t hardlink. Copied: %s -> %s', src, dst)
