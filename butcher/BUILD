# This is a pants BUILD file, not a Butcher one.
# vi:ft=python

BUTCHER_VERSION = '0.2.12'

python_binary(
    name = 'butcher',
    source = 'butcher.py',
    provides = setup_py(
        name = 'butcher',
        version = BUTCHER_VERSION,
        description = 'The Butcher build system',
        namespace_packages = [
            'cloudscaling',
            'cloudscaling.butcher'
            ]
        ),
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

# rubygems is currently (temporarily or permanently) unused:
python_library(
    name = 'rubygems',
    sources = ['rubygems.py'],
    dependencies = [
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
        pants('src/python/cloudscaling/third_party:glob2'),
        pants('src/python/twitter/common/log'),
        ])

python_binary(
    name = 'util_test',
    source = 'util_test.py',
    dependencies = [
        pants(':util'),
        ])
