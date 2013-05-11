"""Butcher dependency graph"""

import json
from matplotlib import pyplot
import networkx
import pprint
from twitter.common import app
from twitter.common import util

#gflags.DEFINE_string('depsjson',
#                     'src/python/cloudscaling/buildy/repodeps.json',
#                     'Path to deps json file')
#FLAGS = gflags.FLAGS


class ButcherGraph(networkx.DiGraph):
  """graphy thing."""

  def __init__(self, data=None, **kwargs):
    networkx.DiGraph.__init__(self, data, **kwargs)


def blarg():
  #if not args:
  #  print "Usage: deps2 <buildtarget>"
  #  return 1

  data = json.load(open(FLAGS.depsjson, 'r'))

  depgraph = networkx.DiGraph()

  for repo in data:
    print "REPO: %s" % repo['repo']
    for target in repo['outputs']:
      pprint.pprint(target)
      name = '//%s:%s' % (repo['repo'], target['name'])
      depgraph.add_node(name)
      if 'dependencies' in target:
        for dep in target['dependencies']:
          depgraph.add_edge(name, dep)
  networkx.write_dot(depgraph, '/tmp/deps.dot')
  #print "Topological sort:"
  #print networkx.topological_sort(depgraph)
  #print "Dict of lists:"
  #print networkx.to_dict_of_lists(depgraph)
  #print "Dict of dicts:"
  #pprint.pprint(networkx.to_dict_of_dicts(depgraph))
  #print "Edge list:"
  edges = networkx.to_edgelist(depgraph)
  edges = [ tuple(x[:-1]) for x in edges ]

  for deps_ready in util.topological_sort(edges):
    print deps_ready

  #networkx.draw_circular(depgraph)
  #networkx.draw_random(depgraph)
  #networkx.draw_spectral(depgraph)
  #networkx.draw_spring(depgraph)
  #networkx.draw_shell(depgraph)
  #networkx.draw_graphviz(depgraph)
  #pyplot.show()
