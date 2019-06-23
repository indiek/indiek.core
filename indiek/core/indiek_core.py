"""
IndieK module containing core functionalities for DB connection and BLL
    offer a basic API to
        a) create topics and links between them
        b) gather topics and links into arbitrary graphs

Examples:
    >>> sess = UserInterface()
    >>> sess.list_topics()

Next steps in development:
+ handle all topic and topic links through the full topic graph
"""
import pyArango.connection as pyconn
from pyArango.document import Document
import pyArango.collection as pcl
from pyArango.graph import Graph, EdgeDefinition
import pyArango.validation as pvl
from pyArango.theExceptions import ValidationError
import json

PATH_TO_CONFIG = '/home/adrian/.ikconfig'

# keys are what I use in the code, values are what is used in the database
COLL_NAMES = {'topics': 'Topics',
              'subtopic_links': 'SubtopicRelation'}
GRAPH_NAMES = {'all_topics': 'TopicsGraph'}
TOPIC_FIELDS = {'name': 'name', 'description': 'description'} 
LINK_FIELDS = {'note': 'note'}
MAX_LENGTHS = {'topic_name': 50, 'topic_description': 1000}


"""
ref for special collections:
https://github.com/ArangoDB-Community/pyArango/tree/5d9465cabca15a75477948c45bb57aa57fc90a0a
"""


def ik_connect(config='default'):
    """
    The aim of this script is to:
        1. connect to ArangoDB with credentials fetched from a .json config file
        2. check whether the 'ikdev' database and the 'topics' and 'links' collections exist
    todo: accept on-the-fly configuration (no need to read from config file)
    """
    with open(PATH_TO_CONFIG) as f:
        conf = json.load(f)[config+'_config']
    conn = pyconn.Connection(username=conf['username'], password=conf['password'])
    db_name = conf['database']

    # check appropriate db and collections exist
    if not conn.hasDatabase(db_name):
        raise LookupError(f"database {db_name} not found; either it doesn't exist or arangodb"
                          f" user {conf['username']} from your config file doesn't have proper permissions")

    db = conn[db_name]

    if not db.hasCollection(COLL_NAMES['topics']):
        print(f"collection {COLL_NAMES['topics']} not found in db {db.name}")
        ans = input("would you like to create it? (y + ENTER for yes) ")
        if ans == 'y':
            db.createCollection(name=COLL_NAMES['topics'], className='Topics')
            print(f"collection {COLL_NAMES['topics']} created")

#    db[COLL_NAMES['topics']].ensureFulltextIndex(list(TOPIC_FIELDS.values())) # somehow this fails

    if not db.hasCollection(COLL_NAMES['subtopic_links']):
        print(f"collection {COLL_NAMES['subtopic_links']} not found in db {db.name}")
        ans = input("would you like to create it? (y + ENTER for yes) ")
        if ans == 'y':
            db.createCollection(name=COLL_NAMES['subtopic_links'], className='SubtopicRelation')
            print(f"collection {COLL_NAMES['subtopic_links']} created")

    if not db.hasGraph(GRAPH_NAMES['all_topics']):
        print(f"database {db_name} has no graph named {GRAPH_NAMES['all_topics']}")
        ans = input("would you like to create it? (y + ENTER for yes) ")
        if ans == 'y':
            db.createGraph(GRAPH_NAMES['all_topics'])
            print(f"graph {GRAPH_NAMES['all_topics']} created")

    return db


def get_topic_by_name(db, topic_name, as_simple_query=False):
    """
    fetches topic if exists, false otherwise
    todo: figure out what batchSize does
    Args:
        db: DBHandle
        topic_name: string, name of topic
        as_simple_query: bool, if true returns SimpleQuery object, if false (default) returns Document object
    Returns:
        pyArango.query.SimpleQuery
    """
    simple_query = db[COLL_NAMES['topics']].fetchByExample({TOPIC_FIELDS['name']: topic_name}, batchSize=100)
    if as_simple_query:
        return simple_query
    if simple_query.count > 0:
        return simple_query[0]
    else:
        return None


class StringVal(pvl.Validator):
    def validate(self, value):
        if type(value) is not str:
            raise ValidationError("Field value must be a string")
        return True


