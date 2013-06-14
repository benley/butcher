# This is a pants BUILD file, not a Butcher one.
# vi:ft=conf
#
python_library(
    name='targets',
    sources = [
        '__init__.py',
        'base.py',
        'gendeb.py',
        'genrule.py',
        'filegroup.py',
        'pkgfilegroup.py',
        'pkg_symlink.py',
        'unimplemented.py',
        'virtual.py',
        ],
    dependencies = [
        pants('src/python/cloudscaling/butcher:address'),
        pants('src/python/cloudscaling/butcher:cache'),
        pants('src/python/cloudscaling/butcher:error'),
        pants('src/python/cloudscaling/butcher:gitrepo'),
        pants('src/python/cloudscaling/third_party:networkx'),
        ],
    )

# TODO: make this a python_test target
python_binary(
    name='genrule_test',
    source = 'genrule_test.py',
    dependencies = [pants(':targets')],
    )
