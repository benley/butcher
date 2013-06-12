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
        pants('src/python/cloudscaling/butcher:gitrepo'),
        pants('src/python/cloudscaling/third_party:networkx'),
        ],
    )
