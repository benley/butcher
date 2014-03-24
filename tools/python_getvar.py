#!/usr/bin/python2.7
"""Print the value of a assigned var from a .py file *without* executing it."""

import ast
import os.path
import sys


def getvar(syntree, targetvar):
    """Scan an ast object for targetvar and return its value.

    Only handles single direct assignment of python literal types. See docs on
    ast.literal_eval for more info:
    http://docs.python.org/2/library/ast.html#ast.literal_eval

    Args:
      syntree: ast.Module object
      targetvar: name of global variable to return
    Returns:
      Value of targetvar if found in syntree, or None if not found.
    """
    for node in syntree.body:
        if isinstance(node, ast.Assign):
            for var in node.targets:
                if var.id == targetvar:
                    return ast.literal_eval(node.value)


def main(argv):
    if len(argv) != 3:
        print("USAGE: {} <filename.py> <variable_name>".format(
            os.path.basename(argv[0])))
        sys.exit(1)

    srcfile = argv[1]
    targetvar = argv[2]

    with open(srcfile, 'r') as src:
        code = ast.parse(src.read(), srcfile)
        print getvar(code, targetvar)


if __name__ == '__main__':
    main(sys.argv)
