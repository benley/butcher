"""Object caching"""

import os
from butcher import gitrepo
from butcher import util
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
        self.obj_cachedir = None
        self.mh_cachedir = None

    def setup_function(self):
        if not self.cache_dir:
            opts = app.get_options()
            if opts.object_cache_dir:
                self.cache_dir = opts.object_cache_dir
            else:
                self.cache_dir = os.path.join(opts.butcher_basedir, 'cache')
        self.obj_cachedir = os.path.join(self.cache_dir, 'obj')
        self.mh_cachedir = os.path.join(self.cache_dir, 'mh')
        for subdir in (self.obj_cachedir, self.mh_cachedir):
            if not os.path.exists(subdir):
                os.makedirs(subdir)
        log.info('Cache initialized at %s', self.cache_dir)

    def path_in_cache(self, filename, metahash):
        """Generates the path to a file in the mh cache.

        The generated path does not imply the file's existence!

        Args:
          filename: Filename relative to buildroot
          rule: A targets.SomeBuildRule object
          metahash: hash object
        """
        cpath = self._genpath(filename, metahash)
        if os.path.exists(cpath):
            return cpath
        else:
            raise CacheMiss

    def _genpath(self, filename, mhash):
        """Generate the path to a file in the cache.

        Does not check to see if the file exists. Just constructs the path
        where it should be.
        """
        mhash = mhash.hexdigest()
        return os.path.join(self.mh_cachedir, mhash[0:2], mhash[2:4],
                            mhash, filename)

    def putfile(self, filepath, buildroot, metahash):
        """Put a file in the cache.

        Args:
          filepath: Path to file on disk.
          buildroot: Path to buildroot
          buildrule: The rule that generated this file.
          metahash: hash object
        """
        def gen_obj_path(filename):
            filehash = util.hash_file(filepath).hexdigest()
            return filehash, os.path.join(self.obj_cachedir, filehash[0:2],
                                          filehash[2:4], filehash)

        filepath_relative = filepath.split(buildroot)[1][1:]  # Strip leading /
        # Path for the metahashed reference:
        incachepath = self._genpath(filepath_relative, metahash)

        filehash, obj_path = gen_obj_path(filepath)
        if not os.path.exists(obj_path):
            obj_dir = os.path.dirname(obj_path)
            if not os.path.exists(obj_dir):
                os.makedirs(obj_dir)
            log.debug('Adding to obj cache: %s -> %s', filepath, obj_path)
            os.link(filepath, obj_path)

        if os.path.exists(incachepath):
            existingfile_hash = util.hash_file(incachepath).hexdigest()
            if filehash != existingfile_hash:
                log.warn('File found in mh cache, but checksum differs. '
                         'Replacing with this new version. (File: %s)',
                         filepath)
                log.warn('Possible reasons for this:')
                log.warn(' 1. This build is not hermetic, and something '
                         'differs about the build environment compared to the '
                         'previous build.')
                log.warn(' 2. This file has a timestamp or other build-time '
                         'related data encoded into it, which will always '
                         'cause the checksum to differ when built.')
                log.warn(' 3. Everything is terrible and nothing works.')
                os.unlink(incachepath)

        if not os.path.exists(incachepath):
            log.debug('Adding to mh cache: %s -> %s', filepath, incachepath)
            if not os.path.exists(os.path.dirname(incachepath)):
                os.makedirs(os.path.dirname(incachepath))
            os.link(obj_path, incachepath)

    def in_cache(self, objpath, metahash):
        """Returns true if object is cached.

        Args:
          objpath: Filename relative to buildroot.
          metahash: hash object
        """
        try:
            self.path_in_cache(objpath, metahash)
            return True
        except CacheMiss:
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
        incachepath = self.path_in_cache(objpath, metahash)
        if not os.path.exists(incachepath):
            raise CacheMiss('%s not in cache.' % incachepath)
        else:
            log.debug('Cache hit! %s~%s', objpath, metahash.hexdigest())
            if not os.path.exists(os.path.dirname(dst_path)):
                os.makedirs(os.path.dirname(dst_path))
            os.link(incachepath, dst_path)
            #shutil.copy2(incachepath, dst_path)
