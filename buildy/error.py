"""Exceptions and errors."""


class ButcherError(RuntimeError):
  """Generic error class."""
  pass


class BrokenGraph(ButcherError):
  """Something's fubar in the graph. Probably bad user input."""
  pass


class InvalidRule(ButcherError):
  """That is totally not a valid build rule."""
  pass


class BuildFailed(ButcherError):
  """A build failed."""
  pass
