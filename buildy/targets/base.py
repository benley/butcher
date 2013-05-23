"""Base target."""

class BaseTarget(object):
  """Abstract base class for build targets."""

  def __init__(self, name):
    self.name = name
