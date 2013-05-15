# vi:ft=python

python_binary(
    name = 'graphtest',
    source = 'graphtest.py',
    dependencies = [
        pants(':butcher_lib'),
        ]
    )

python_binary(
    name = 'butcher',
    source = 'butcher.py',
    dependencies = [
        pants(':butcher_lib'),
        ]
    )

python_library(
    name = 'butcher_lib',
    sources = [
        'butcher.py',
        'buildfile.py',
        'buildtarget.py',
        'error.py',
        ],
    dependencies = [
        pants(':graph'),
        pants(':gitrepo'),
        pants('src/python/cloudscaling/buildy/nodes'),
        pants('src/python/twitter/common/app'),
        pants('src/python/twitter/common/log'),
        ]
    )

python_library(
    name = 'graph',
    sources = 'graph.py',
    dependencies = [
        pants('src/python/twitter/common/app'),
        pants('src/python/twitter/common/util'),
        pants('3rdparty/python:matplotlib'),
        pants('3rdparty/python:networkx'),
        ]
    )

python_library(
    name = 'gitrepo',
    sources = 'gitrepo.py',
    dependencies = [
        python_requirement('GitPython'),
        pants('src/python/twitter/common/app'),
        pants('src/python/twitter/common/log'),
        ]
    )
