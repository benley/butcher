"""Parsing context manager for BUILD files."""

import collections
import contextlib
import copy
import os
from cloudscaling.butcher import error

class ContextError(error.ButcherError):
  """Something requiring a BUILD context was attempted out of context."""
  pass


class ParseContext(object):
  _active = collections.deque([])
  _parsed = set()
  _strs_to_exec = [
      'print "IN CONTEXT WOOO"',
      'from cloudscaling.butcher.targets import *',
      ]

  @staticmethod
  @contextlib.contextmanager
  def activate(ctx):
    """Activate the given ParseContext."""
    if hasattr(ctx, '_on_context_exit'):
      raise ContextError(
          'Context actions registered outside this parse context are active')

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

  @staticmethod
  def _exec_function(ast, globals_map):
    locals_map = globals_map
    exec(ast, globals_map, locals_map)
    return locals_map

  def parse(self, **global_args):
    """Entry point to parsing a BUILD file."""

    if self.build_file not in ParseContext._parsed:
      # http://en.wikipedia.org/wiki/Abstract_syntax_tree
      # http://martinfowler.com/books/dsl.html
      butcher_context = {}
      for str_to_exec in self._strs_to_exec:
        ast = compile(str_to_exec, '<string>', 'exec')
        self._exec_function(ast, butcher_context)

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
            self._exec_function(self.build_file.code(), eval_globals)
        finally:
          os.chdir(startdir)
