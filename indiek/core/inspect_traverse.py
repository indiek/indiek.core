"""
inspect the behavior of traverse function
"""
import pprint
from indiek_core import *

s = UserInterface()
g = s.topics_graph

# pprint.pprint(
#     g.traverse('Topics/248657', direction='outbound')  # AA2 node
# )

# # IN kwarg doesn't work
# pprint.pprint(
#     g.traverse('Topics/248657', direction='outbound', IN='0..1')  # AA2 node
# )

# # go backwards
# pprint.pprint(
#     g.traverse('Topics/249060', direction='inbound')  # AA2 node
# )

# this is most convenient for my topics needs
queries = {
    'long': "FOR v IN 0..2 OUTBOUND 'Topics/248657' GRAPH 'TopicsGraph' RETURN v.name",
    'late': "FOR v IN 1..2 OUTBOUND 'Topics/248657' GRAPH 'TopicsGraph' RETURN v.name",
    'short': "FOR v IN 0..1 OUTBOUND 'Topics/248657' GRAPH 'TopicsGraph' RETURN v.name",
    'invshort':  "FOR v IN 0..1 INBOUND 'Topics/249060' GRAPH 'TopicsGraph' RETURN v.name",
    'radius': "FOR v IN 0..2 ANY 'Topics/249060' GRAPH 'TopicsGraph' RETURN v.name"
}

for q in queries:
    queryResult = s.db.AQLQuery(queries[q], rawResults=True)  # I believe rawResults=True ensures results are dicts
    print(q)
    pprint.pprint(list(queryResult))


# some bug with rawResults set to False
# queryResultNotRaw = s.db.AQLQuery(aqlQuery, rawResults=False)  # I believe rawResults=False ensures results are docs
# pprint.pprint(list(queryResultNotRaw))
# for doc in queryResultNotRaw:
#     print(doc['name'])
