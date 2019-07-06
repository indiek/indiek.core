"""
IndieK module containing core functionalities for DB connection and BLL
    offer a basic API to
        a) create topics and links between them
        b) gather topics and links into arbitrary graphs

Examples:
    >>> with session() as db:
    ...     sess = UserInterface(db)
    ...     topic1 = sess.create_topic('topic title', 'topic description')
    ...     if topic1 is None:
    ...         topic1 = get_topic_by_name(sess.db, 'topic title')
    ...     sess.display(topic1)
"""
from contextlib import contextmanager

import pyArango.connection as pyconn
from pyArango.document import Document
import pyArango.collection as pcl
from pyArango.graph import Graph, EdgeDefinition
import pyArango.validation as pvl
from pyArango.theExceptions import ValidationError, InvalidDocument
import json
import os
import pprint

PATH_TO_CONFIG = os.path.expanduser('~/.ikconfig')

# keys are what I use in the code, values are what is used in the database
DB_NAMES = {
    'collections': {'topics': 'Topics', 'subtopic_links': 'SubtopicRelation'},
    'graphs': {'all_topics': 'TopicsGraph'},
    'fields': {
        'topics': {'name': 'name', 'description': 'description'},
        'subtopic_links': {'note': 'note'}
    }
}

MAX_LENGTHS = {'topic_name': 50, 'topic_description': 1000}

"""
ref for special collections:
https://github.com/ArangoDB-Community/pyArango/tree/5d9465cabca15a75477948c45bb57aa57fc90a0a
"""


@contextmanager
def session(config='default', create_if_missing=False):
    """
    The aim of this context manager (meant to be used in a with statement) is to:
        1. connect to ArangoDB with credentials fetched from a .json config file
        2. check whether the database is properly configured for indiek
    todo: accept on-the-fly configuration (no need to read from config file)
    """
    with open(PATH_TO_CONFIG) as f:
        conf = json.load(f)[config + '_config']

    conn = pyconn.Connection(username=conf['username'], password=conf['password'])
    db_name = conf['database']

    if not conn.hasDatabase(db_name):
        raise LookupError(f"database {db_name} not found; either it doesn't exist or arangodb"
                          f" user {conf['username']} from your config file doesn't have proper permissions")

    db = conn[db_name]

    def check_db_infrastructure(create_missing):
        """
        todo: provide option to delete useless collections (and graphs?)
        :param create_missing: (bool) if True, creates required collections and graphs for IndieK
        :return: None
        """
        topic_coll = DB_NAMES['collections']['topics']
        if not db.hasCollection(topic_coll):
            print(f"collection {topic_coll} not found in db {db.name}")
            if create_missing:
                db.createCollection(name=topic_coll, className='Topics')
                print(f"collection {topic_coll} created")

        # somehow the following fails
        #    db[COLL_NAMES['topics']].ensureFulltextIndex(list(TOPIC_FIELDS.values()))

        topic_links_coll = DB_NAMES['collections']['subtopic_links']
        if not db.hasCollection(topic_links_coll):
            print(f"collection {topic_links_coll} not found in db {db.name}")
            if create_missing:
                db.createCollection(name=topic_links_coll, className='SubtopicRelation')
                print(f"collection {topic_links_coll} created")

        graph_name = DB_NAMES['graphs']['all_topics']
        if not db.hasGraph(graph_name):
            print(f"database {db.name} has no graph named {graph_name}")
            if create_missing:
                db.createGraph(graph_name, createCollections=False)
                print(f"graph {graph_name} created")

    check_db_infrastructure(create_if_missing)

    try:
        yield db
    finally:
        conn.disconnectSession()


def db_setup(config_str):
    """
    Convenience function to make sure the database corresponding to the passed configuration string is set up.
    :param config_str: should match the config name in the config file (PATH_TO_CONFIG), e.g. 'default', 'test_db', etc.
    :return: None
    """
    with session(config=config_str, create_if_missing=True):
        pass


