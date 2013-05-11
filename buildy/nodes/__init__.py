from .deb import Deb
from .filegroup import FileGroup
from .generic import GenericNode
from .gitrepo import GitRepo, GitError
from .unresolved import UnresolvedDep

__all__ = [
    'Deb',
    'GenericNode',
    'GitRepo',
    'GitError',
    'UnresolvedDep',
    'FileGroup',
    ]

def node(name, props=None):
  if not props:
    return GenericNode(name, props)
  if 'type' in props:
    ntype = props.pop('type')
    if ntype == 'deb':
      return Deb(name, props)
    elif ntype == 'filegroup':
      return FileGroup(name, props)
    else:
      return GenericNode(name, props)
