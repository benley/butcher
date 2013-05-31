"""Object caching"""

import os
import shutil
from cloudscaling.buildy import gitrepo
from cloudscaling.buildy import error
from twitter.common import app
from twitter.common import log

app.add_option('--object_cache_dir', dest='object_cache_dir',
               help='Path to local object cache directory.')


class CacheMiss(RuntimeError):
  pass


class CacheManager(app.Module):
  """Built object cache manager."""
  cache_dir = None

  def __init__(self):
    app.Module.__init__(self, label='butcher.cachemanager',
                        description='Butcher cache manager')

  def setup_function(self):
    if not self.cache_dir:
      opts = app.get_options()
      if opts.object_cache_dir:
        self.cache_dir = opts.object_cache_dir
      else:
        self.cache_dir = os.path.join(opts.butcher_basedir, 'cache')
      log.info('Cache initialized at %s', self.cache_dir)
    if not os.path.exists(self.cache_dir):
      os.makedirs(self.cache_dir)

  def path_in_cache(self, filename, metahash):
    """Generates the path to a file in the cache.

    The generated path does not imply the file's existence!

    Args:
      filename: Filename relative to buildroot
      rule: A targets.SomeBuildRule object
      metahash: hash object
    """
    mhash = metahash.hexdigest()
    return os.path.join(self.cache_dir, mhash, filename)

  def putfile(self, filepath, buildroot, metahash):
    """Put a file in the cache.

    Args:
      filepath: Path to file on disk.
      buildroot: Path to buildroot
      buildrule: The rule that generated this file.
      metahash: hash object
    """
    filepath_relative = filepath.split(buildroot)[1][1:]  # (Strip leading /)
    incachepath = self.path_in_cache(filepath_relative, metahash)
    log.debug('Cache: %s -> %s', filepath, incachepath)
    if not os.path.exists(os.path.dirname(incachepath)):
      os.makedirs(os.path.dirname(incachepath))
    shutil.copy2(filepath, incachepath)
    log.debug('Added to cache: %s', incachepath)

  def in_cache(self, objpath, metahash):
    """Returns true if object is cached.

    Args:
      objpath: Filename relative to buildroot.
      metahash: hash object
    """
    if os.path.exists(self.path_in_cache(objpath, metahash)):
      return True
    else:
      return False

  def get_obj(self, objpath, metahash, dst_path):
    """Get object from cache, write it to dst_path.

    Args:
      objpath: filename relative to buildroot
               (example: mini-boot/blahblah/somefile.bin)
      metahash: metahash. See targets/base.py
      dst_path: Absolute path where the file should be written.
    Raises:
      CacheMiss: if the item is not in the cache
    """
    mhash = metahash.hexdigest()
    incachepath = self.path_in_cache(objpath, metahash)
    if not os.path.exists(incachepath):
      raise CacheMiss('%s not in cache.' % incachepath)
    else:
      log.debug('Cache hit! %s~%s', objpath, mhash)
      if not os.path.exists(os.path.dirname(dst_path)):
        os.makedirs(dst_path)
      shutil.copy2(incachepath, dst_path)
