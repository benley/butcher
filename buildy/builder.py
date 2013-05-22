"""Dealing with actually executing builds."""

import os
from twitter.common import app
from twitter.common import log

app.add_option('--build_root', dest='build_root',
               help='Base directory in which builds will be done.',
               default='/var/lib/butcher/build_root')

class BuildRoot(object):

  def __init__(self):
    self.buildroot = app.get_options().build_root
    os.makedirs(self.buildroot)