class Topics(pcl.Collection):
    # not convinced the _properties below are all necessary
    _properties = {
        "keyOptions": {
            "allowUserKeys": False,
            "type": "autoincrement",
        }
    }

    _validation = {
        'on_save': True,
        'on_set': True,
        'allow_foreign_fields': False  # allow fields that are not part of the schema
    }

    _fields = {
        'name': pcl.Field(validators=[pvl.NotNull(),
                                      pvl.Length(2, MAX_LENGTHS['topic_name']),
                                      StringVal()]),
        'description': pcl.Field(validators=[pvl.NotNull(),
                                             pvl.Length(4, MAX_LENGTHS['topic_description']),
                                             StringVal()])
    }


class SubtopicRelation(pcl.Edges):
    """edge class to use to assign a topic as a subtopic of another"""
    pass


class TopicsGraph(Graph):
    """graph of all topics in the database"""
    _edgeDefinitions = [EdgeDefinition("SubtopicRelation",
                                       fromCollections=COLL_NAMES["topics"],
                                       toCollections=COLL_NAMES["topics"])]
    _orphanedCollections = []


class UserInterface:
    """
    Class through which all user interactions with ik database occurs. Should be used as a session manager, i.e. each
    instance is a separate ik user session with its own connection to ik's database.
    """
    def __init__(self, conn_opts='default'):
        self.db = ik_connect(config=conn_opts)
        self.topics_graph = self.db.graphs[GRAPH_NAMES['all_topics']]

    def create_topic(self, name, descr):
        """
        :param name: topic name (see Topics._fields for constraints)
        :param descr: topic description (see Topics._fields for constraints)
        :return:
        """
        if get_topic_by_name(self.db, name, as_simple_query=True):
            print(f"topic '{name}' already exists")
            doc = None
        else:
            doc = self.topics_graph.createVertex(
                COLL_NAMES['topics'],
                {
                    TOPIC_FIELDS['name']: name,
                    TOPIC_FIELDS['description']: descr
                }
            )
            doc.save()
        return doc

    def delete_topic(self, doc):
        """remove topic from database, and all linked edges"""
        self.topics_graph.deleteVertex(doc)

    def list_topics(self):
        """
        :param db: ik db instance
        :return:
        """
        sep_line = '----------------------'

        simple_query = self.db[COLL_NAMES['topics']].fetchAll()

        print(f'LIST OF {simple_query.count} TOPICS IN DB')

        for topic in simple_query:
            name_key = TOPIC_FIELDS['name']
            description_key = TOPIC_FIELDS['description']
            print(f"\n{name_key}: {topic[name_key]}\n")
            print(f"{description_key}:\n{topic[description_key]}")
            print(sep_line)

    def set_subtopic(self, supratopic, subtopic):
        self.topics_graph.link('SubtopicRelation', supratopic, subtopic)


def doc_in_list(document, list_of_docs):
    doc_id = document['_id']
    id_list = [d['_id'] for d in list_of_docs]
    return doc_id in id_list


def subtopic_link_exists(db, topic1, topic2):
    out_edges = db[COLL_NAMES['subtopic_links']].getOutEdges(topic1)
    in_edges = db[COLL_NAMES['subtopic_links']].getInEdges(topic2)
    return any([doc_in_list(o, in_edges) for o in out_edges])


def create_subtopic_link(db, topic1, topic2):
    """
    todo: check that topic1 and topic2 are 'up-to-date' before saving the link
    todo: use graph API in this function
    todo: get genealogy
    :param db:
    :param topic1: topic obj
    :param topic2: topic obj
    :return:
    """
    if subtopic_link_exists(db, topic1, topic2):
        print('subtopic link exists, link creation aborted')
        return None

    link = db[COLL_NAMES['subtopic_links']].createEdge()
    link['_from'] = topic1['_id']
    link['_to'] = topic2['_id']

    link.save()
    return link


if __name__ == "__main__":
    s = UserInterface()
    # create a simple topics graph
    t1 = s.create_topic('t1', 'minimal element')
    t2 = s.create_topic('t2', 'same level as t1')
    t3 = s.create_topic('t3', 'child of t1 and t2')
    s.set_subtopic(t1, t3)
    s.set_subtopic(t2, t3)

    t4 = s.create_topic('t4', 'child of t3 and t5')
    s.set_subtopic(t3, t4)

    t5 = s.create_topic('t5', 'minimal element')
    s.set_subtopic(t5, t4)
    # now explore it in browser
