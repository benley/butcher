# vi:ft=python

python_library(
    name = 'nodes',
    sources =  [
        '__init__.py',
        'unresolved.py',
        'generic.py',
        'deb.py',
        'filegroup.py',
        ],
    dependencies = [
        ':gitrepo',
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
