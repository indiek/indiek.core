import io
import unittest
import sys
import pprint
from tempfile import NamedTemporaryFile as Tmp
import json
from pyArango.theExceptions import ConnectionError, ValidationError, InvalidDocument

# todo: clean up following imports
sys.path.append('../indiek/core/')
import indiek_core as ikcore

TEST_CONFIG = 'test_db'
"""
List of things to test:
-    Connection
+        username
+        password
-        config file (ik should check validity of config file) -- might be taken care of by json module
-        port
+        database permissions
-        collection permissions
-    Creation/edition/deletion of info
+        format and constraints of user input
-        saving to database
-        validity of database data (BLL), at input time and as diagnostic utility:
+            two topics with same name forbidden
+            duplicated subtopic links forbidden (and self-reflecting as well)
+            subtopic link creation constraints about ancestors/descendents relations
-            timestamp fields update
+            text length
-            relation properties for user-defined relations
-        automatic info fetch:
-            from files
-            from web URL
-            from other APIs (mendeley/ emails)
-    Queries
-        info returned for each object (item/topic/graph)
-        organization of results (graphs-topics-items)
-        filters:
-            by date
-            by keywords
-            by graph properties (i.e. k-neighbors)
-        fuzzy search
-        compound queries (with filters on several levels)
-    Workspace?
"""
# todo: test display


class GraphForTests:
    minimal = ['t1', 't2', 't5', 't7']
    maximal = ['t7', 't9']
    singleton = list(set(minimal).intersection(maximal))

    test_topics_graph = {
        'topics': [
            {
                'name': 't1',
                'description': 'minimal element'
            },
            {
                'name': 't2',
                'description': 'same level as t1'
            },
            {
                'name': 't3',
                'description': 'child of t1 and t2'
            },
            {
                'name': 't4',
                'description': 'child of t3 and t5'
            },
            {
                'name': 't5',
                'description': 'minimal element'
            },
            {
                'name': 't6',
                'description': 'maximal element'
            },
            {
                'name': 't7',
                'description': 'minimal & maximal element & singleton'
            },
            {
                'name': 't8',
                'description': 'blablabla'
            },
            {
                'name': 't9',
                'description': 'maximal element'
            }
        ],
        'relations': [
            {
                'supratopic': 't1',
                'subtopic': 't3'
            },
            {
                'supratopic': 't2',
                'subtopic': 't3'
            },
            {
                'supratopic': 't3',
                'subtopic': 't4'
            },
            {
                'supratopic': 't5',
                'subtopic': 't4'
            },
            {
                'supratopic': 't4',
                'subtopic': 't6'
            },
            {
                'supratopic': 't6',
                'subtopic': 't8'
            },
            {
                'supratopic': 't8',
                'subtopic': 't9'
            }
        ]
    }

    @staticmethod
    def create_test_topics_graph(db):
        """
        a few words about this directed graph:
        t1 and t2 are immediate parents to t3
        t3 and t5 are immediate parents to t4
        t4 is an immediate parent to t6
        t6 immediate parent to t8
        t8 immediate parent to t9
        t7 is a singleton
        No other links exist, apart from these
        So, minimal elements are: [t1, t2, t5, t7]
        maximal elements are: [t9, t7]
        :param db: pyArango database (or DBHandle?)
        :return:
        """
        sess = ikcore.UserInterface(db)
        # create a basic graph (may already exist...)
        t1 = sess.create_topic('t1', 'minimal element')
        if t1 is None:
            t1 = ikcore.get_topic_by_name(sess.db, 't1')

        t2 = sess.create_topic('t2', 'same level as t1')
        if t2 is None:
            t2 = ikcore.get_topic_by_name(sess.db, 't2')

        t3 = sess.create_topic('t3', 'child of t1 and t2')
        if t3 is None:
            t3 = ikcore.get_topic_by_name(sess.db, 't3')

        t4 = sess.create_topic('t4', 'child of t3 and t5')
        if t4 is None:
            t4 = ikcore.get_topic_by_name(sess.db, 't4')

        t5 = sess.create_topic('t5', 'minimal element')
        if t5 is None:
            t5 = ikcore.get_topic_by_name(sess.db, 't5')

        t6 = sess.create_topic('t6', 'maximal element')
        if t6 is None:
            t6 = ikcore.get_topic_by_name(sess.db, 't6')

        t7 = sess.create_topic('t7', 'minimal & maximal element & singleton')
        if t7 is None:
            t7 = ikcore.get_topic_by_name(sess.db, 't7')

        t8 = sess.create_topic('t8', 'blablabla')
        if t8 is None:
            t8 = ikcore.get_topic_by_name(sess.db, 't8')

        t9 = sess.create_topic('t9', 'maximal element')
        if t9 is None:
            t9 = ikcore.get_topic_by_name(sess.db, 't9')

        # whole two_valid block might be redundant
        def two_valid(a, b):
            return (a is not None) and (b is not None)

        if two_valid(t1, t3):
            sess.set_subtopic(t1, t3)
        if two_valid(t2, t3):
            sess.set_subtopic(t2, t3)
        if two_valid(t3, t4):
            sess.set_subtopic(t3, t4)
        if two_valid(t4, t5):
            sess.set_subtopic(t5, t4)
        if two_valid(t4, t6):
            sess.set_subtopic(t4, t6)
        if two_valid(t6, t8):
            sess.set_subtopic(t6, t8)
        if two_valid(t8, t9):
            sess.set_subtopic(t8, t9)


