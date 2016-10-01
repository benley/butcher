"""Parsing context manager for BUILD files.

Things available in BUILD context:
  invokable rules:
    - At the time of writing this: genrule, gendeb, filegroup, pkgfilegroup
    - See documentation for each type.
    - For a list see butcher.targets.__init__.py
  functions:
    - glob: see python help for glob.glob
  variables:
    - ROOTDIR: path to the source tree root.
    - RULEDIR: path to the directory the BUILD file is in.
"""

import collections
import contextlib
import copy
import os
from butcher import error


class ContextError(error.ButcherError):
    """Something requiring a BUILD context was attempted out of context."""
    pass


class ParseContext(object):
    """Manage context for parsing/loading BUILD files."""
    _active = collections.deque([])
    _parsed = set()
    # These strings get executed inside each buildfile context
    # to initialize it:
    _strs_to_exec = [
        'from butcher.target_context import *',
        ]

    @staticmethod
    @contextlib.contextmanager
    def activate(ctx):
        """Activate the given ParseContext."""
        if hasattr(ctx, '_on_context_exit'):
            raise ContextError(
                'Context actions registered outside this '
                'parse context are active')

        try:
            ParseContext._active.append(ctx)
            ctx._on_context_exit = []
            yield
        finally:
            for func, args, kwargs in ctx._on_context_exit:
                func(*args, **kwargs)
            del ctx._on_context_exit
            ParseContext._active.pop()

    def __init__(self, build_file):
        self.build_file = build_file
        self._parsed = False

    def parse(self, **global_args):
        """Entry point to parsing a BUILD file.

        Args:
          **global_args: Variables to include in the parsing environment.
        """

        if self.build_file not in ParseContext._parsed:
            # http://en.wikipedia.org/wiki/Abstract_syntax_tree
            # http://martinfowler.com/books/dsl.html
            butcher_context = {}
            for str_to_exec in self._strs_to_exec:
                ast = compile(str_to_exec, '<string>', 'exec')
                exec_function(ast, butcher_context)

            with ParseContext.activate(self):
                startdir = os.path.abspath(os.curdir)
                try:
                    os.chdir(self.build_file.path_on_disk)
                    if self.build_file not in ParseContext._parsed:
                        ParseContext._parsed.add(self.build_file)
                        eval_globals = copy.copy(butcher_context)
                        eval_globals.update(
                            {'ROOT_DIR': self.build_file.path_on_disk,
                             '__file__': 'bogus please fix this'})
                        eval_globals.update(global_args)
                        exec_function(self.build_file.code, eval_globals)
                finally:
                    os.chdir(startdir)


def exec_function(ast, globals_map):
    """Execute a python code object in the given environment.

    Args:
      globals_map: Dictionary to use as the globals context.
    Returns:
      locals_map: Dictionary of locals from the environment after execution.
    """
    locals_map = globals_map
    exec ast in globals_map, locals_map
    return locals_map
