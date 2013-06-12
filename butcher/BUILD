# This is a pants BUILD file, not a Butcher one.
# vi:ft=conf

python_binary(
    name = 'graphtest',
    source = 'graphtest.py',
    dependencies = [
        pants(':butcher_lib'),
        ])

python_binary(
    name = 'butcher',
    source = 'butcher.py',
    dependencies = [
        pants(':butcher_lib'),
        ])

python_library(
    name = 'butcher_lib',
    sources = [
        'address.py',
        'buildfile.py',
        'butcher.py',
        'cache.py',
        'buildfile_context.py',
        'error.py',
        'util.py',
        ],
    dependencies = [
        pants(':graph'),
        pants(':gitrepo'),
        pants('src/python/cloudscaling/butcher/targets'),
        pants('src/python/twitter/common/app'),
        pants('src/python/twitter/common/log'),
        ])

python_library(
    name = 'graph',
    sources = 'graph.py',
    dependencies = [
        pants('src/python/twitter/common/app'),
        pants('src/python/twitter/common/util'),
        pants('src/python/cloudscaling/third_party:matplotlib'),
        pants('src/python/cloudscaling/third_party:networkx'),
        ])

python_library(
    name = 'gitrepo',
    sources = 'gitrepo.py',
    dependencies = [
        python_requirement('GitPython'),
        pants('src/python/twitter/common/app'),
        pants('src/python/twitter/common/log'),
        ])
