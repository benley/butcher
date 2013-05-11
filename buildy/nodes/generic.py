class GenericNode(object):

  def __init__(self, name=None, dependencies=None):
    self.name = name
    self.dependencies = dependencies

  def __str__(self):
    return self.name

  def __hash__(self):
    return hash(self.name)

  def __eq__(self, other):
    print type(self)
    print type(other)
    return self.name == str(other)
