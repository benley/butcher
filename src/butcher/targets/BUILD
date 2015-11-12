# This is a pants BUILD file, not a Butcher one.

python_library(
    name = 'targets',
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
        pants('src/butcher:address'),
        pants('src/butcher:cache'),
        pants('src/butcher:error'),
        pants('src/butcher:gitrepo'),
        ],
    )

python_tests(
    name = 'tests',
    sources = globs('*_test.py'),
    coverage = [
        'butcher.targets',
        ],
    dependencies = [
        pants(':targets'),
        ],
    )
