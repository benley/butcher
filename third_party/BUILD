# This is a pants BUILD file, not a Butcher one.

# FIXME(ben): There is a bug preventing butcher from working with networkx
# newer than 1.7rc1. Try asking it to dump the graph for mini-boot; it will
# fail. Are we accidentally relying on a networkx bug that was later fixed?
python_library(name='Networkx',
               dependencies=[
                   python_requirement('networkx==1.7rc1'),
                   python_requirement('pygraphviz'),
                   ])

python_library(name='Matplotlib',
               dependencies=[
                   python_requirement('matplotlib'),
                   python_requirement('numpy'),
                   python_requirement('dateutils')
                   ])

python_requirement('GitPython', name='gitpython')
python_requirement('glob2')
python_requirement('twitter.common.app')

# We don't require a pinned version for any reason other than pip's
# inability to resolve versioned dependencies properly.
# If they release a newer twitter.common.app on pypi at some point this
# can probably become an unversioned dependency.
python_requirement('twitter.common.log==0.1.0', name='twitter.common.log')
