from .generic import GenericNode

class Deb(GenericNode):
  """Node representing a Debian package."""

  def __init__(self, name=None):
    self.name = name

  def __str__(self):
    return self.name
