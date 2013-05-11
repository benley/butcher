from cloudscaling.buildy import graph
from cloudscaling.buildy import nodes

gr = graph.ButcherGraph(name = 'blah')
gr.add_node(nodes.node('node1'))
gr.add_node(nodes.node('node1'))

gr.add_node(nodes.node('node2'))
gr.add_node(nodes.node('node3'))

gr.add_node('foo')
gr.add_node('foo')

print gr.nodes()
print gr.edges()

for node in gr.nodes():
  print "Node: %s\tHash: %s" % (node, hash(node))

#    reponame = '//%s' % builddata['repo']
#    subgraph = graph.ButcherGraph(name = reponame)
#    #subgraph.add_node(reponame, {'repo': repo})
#    if 'targets' in builddata:
#      for target in builddata['targets']:
#        targetname = '%s:%s' % (reponame, target.pop('name'))
#        subgraph.add_node(nodes.node(targetname))
#        if 'dependencies' in target:
#          for dep in target['dependencies']:
#            #TODO(ben): fully resolve dep name
#            if nodes.node(dep) not in subgraph.nodes():
#              subgraph.add_node(nodes.UnresolvedDep(dep))
#            subgraph.add_edge(nodes.node(targetname), nodes.node(dep))
#        #subgraph.add_edge(reponame, targetname)
