"""Object caching"""

import os
import shutil
from cloudscaling.buildy import gitrepo
from cloudscaling.buildy import error
from twitter.common import app
from twitter.common import log

app.add_option('--object_cache_dir', dest='object_cache_dir',
               help='Path to local object cache directory.')


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

  def path_in_cache(self, filename, rule, metahash):
    """Generates the path to a file in the cache.

    The generated path does not imply the file's existence!

    Args:
      filename: Filename relative to the path of the rule that generated it.
      rule: A targets.SomeBuildRule object
      metahash: Hashed combination of source ingredients and flags and
                whatever. (Not yet implemented, nor fully thought out.)

    """
    return os.path.join(self.cache_dir, str(metahash), rule.address.repo,
                        rule.address.path, filename)

  def putfile(self, filepath, buildroot, buildrule, metahash):
    """Put a file in the cache.

    Args:
      filepath: Path to file on disk.
      buildroot: Path to buildroot (i.e. filepath prefix to strip)
      buildrule: The rule that generated this file.
      metahash: unique metahash (blahblah?)
    """
    filepath_relative = filepath.split(buildroot)[1][1:]
    incachepath = self.path_in_cache(filepath_relative, buildrule, metahash)
    log.debug('Cache: %s -> %s', filepath, incachepath)
    if not os.path.exists(os.path.dirname(incachepath)):
      os.makedirs(os.path.dirname(incachepath))
    shutil.copy2(filepath, incachepath)
    log.debug('Added to cache: %s', incachepath)