def session_call(config, e):
    try:
        with ikcore.session(config=config):
            pass
    except e:
        raise


def topics_set(list_of_topics):
    return set([ikcore.extract_doc_privates(d) for d in list_of_topics])


def from_names_to_docs(list_of_topic_names, db):
    return [ikcore.get_topic_by_name(db, n) for n in list_of_topic_names]


def print_unequal_sets(s1, s2, query_num=None):
    if s1 != s2:
        if query_num:  # won't do anything if query_num is None or 0
            print('unequal sets in query ', query_num)
        pprint.pprint(s1)
        pprint.pprint(s2)


class TestDBInfrastructure(unittest.TestCase):
    """
    tests cases when a connection to the db is started with erroneous credentials
    """
    def test_faulty_connexion(self):
        self.assertRaises(ConnectionError,
                          session_call, 'missing_user', ConnectionError)
        self.assertRaises(ConnectionError,
                          session_call, 'wrong_pwd', ConnectionError)
        self.assertRaises(LookupError,
                          session_call, 'missing_db', LookupError)
        self.assertRaises(LookupError,
                          session_call, 'unauthorized_user', LookupError)

    def test_db_setup(self):
        ikcore.db_setup(TEST_CONFIG)

        with ikcore.session(config=TEST_CONFIG, create_if_missing=False) as db:
            for coll in ikcore.DB_NAMES['collections'].values():
                self.assertTrue(db.hasCollection(coll))
            for gr in ikcore.DB_NAMES['graphs'].values():
                self.assertTrue(db.hasGraph(gr))

            db.dropAllCollections()
            db.reload()

    def test_db_erase(self):
        ikcore.db_erase(TEST_CONFIG)

        with ikcore.session(config=TEST_CONFIG, create_if_missing=False) as db:
            for coll in ikcore.DB_NAMES['collections'].values():
                self.assertFalse(db.hasCollection(coll))
            for gr in ikcore.DB_NAMES['graphs'].values():
                self.assertFalse(db.hasGraph(gr))