def db_erase(config_str):
    """
    erases (drops) collections and graphs corresponding to indiek in the database mentioned in config_str
    :param config_str: should match the config name in the config file (PATH_TO_CONFIG), e.g. 'default', 'test_db', etc.
    :return:
    """
    with session(config=config_str, create_if_missing=False) as db:
        db.dropAllCollections()


# def db_session(f):
#     """
#     decorator that allows to wrap any function that requires a database instance into a 'with' statement
#     :param f: a function that uses the kwarg 'database'; kwargs 'config' and 'create_if_missing' are passed to session()
#                 if present.
#     :return: decorated f
#     """
#     def f_with_session(*args, **kwargs):
#         to_session = {}
#         if 'config' in kwargs:
#             to_session['config'] = kwargs['config']
#         if 'create_if_missing' in kwargs:
#             to_session['create_if_missing'] = kwargs['create_if_missing']
#         with session(**to_session) as db:
#             kwargs['database'] = db
#             result = f(*args, **kwargs)
#         return result
#     return f_with_session

def equal_docs(d1, d2):
    return [d1[k] for k in d1.privates] == [d2[k] for k in d2.privates]


def extract_doc_privates(d):
    return tuple([d[k] for k in d.privates])


def get_topic_by_name(database, topic_name, as_simple_query=False):
    """
    fetches topic if exists, returns None otherwise
    todo: figure out what batchSize does
    Args:
        database: DBHandle or Database from pyArango module
        topic_name: string, name of topic
        as_simple_query: bool, if true returns SimpleQuery object, if false (default) returns Document object
    Returns:
        pyArango.query.SimpleQuery OR Topics document
    """
    topic_coll = DB_NAMES['collections']['topics']
    name_field = DB_NAMES['fields']['topics']['name']
    simple_query = database[topic_coll].fetchByExample({name_field: topic_name}, batchSize=100)
    if as_simple_query:
        return simple_query
    if simple_query.count > 0:
        return simple_query[0]
    else:
        return None


def display(elements, title, separator='==========', hide_privates=True, only_fields=None):
    """
    todo: accept graph-like argument
    todo: accept optional argument to only display specific fields
    todo: control field order in display
    :param elements: iterable of pyarango docs, (e.g. simple query object)
    :param title: str to display before anything else
    :param separator: str to display in between elements
    :param hide_privates: bool. If True, private doc attributes not shown. But interaction with only_fields arg are
                          complex, read below
    :param only_fields: list of strings containing field names for document store.
                        case1: only_fields is None; then hide_privates has highest authority
                        case2: only_fields is not None and only_fields contains no private field; then, all fields in
                          only_fields are displayed, and private fields are displayed according to hide_privates value
                        case3: only_fields contains a private field and hide_privates is False, then all private fields
                          are displayed, as well as the non-private fields from only_fields
                        case4: only_fields contains a private field and hide_privates is True, then only the fields in
                          only_fields are displayed.
    :return:
    """
    print(title)
    for el in elements:
        def delete_field(key):
            """
            :param key: key from store
            :return: True if key-value pair should be deleted from store
            """
            # two conditions in which field should be deleted, in most cases
            hide_privates_cond = hide_privates and (key in el.privates)
            only_fields_cond = (only_fields is not None) and (key not in only_fields)

            if only_fields is None:
                return hide_privates_cond  # case 1
            if only_fields is not None:
                assert len(set(only_fields)) == len(only_fields), "duplicate fields in argument only_fields"
                # bool below is True if only_fields contains no private field
                null_intersection = not bool(set(only_fields).intersection(set(el.privates)))
                if null_intersection:  # case 2
                    if hide_privates_cond or only_fields_cond:
                        return True
                    return False
                if hide_privates:
                    return only_fields_cond  # case 4
                return key not in set(only_fields).union(set(el.privates))  # case 3

        content = el.getStore()

        for k, v in content.items():
            if not delete_field(k):
                print(k + ': ' + v)
        print(separator)


class StringVal(pvl.Validator):
    """
    string validator for pyArango custom collections
    """
    def validate(self, value):
        if type(value) is not str:
            raise ValidationError("Field value must be a string")
        return True


