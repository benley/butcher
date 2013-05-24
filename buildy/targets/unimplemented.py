"""Unimplemented target class."""

from . import BaseTarget
from twitter.common import log


class UnimplementedTarget(BaseTarget):
  ruletype = 'UNKNOWN'

  def __init__(self, name, *args, **kwargs):
    log.warn('New Unimplemented %s target: name=%s, %s, %s',
             self.ruletype, name, args, kwargs)
    BaseTarget.__init__(self, name)
