"""Unimplemented target class."""

from butcher.targets import base
from twitter.common import log


class UnimplementedTarget(base.BaseTarget):
    ruletype = 'UNKNOWN'

    def __init__(self, name, *args, **kwargs):
        log.warn('New Unimplemented %s target: name=%s, %s, %s',
                 self.ruletype, name, args, kwargs)
        base.BaseTarget.__init__(self, name)
