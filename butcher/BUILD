# This is a pants BUILD file, not a Butcher one.
# vi:ft=conf

python_binary(
    name = 'butcher',
    source = 'butcher.py',
    dependencies = [
        pants(':butcher_lib'),
        ])

python_library(
    name = 'butcher_lib',
    sources = [
        'buildfile.py',
        'butcher.py',
        'buildfile_context.py',
        'target_context/__init__.py',
        ],
    dependencies = [
        pants(':address'),
        pants(':cache'),
        pants(':error'),
        pants(':gitrepo'),
        pants(':util'),
        pants('src/python/cloudscaling/butcher/targets'),
        pants('src/python/twitter/common/app'),
        pants('src/python/twitter/common/log'),
        ])

python_library(
    name = 'address',
    sources = 'address.py',
    dependencies = [
        pants(':error'),
        ]
    )

python_library(
    name = 'cache',
    sources = 'cache.py',
    dependencies = [
        pants(':gitrepo'),
        pants(':error'),
        pants(':util'),
        ]
    )

python_library(
    name = 'error',
    sources = 'error.py',
    )

python_library(
    name = 'gitrepo',
    sources = 'gitrepo.py',
    dependencies = [
        python_requirement('GitPython'),
        pants('src/python/twitter/common/app'),
        pants('src/python/twitter/common/log'),
        ])

python_library(
    name = 'util',
    sources = 'util.py',
    dependencies = [
        pants('src/python/cloudscaling/third_party:glob2')
        ])
