# This is a pants BUILD file, not a Butcher one.

BUTCHER_VERSION = '0.2.13'

python_binary(
    name = 'butcher',
    source = 'butcher.py',
    dependencies = [
        pants(':butcher_lib'),
        ])

python_library(
    name = 'butcher_lib',
    provides = setup_py(
        name = 'butcher',
        version = BUTCHER_VERSION,
        description = 'The Butcher build system',
        namespace_packages = [
            'cloudscaling',
            'cloudscaling.butcher'
            ]
        ),
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
        pants('src/cloudscaling/butcher/targets:targets'),
        pants('third_party:twitter.common.app'),
        pants('third_party:twitter.common.log'),
        pants('third_party:Networkx'),
        ])

# rubygems is currently (temporarily or permanently) unused:
python_library(
    name = 'rubygems',
    sources = ['rubygems.py'],
    dependencies = [
        pants('third_party:twitter.common.app'),
        pants('third_party:twitter.common.log'),
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
        pants('third_party:gitpython'),
        pants('third_party:twitter.common.app'),
        pants('third_party:twitter.common.log'),
        ])

python_library(
    name = 'util',
    sources = 'util.py',
    dependencies = [
        pants(':error'),
        pants('third_party:glob2'),
        pants('third_party:twitter.common.app'),
        pants('third_party:twitter.common.log'),
        ])

python_test_suite(
    name='tests',
    dependencies = [
        pants(':util_test'),
        pants('src/cloudscaling/butcher/targets:tests'),
        ])

python_tests(
    name = 'util_test',
    sources = ['util_test.py'],
    coverage = ['cloudscaling.butcher.util'],
    dependencies = [
        pants(':util'),
        ])
