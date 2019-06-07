"""
IndieK module containing core functionalities for DB connection and BLL
    offer a basic API to
        a) create topics and links between them
        b) gather topics and links into arbitrary graphs
"""
import pyArango.connection as pyconn
from pyArango.document import Document
from pyArango.collection import Collection #, Field
from pyArango.graph import Graph, EdgeDefinition
import json

PATH_TO_CONFIG = '/home/adrian/.ikconfig'

# keys are what I use in the code, values are what is used in the database
COLL_NAMES = {'topics': 'topics',
              'subtopic_links': 'subtopic_links'}
TOPIC_FIELDS = {'name': 'name', 'description': 'description'} 
LINK_FIELDS = {'note': 'note'}


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

    # check appropriate db and collections exist; offer to create them if they don't
    # note that creation might fail if proper permissions aren't set for the user
    if not conn.hasDatabase(db_name):
        raise LookupError(f"database {db_name} not found; either it doesn't exist or arangodb"
                          f" user {conf['username']} from your config file doesn't have proper permissions")

    db = conn[db_name]

    if not db.hasCollection(COLL_NAMES['topics']):
        print(f"collection {COLL_NAMES['topics']} not found in db {db.name}")
        ans = input("would you like to create it? (y + ENTER for yes) ")
        if ans == 'y':
            db.createCollection(name=COLL_NAMES['topics'], className='Collection')
            print(f"collection {COLL_NAMES['topics']} created")

#    db[COLL_NAMES['topics']].ensureFulltextIndex(list(TOPIC_FIELDS.values())) # somehow this fails

    if not db.hasCollection(COLL_NAMES['subtopic_links']):
        print(f"collection {COLL_NAMES['subtopic_links']} not found in db {db.name}")
        ans = input("would you like to create it? (y + ENTER for yes) ")
        if ans == 'y':
            db.createCollection(name=COLL_NAMES['subtopic_links'], className='Edges')
            print(f"collection {COLL_NAMES['subtopic_links']} created")

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


def list_topics(db):
    """

    :param db: ik db instance
    :return:
    """
    sep_line = '----------------------'

    simple_query = db[COLL_NAMES['topics']].fetchAll()

    print(f'LIST OF {simple_query.count} TOPICS IN DB')

    for topic in simple_query:
        name_key = TOPIC_FIELDS['name']
        description_key = TOPIC_FIELDS['description']
        print(f"\n{name_key}: {topic[name_key]}\n")
        print(f"{description_key}:\n{topic[description_key]}")
        print(sep_line)


def create_topic(db, name, descr):
    """
    todo: use graph API
    :param db:
    :param name:
    :param descr:
    :return:
    """
    if get_topic_by_name(db, name, as_simple_query=True):
        print(f"topic '{name}' already exists")
        doc = None
    else:
        doc = db[COLL_NAMES['topics']].createDocument({
            TOPIC_FIELDS['name']: name,
            TOPIC_FIELDS['description']: descr})
        doc.save()
    return doc


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
    db_o = ik_connect()
    print('list topics')
    print(list_topics(db_o))

    print('checking emptyness in if statement')
    t = get_topic_by_name(db_o, 'salut')
    if t:
        print('topic found!')
    else:
        print('topic not found!')

    print('creating topic "salut"')
    create_topic(db_o, 'salut', 'premier topic')
    
    print('list topics')
    print(list_topics(db_o))

    print('checking emptyness in if statement')
    t = get_topic_by_name(db_o, 'salut')
    if t:
        print('topic found!')
    else:
        print('topic not found!')

    print('trying to re-create same topic')
    create_topic(db_o, 'salut', 'premier topic')
    
    print('list topics')
    print(list_topics(db_o))