# class PosIntVal(pvl.Validator):
#     """
#     positive integer validator for pyArango custom collections
#     """
#     def validate(self, value):
#         if type(value) is not int:
#             raise ValidationError("Field value must be an int")
#         elif value < 0:
#             raise ValidationError("level should be greater than zero")
#         else:
#             return True

# todo: do I need my own document class? Main use case would be to use _id, _key and _rev for comparison with __eq__
# class IkDocument(Document):
#     def __init__(self, pyarango_doc):
#         self.doc = pyarango_doc
#         self.ik_id = tuple(self[k] for k in self.privates)


class Topics(pcl.Collection):
    """
    Document collection for pyArango corresponding to topics
    """
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
        DB_NAMES['fields']['topics']['name']: pcl.Field(validators=[pvl.NotNull(),
                                                                    pvl.Length(2, MAX_LENGTHS['topic_name']),
                                                                    StringVal()]),
        DB_NAMES['fields']['topics']['description']: pcl.Field(validators=[pvl.NotNull(),
                                                                           pvl.Length(4,
                                                                                      MAX_LENGTHS['topic_description']),
                                                                           StringVal()]),
    }


class SubtopicRelation(pcl.Edges):
    """edge class to use to assign a topic as a subtopic of another"""
    pass


class TopicsGraph(Graph):
    """graph of all topics in the database. All topic management occurs through this graph."""
    _edgeDefinitions = [EdgeDefinition("SubtopicRelation",
                                       fromCollections=[DB_NAMES['collections']['topics']],
                                       toCollections=[DB_NAMES['collections']['topics']])]
    _orphanedCollections = []


