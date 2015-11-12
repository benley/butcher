"""Base target."""

import os
import re
import shutil
from butcher import address
from butcher import cache
from butcher import error
from butcher import util
from twitter.common import log


class BaseBuilder(object):
    """Base class for rule self-builders."""

    # If true, butcher will generally hard-link files from its cache into the
    # build area rather than copying them.
    linkfiles = True

    def __init__(self, buildroot, target_obj, source_dir):
        self.source_dir = source_dir    # Where the git repo is checked out
        self.rule = target_obj          # targets.something object
        self.address = target_obj.name  # Build address
        self.buildroot = buildroot
        self.cachemgr = cache.CacheManager()
        self._cached_metahash = None
        if not os.path.exists(self.buildroot):
            os.makedirs(self.buildroot)
        # TODO: some rule types don't have srcs.
        #       Should probably use an intermediate subclass.
        self.srcs_map = {}
        self.deps_map = {}

    def collect_srcs(self):
        for src in self.rule.source_files or []:
            srcpath = os.path.join(self.source_dir, self.address.path, src)
            dstpath = os.path.join(self.buildroot, self.address.repo,
                                   self.address.path, src)
            dstdir = os.path.dirname(dstpath)
            if not os.path.exists(dstdir):
                os.makedirs(dstdir)
            log.debug('[%s]: Collect srcs: %s -> %s', self.rule.address,
                      srcpath, dstpath)
            self.linkorcopy(srcpath, dstpath)
            self.srcs_map[src] = dstpath

    def collect_deps(self):
        pass
        # Holy crap, this whole function is unnecessary with the current
        # design. A rule's dependencies are built before the rule (duh) and the
        # outputs thereof go into the same buildroot that this one uses, so the
        # files will already be in place. This will probably not always be the
        # case though, so this ought to get implemented in an intelligent way.

        #if 'deps' not in self.rule.params:
        #    return
        #for dep in self.rule.composed_deps() or []:
        #    dep_rule = self.rule.subgraph.node[dep]['target_obj']
        #    for item in dep_rule.output_files:
        #       srcpath = os.path.join(self.buildroot, item)
        #       dstpath = os.path.join(self.buildroot, item)
        #       dstdir = os.path.dirname(dstpath)
        #       log.debug('[%s]: Collecting deps: %s -> %s',
        #                 self.address, item, dstpath)
        #       if not os.path.exists(dstdir):
        #           os.makedirs(dstdir)
        #       shutil.copy2(srcpath, dstdir)
        #       self.deps_map[item] = dstpath

    def _metahash(self):
        """Checksum hash of all the inputs to this rule.

        Output is invalid until collect_srcs and collect_deps have been run.

        In theory, if this hash doesn't change, the outputs won't change
        either, which makes it useful for caching.
        """

        # BE CAREFUL when overriding/extending this method. You want to copy
        # the if(cached)/return(cached) part, then call this method, then at
        # the end update the cached metahash. Just like this code, basically,
        # only you call the method from the base class in the middle of it. If
        # you get this wrong it could result in butcher not noticing changed
        # inputs between runs, which could cause really nasty problems.
        # TODO(ben): the above warning seems avoidable with better memoization

        if self._cached_metahash:
            return self._cached_metahash

        # If you are extending this function in a subclass,
        # here is where you do:
        # BaseBuilder._metahash(self)

        log.debug('[%s]: Metahash input: %s', self.address,
                  unicode(self.address))
        mhash = util.hash_str(unicode(self.address))
        log.debug('[%s]: Metahash input: %s', self.address, self.rule.params)
        mhash = util.hash_str(str(self.rule.params), hasher=mhash)
        for src in self.rule.source_files or []:
            log.debug('[%s]: Metahash input: %s', self.address, src)
            mhash = util.hash_str(src, hasher=mhash)
            mhash = util.hash_file(self.srcs_map[src], hasher=mhash)
        for dep in self.rule.composed_deps() or []:
            dep_rule = self.rule.subgraph.node[dep]['target_obj']
            for item in dep_rule.output_files:
                log.debug('[%s]: Metahash input: %s', self.address, item)
                item_path = os.path.join(self.buildroot, item)
                mhash = util.hash_str(item, hasher=mhash)
                mhash = util.hash_file(item_path, hasher=mhash)
        self._cached_metahash = mhash
        return mhash

    def collect_outs(self):
        """Collect and store the outputs from this rule."""
        # TODO: this should probably live in CacheManager.
        for outfile in self.rule.output_files or []:
            outfile_built = os.path.join(self.buildroot, outfile)
            if not os.path.exists(outfile_built):
                raise error.TargetBuildFailed(
                    self.address, 'Output file is missing: %s' % outfile)

        #git_sha = gitrepo.RepoState().GetRepo(self.address.repo).repo.commit()
        # git_sha is insufficient, and is actually not all that useful.
        # More factors to include in hash:
        # - commit/state of source repo of all dependencies
        #   (or all input files?)
        #   - Actually I like that idea: hash all the input files!
        # - versions of build tools used (?)
        metahash = self._metahash()
        log.debug('[%s]: Metahash: %s', self.address, metahash.hexdigest())
        # TODO: record git repo state and buildoptions in cachemgr
        # TODO: move cachemgr to outer controller(?)
        self.cachemgr.putfile(outfile_built, self.buildroot, metahash)

    def prep(self):
        self.collect_srcs()
        self.collect_deps()

    def is_cached(self):
        """Returns true if this rule is already cached."""
        # TODO: cache by target+hash, not per file.
        try:
            for item in self.rule.output_files:
                log.info(item)
                self.cachemgr.in_cache(item, self._metahash())
        except cache.CacheMiss:
            log.info('[%s]: Not cached.', self.address)
            return False
        else:
            log.info('[%s]: found in cache.', self.address)
            return True

    def get_from_cache(self):
        """See if this rule has already been built and cached."""
        for item in self.rule.output_files:
            dstpath = os.path.join(self.buildroot, item)
            self.linkorcopy(
                self.cachemgr.path_in_cache(item, self._metahash()),
                dstpath)
            #self.cachemgr.get_obj(item, self._metahash(), dstpath)

    def linkorcopy(self, src, dst):
        """hardlink src file to dst if possible, otherwise copy."""
        if os.path.isdir(dst):
            log.warn('linkorcopy given a directory as destination. '
                     'Use caution.')
            log.debug('src: %s  dst: %s', src, dst)
        elif os.path.exists(dst):
            os.unlink(dst)
        elif not os.path.exists(os.path.dirname(dst)):
            os.makedirs(os.path.dirname(dst))
        if self.linkfiles:
            log.debug('Linking: %s -> %s', src, dst)
            os.link(src, dst)
        else:
            log.debug('Copying: %s -> %s', src, dst)
            shutil.copy2(src, dst)

    def build(self):
        """Build the rule. Must be overridden by inheriting class."""
        raise NotImplementedError(self.rule.address)

    def rulefor(self, addr):
        """Return the rule object for an address from our deps graph."""
        return self.rule.subgraph.node[self.rule.makeaddress(addr)][
            'target_obj']


