"""Exceptions and errors."""


class ButcherError(RuntimeError):
  """Generic error class."""
  pass


class BrokenGraph(ButcherError):
  """Something's fubar in the graph. Probably bad user input."""
  pass