class UserInterface:
    """
    Class through which all user interactions with ik database occurs. Should be used within a with block that provides
    the database as a context, via the session() module function.
    """
    def __init__(self, db):
        self.db = db
        self.topics_graph = self.db.graphs[DB_NAMES['graphs']['all_topics']]

    def create_topic(self, name, descr):
        """
        :param name: topic name (see Topics._fields for constraints)
        :param descr: topic description (see Topics._fields for constraints)
        :return: document if topic successfully created, otherwise None
        """
        if get_topic_by_name(self.db, name, as_simple_query=True):
            print(f"topic '{name}' already exists")
            doc = None
        else:
            doc = self.topics_graph.createVertex(
                DB_NAMES['collections']['topics'],
                {
                    DB_NAMES['fields']['topics']['name']: name,
                    DB_NAMES['fields']['topics']['description']: descr,
                }
            )
            doc.save()
        return doc

    def delete_topic(self, doc):
        """remove topic from database, and all linked edges"""
        self.topics_graph.deleteVertex(doc)

    def list_topics(self):
        """
        lists all topics in database
        :return:
        """

        simple_query = self.db[DB_NAMES['collections']['topics']].fetchAll()

        display(simple_query, title=f'LIST OF {simple_query.count} TOPICS IN DB')

    def set_subtopic(self, supratopic, subtopic):
        """
        sets topic "subtopic" as subtopic of "supratopic"
        :param supratopic: topic document or topic name
        :param subtopic: topic document or topic name
        :return:

        todo: check that topic1 and topic2 are 'up-to-date' before saving the link
        todo: get genealogy of both topics and warn the user if genalogies have non-zero intersection
        """
        name_field = DB_NAMES['fields']['topics']['name']
        subname = subtopic if isinstance(subtopic, str) else subtopic[name_field]
        supname = supratopic if isinstance(supratopic, str) else supratopic[name_field]
        if self.has_as_descendent(supratopic, subtopic):
            print(f"topic {subname} is already a descendent "
                  f"of topic {supname}. No new link created.")
        elif self.has_as_descendent(subtopic, supratopic):
            print(f"topic {subname} is already an ancestor "
                  f"of topic {supname}. No new link created to avoid loop.")
        else:
            if isinstance(supratopic, str):
                supratopic = get_topic_by_name(self.db, supratopic)
            if isinstance(subtopic, str):
                subtopic = get_topic_by_name(self.db, subtopic)
            self.topics_graph.link('SubtopicRelation', supratopic, subtopic, {})

    def has_as_descendent(self, supra, sub):
        """
        True if sub is in the list of subtopic descendents of supra
        :param supra: topic document (or name as str) supposed to be ancestor
        :param sub: topic document (or name as str) supposed to be descendent
        :return: (bool)
        """
        if isinstance(supra, str):
            supra = get_topic_by_name(self.db, supra)

        list_of_descendents = self.get_connected_component(supra, direction='outbound')

        if isinstance(sub, str):
            to_return = sub in list_of_descendents
        else:
            n = DB_NAMES['fields']['topics']['name']
            to_return = sub[n] in list_of_descendents
        return to_return

    def clear_topics(self):
        """
        removes all topics and their associated subtopic links from database.
        Doesn't delete collections
        :return:
        """
        simple_query = self.db[DB_NAMES['collections']['topics']].fetchAll()

        for topic in simple_query:
            self.topics_graph.deleteVertex(topic)

    def get_connected_component(self, topic, direction='outbound', depth=None):
        """
        my idea for this method is to create a graph in the database that corresponds to all the genealogy
        (ancestors and descendents) of a topic
        :param topic: any topic document
        :param direction:
        :param depth:
        :return: a list of vertices

        todo: control for duplicates in returned list?
        """
        name_field = DB_NAMES['fields']['topics']['name']
        if depth is None:
            q = self.topics_graph.traverse(topic, direction=direction)

            return [d[name_field] for d in q['visited']['vertices']]
        else:
            graph_name = DB_NAMES['graphs']['all_topics']

            q_str = f"FOR v IN 0..{depth} {direction.upper()} '{topic._id}' " \
                    f"GRAPH '{graph_name}' " \
                    f"RETURN v.{name_field}"
            return self.db.AQLQuery(q_str, rawResults=True)

    def get_extremal_topics(self, kind='minimal'):
        simple_query = self.db[DB_NAMES['collections']['topics']].fetchAll()

        if kind == 'minimal':
            dirr = 'inbound'
        elif kind == 'maximal':
            dirr = 'outbound'
        elif kind == 'singleton':
            dirr = 'any'
        else:
            raise ValueError("Invalid 'kind' argument, expects 'minimal', 'maximal' or 'singleton'")

        topic_list = []
        for t in simple_query:
            if len(self.get_connected_component(t, direction=dirr, depth=1)) == 1:
                topic_list.append(t)

        return topic_list

    def import_topics(self, f):
        """
        :param f: file-like object with read permission
        :return:
        """
        data = json.load(f)
        exclude = []
        for t in data['topics']:
            try:
                self.create_topic(t['name'], t['description'])
            except InvalidDocument as err:
                exclude.append(t['name'])
                print(f"Can't import topic with name {t['name']}")
                print(err)
        for r in data['relations']:
            if r['supratopic'] not in exclude and r['subtopic'] not in exclude:
                self.set_subtopic(r['supratopic'], r['subtopic'])

# def doc_in_list(document, list_of_docs):
#     doc_id = document['_id']
#     id_list = [d['_id'] for d in list_of_docs]
#     return doc_id in id_list
#
#
# def subtopic_link_exists(db, topic1, topic2):
#     out_edges = db[COLL_NAMES['subtopic_links']].getOutEdges(topic1)
#     in_edges = db[COLL_NAMES['subtopic_links']].getInEdges(topic2)
#     return any([doc_in_list(o, in_edges) for o in out_edges])
#
#
# def create_subtopic_link(db, topic1, topic2):
#     """

#     :param db:
#     :param topic1: topic obj
#     :param topic2: topic obj
#     :return:
#     """
#     if subtopic_link_exists(db, topic1, topic2):
#         print('subtopic link exists, link creation aborted')
#         return None
#
#     link = db[COLL_NAMES['subtopic_links']].createEdge()
#     link['_from'] = topic1['_id']
#     link['_to'] = topic2['_id']
#
#     link.save()
#     return link


if __name__ == "__main__":
    pass