class TestQueries(unittest.TestCase):
    def setUp(self):
        ikcore.db_setup(TEST_CONFIG)  # create indiek infrastructure in arangodb

        with ikcore.session(config=TEST_CONFIG) as db:  # create a test graph of topics
            GraphForTests.create_test_topics_graph(db)

    def tearDown(self):
        ikcore.db_erase(TEST_CONFIG)

    def test_list_topics(self):
        """
        add a topic and check it is in the output
        """
        # the following block taken from there: https://stackoverflow.com/a/34738440
        captured_output = io.StringIO()  # Create StringIO object
        sys.stdout = captured_output     # and redirect stdout.

        topic_name = 'test_topic'
        topic_descr = 'descr of test topic'

        with ikcore.session(config=TEST_CONFIG) as db:
            sess = ikcore.UserInterface(db)
            topic = sess.create_topic(topic_name, topic_descr)
            sess.list_topics()      # Call function to test
            sess.delete_topic(topic)

        sys.stdout = sys.__stdout__      # Reset redirect.

        self.assertIn(topic_name, captured_output.getvalue())
        self.assertIn(topic_descr, captured_output.getvalue())

    def test_has_as_descendent(self):
        with ikcore.session(config=TEST_CONFIG) as db:
            sess = ikcore.UserInterface(db)
            t1 = ikcore.get_topic_by_name(sess.db, 't1')
            t2 = ikcore.get_topic_by_name(sess.db, 't2')
            t3 = ikcore.get_topic_by_name(sess.db, 't3')
            t4 = ikcore.get_topic_by_name(sess.db, 't4')
            t5 = ikcore.get_topic_by_name(sess.db, 't5')

            # assert statements
            self.assertTrue(sess.has_as_descendent(t1, t3))
            self.assertTrue(sess.has_as_descendent(t2, t3))
            self.assertTrue(sess.has_as_descendent(t3, t4))
            self.assertTrue(sess.has_as_descendent(t5, t4))

            self.assertTrue(sess.has_as_descendent(t2, t4))
            self.assertTrue(sess.has_as_descendent(t1, t4))

            self.assertFalse(sess.has_as_descendent(t3, t1))
            self.assertFalse(sess.has_as_descendent(t3, t2))
            self.assertFalse(sess.has_as_descendent(t4, t1))
            self.assertFalse(sess.has_as_descendent(t4, t5))

            self.assertFalse(sess.has_as_descendent(t2, t5))
            self.assertFalse(sess.has_as_descendent(t5, t2))

            # sess.clear_topics()

    def test_get_connected_component(self):
        """
        todo: single vertex for unconnected topic
        todo: two vertices down for direction 'outbound'
        todo: three vertices up for direction 'inbound'
        todo: radius for
        :return:
        """
        with ikcore.session(config=TEST_CONFIG) as db:
            sess = ikcore.UserInterface(db)

            t1 = ikcore.get_topic_by_name(sess.db, 't1')
            t2 = ikcore.get_topic_by_name(sess.db, 't2')
            t3 = ikcore.get_topic_by_name(sess.db, 't3')
            t4 = ikcore.get_topic_by_name(sess.db, 't4')
            t5 = ikcore.get_topic_by_name(sess.db, 't5')
            t6 = ikcore.get_topic_by_name(sess.db, 't6')
            t7 = ikcore.get_topic_by_name(sess.db, 't7')
            t8 = ikcore.get_topic_by_name(sess.db, 't8')
            t9 = ikcore.get_topic_by_name(sess.db, 't9')

            def perform_checks(list1, list2, qid):
                if len(list1) != len(list2):
                    print('unequal lists in query ', qid)
                    print(list1)
                    print(list2)

                self.assertEqual(len(list1), len(list2))

                set1 = topics_set(from_names_to_docs(list1, sess.db))
                set2 = topics_set(from_names_to_docs(list2, sess.db))

                print_unequal_sets(set1, set2, qid)

                self.assertEqual(set1, set2)

            to_check = [
                {'query': sess.get_connected_component(t4, direction='any', depth=1),        # query 1
                 'correct': ['t4', 't3', 't5', 't6']},
                {'query': sess.get_connected_component(t4, direction='inbound', depth=1),    # query 2
                 'correct': ['t4', 't3', 't5']},
                {'query': sess.get_connected_component(t4, direction='outbound', depth=1),   # query 3
                 'correct': ['t4', 't6']},
                {'query': sess.get_connected_component(t7, direction='any', depth=1),        # query 4
                 'correct': ['t7']},
                {'query': sess.get_connected_component(t4, direction='inbound', depth=2),    # query 5
                 'correct': ['t1', 't2', 't3', 't4', 't5']},
                {'query': sess.get_connected_component(t4, direction='outbound', depth=2),   # query 6
                 'correct': ['t4', 't6', 't8']},
                {'query': sess.get_connected_component(t4, direction='any', depth=2),        # query 7
                 'correct': ['t1', 't2', 't3', 't4', 't5', 't6', 't8']},
                {'query': sess.get_connected_component(t4, direction='any'),                 # query 8
                 'correct': ['t1', 't2', 't3', 't4', 't6', 't8', 't9', 't5']},
                {'query': sess.get_connected_component(t4, direction='inbound'),             # query 9
                 'correct': ['t1', 't2', 't3', 't4', 't5']},
                {'query': sess.get_connected_component(t4, direction='outbound'),            # query 10
                 'correct': ['t4', 't6', 't8', 't9']},
                {'query': sess.get_connected_component(t3, direction='any', depth=0),        # query 11
                 'correct': ['t3']},
                {'query': sess.get_connected_component(t3, direction='outbound', depth=0),   # query 12
                 'correct': ['t3']}
            ]

            for qnum, pair in enumerate(to_check, start=1):
                perform_checks(pair['query'], pair['correct'], qnum)

    def test_get_extremal_topics(self):
        with ikcore.session(config=TEST_CONFIG) as db:
            sess = ikcore.UserInterface(db)
            self.assertRaises(ValueError, sess.get_extremal_topics, kind='wrong arg')
            self.assertRaises(ValueError, sess.get_extremal_topics, kind=0)

            minimal = sess.get_extremal_topics(kind='minimal')
            correct_min_set = topics_set(from_names_to_docs(GraphForTests.minimal, sess.db))
            # print([d['name'] for d in minimal])
            # print(GraphForTests.minimal)
            print_unequal_sets(topics_set(minimal), correct_min_set, 1)
            self.assertEqual(topics_set(minimal), correct_min_set)

            maximal = sess.get_extremal_topics(kind='maximal')
            correct_max_set = topics_set(from_names_to_docs(GraphForTests.maximal, sess.db))
            print_unequal_sets(topics_set(maximal), correct_max_set, 2)
            self.assertEqual(topics_set(maximal), correct_max_set)

            singletons = sess.get_extremal_topics(kind='singleton')
            correct_singleton_set = topics_set(from_names_to_docs(GraphForTests.singleton, sess.db))
            print_unequal_sets(topics_set(singletons), correct_singleton_set, 3)
            self.assertEqual(topics_set(singletons), correct_singleton_set)


