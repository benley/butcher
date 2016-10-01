"""Exceptions and errors."""


class ButcherError(RuntimeError):
    """Generic error class."""
    pass


class BrokenGraph(ButcherError):
    """Something's fubar in the graph. Probably bad user input."""
    pass


class InvalidRule(ButcherError):
    """That is totally not a valid build rule."""
    node = None


class BuildFailure(ButcherError):
    """Parent for build failures."""
    node = None


class AddressError(ButcherError):
    """Can't parse that or something."""
    pass


class TargetBuildFailed(BuildFailure):
    """A build failed."""
    def __init__(self, node, *args):
        BuildFailure.__init__(self, *args)
        self.node = node


class OverallBuildFailure(BuildFailure):
    """The overall build failed, most likely because of individual failures."""
    pass


class NoSuchTargetError(BuildFailure):
    """That target does not exist."""
    pass