class BaseTarget(object):
    """Partially abstract base class for build targets."""
    # graphcontext is attached by PythonBuildFile. If present, instances of
    # this class add themselves to the given networkx graph.
    graphcontext = None

    rulebuilder = BaseBuilder
    ruletype = None

    # List of tuples: [('argument_name', type), ...]
    required_params = [('name', str)]

    # List of tuples: ('arg_name', type, 'default value'), ...
    # or ('arg_name', (list, of, types), 'default value'), ...
    optional_params = []

    def __init__(self, **kwargs):
        """Initialize the build rule.

        Args:
          **kwargs: Assorted parameters; see subclass implementations for
                    details.
        """
        self.address = self.name = address.new(kwargs['name'])
        # TODO: eliminate use of .name
        self.subgraph = None
        self.params = {}
        log.debug('New target: %s', self.address)

        try:
            for param_name, param_type in self.required_params:
                self.params[param_name] = kwargs.pop(param_name)
                assert isinstance(self.params[param_name], param_type)
        except AssertionError as err:
            if isinstance(param_type, tuple) and len(param_type) > 1:
                msg = 'one of: %s' % ', '.join(param_type.__name__)
            else:
                msg = str(param_type.__name__)
            raise error.InvalidRule(
                'While loading %s: Invalid type for %s. '
                'Expected: %s. Actual: %s.' % (
                    self.address, param_name, msg,
                    repr(self.params[param_name])))
        except KeyError as err:
            log.error(err)
            raise error.InvalidRule(
                'While loading %s: Required parameter %s not given.' % repr(
                    self.address, param_name))

        for (param_name, param_type, param_default) in self.optional_params:
            if param_name not in kwargs:
                self.params[param_name] = param_default
            else:
                self.params[param_name] = kwargs.pop(param_name)
                if not isinstance(self.params[param_name], param_type):
                    msg = str(param_type.__name__)
                    if isinstance(param_type, tuple) and len(param_type) > 1:
                        msg = 'one of: %s' % ', '.join(param_type.__name__)
                    raise error.InvalidRule(
                        'While loading %s: Invalid type for %s. '
                        'Expected: %s. Actual: %s.' % (
                            self.address, param_name, msg,
                            repr(self.params[param_name])))

        if kwargs:  # There are leftover arguments.
            raise error.InvalidRule(
                '[%s]: Unknown argument(s): %s' % (
                    self.address, ', '.join(kwargs.keys())))

        if self.graphcontext is not None:
            self.graphcontext.add_node(self.address, target_obj=self)
            # TODO: process deps here?

        try:
            self.validate_args()
        except AssertionError as err:
            raise error.InvalidRule('Error in %s: %s' % (self.address, err))

    def validate_args(self):
        """Input validation!"""
        def validate_name():
            allowed_re = '^[a-z](([a-z0-9_-]+)?([a-z0-9])?)?'
            assert isinstance(self.params['name'], basestring), (
                'Name must be a string, not %s' % repr(self.params['name']))
            assert re.match(allowed_re, self.params['name']), (
                'Invalid rule name: %s. Must match %s.' % (
                    repr(self.params['name']), repr(allowed_re)))
        validate_name()

        def validate_deps():
            if 'deps' in self.params:
                assert type(self.params['deps']) in (type(None), list), (
                    'Deps must be a list, not %s' % repr(self.params['deps']))
        validate_deps()

    @property
    def output_files(self):
        """Returns the list of output files from this rule.

        Should be overridden by inheriting class.
        Paths are relative to buildroot.
        """
        raise NotImplementedError(
            '[%s]: Implementation is incomplete.' % self.address)

    def composed_deps(self):
        """Dependencies of this build target."""
        if 'deps' in self.params:
            param_deps = self.params['deps'] or []
            deps = [self.makeaddress(dep) for dep in param_deps]
            return deps
        else:
            return None

    @property
    def source_files(self):
        """This rule's source files."""
        if 'srcs' in self.params and self.params['srcs'] is not None:
            return util.flatten(self.params['srcs'])

    def makeaddress(self, label):
        """Turn a label into an Address with current context.

        Adds repo and path if given a label that only has a :target part.
        """
        addr = address.new(label)
        if not addr.repo:
            addr.repo = self.address.repo
            if not addr.path:
                addr.path = self.address.path
        return addr