class TestTopicFieldValidation(unittest.TestCase):
    """
    more generally, tests the Topics schema

    todo: check that duplicating a topic name is forbidden/impossible
    """
    def setUp(self):
        ikcore.db_setup(TEST_CONFIG)

    def tearDown(self):
        ikcore.db_erase(TEST_CONFIG)

    def test_topic_name(self):
        """
        name is empty string
        # todo: the remainder of this docstring
        name too long
        name not a string
        name contains space or tabs
        """
        with ikcore.session(config=TEST_CONFIG) as db:
            sess = ikcore.UserInterface(db)
            self.assertRaises(InvalidDocument, sess.create_topic, '', 'descr')
            self.assertRaises(InvalidDocument, sess.create_topic, 'A', 'too short')
            self.assertRaises(InvalidDocument, sess.create_topic, 'missing description', '')

    def test_equal_doc(self):
        with ikcore.session(config=TEST_CONFIG) as db:
            sess = ikcore.UserInterface(db)
            topic1 = sess.create_topic('topic1', 'some descr')
            topic2 = sess.create_topic('topic2', 'another descr')
            self.assertTrue(ikcore.equal_docs(topic1, topic1))
            self.assertFalse(ikcore.equal_docs(topic1, topic2))
            # todo: check what happens if topic1 is modified, patched and if its privates are forcefully edited
            # remember the useful method doc.setPrivates({'_rev': 'new val'})


class TestBulkImport(unittest.TestCase):
    def setUp(self):
        ikcore.db_setup(TEST_CONFIG)

    def tearDown(self):
        ikcore.db_erase(TEST_CONFIG)

    def test_import_topics(self):
        with ikcore.session(config=TEST_CONFIG) as db:
            sess = ikcore.UserInterface(db)
            with Tmp(mode='w+t', delete=False, encoding='utf-8') as f:
                json.dump(GraphForTests.test_topics_graph, f, ensure_ascii=False, indent=4)
                filename = f.name
            with open(f.name, 'r') as f:
                sess.import_topics(f)
            t1 = ikcore.get_topic_by_name(sess.db, 't1')
            self.assertTrue(t1 is not None)
            self.assertTrue(sess.has_as_descendent(t1, 't3'))
            self.assertTrue(sess.has_as_descendent('t3', 't9'))

if __name__ == '__main__':
    unittest.main()

