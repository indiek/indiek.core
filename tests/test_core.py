import io
import unittest
import sys
from pyArango.theExceptions import ConnectionError, ValidationError, InvalidDocument

# todo: clean up following imports
sys.path.append('../indiek/core/')
import indiek_core as ikcore
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
-        format and constraints of user input
-        saving to database
-        validity of database data (BLL), at input time and as diagnostic utility:
-            two topics with same name forbidden
-            duplicated subtopic links forbidden
-            subtopic link creation constraints about ancestors/descendents relations
-            timestamp fields update
-            text length
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


class TestDBInfrastructure(unittest.TestCase):
    """
    when a connection to the db is started
    """
    def test_missing_user(self):
        """
        make sure the following cell exists in your .ikconfig file
        "missing_user_config": {
            "username": "bamboo",
            "password": "",
            "database": ""
        }
        """
        self.assertRaises(ConnectionError, ikcore.ik_connect, config='missing_user')

    def test_wrong_password(self):
        """
        "wrong_pwd_config": {
            "username": "<correct username>",
            "password": "<wrong password>",
            "database": "<correct db name>"
        }
        """
        self.assertRaises(ConnectionError, ikcore.ik_connect, config='wrong_pwd')

    # def test_topics_graph_existence(self):
    #     pass

    def test_missing_db(self):
        """
        make sure the following cell exists in your .ikconfig file
        "missing_db_config": {
            "username": "<valid username>",
            "password": "<valid password>",
            "database": "<invalid database name>"
        },
        """
        self.assertRaises(LookupError, ikcore.ik_connect, config='missing_db')

    def test_unauthorized_user(self):
        """
        make sure the following cell exists in your .ikconfig file and that a user named <unauth> exists in your
        ArangoDB database which doesn't have access to the database <database>
        "unauthorized_user_config": {
            "username": "<unauth>",
            "password": "",
            "database": "<database>"
        }
        """
        self.assertRaises(LookupError, ikcore.ik_connect, config='unauthorized_user')


class TestQueries(unittest.TestCase):
    def setUp(self):
        self.sess = ikcore.UserInterface(conn_opts='test_db')

    def tearDown(self):
        del self.sess

    def test_list_topics(self):
        """
        add a topic and check it is in the output
        """
        topic_name = 'test_topic'
        topic_descr = 'descr of test topic'
        topic = self.sess.create_topic(topic_name, topic_descr)

        # the following block taken from there: https://stackoverflow.com/a/34738440
        captured_output = io.StringIO()  # Create StringIO object
        sys.stdout = captured_output     # and redirect stdout.

        self.sess.list_topics()      # Call function to test

        sys.stdout = sys.__stdout__      # Reset redirect.

        self.assertIn(topic_name, captured_output.getvalue())
        self.assertIn(topic_descr, captured_output.getvalue())
        self.sess.delete_topic(topic)

    def test_has_as_descendent(self):
        # create a basic graph (may already exist...)
        t1 = self.sess.create_topic('t1', 'minimal element')
        if t1 is None:
            t1 = ikcore.get_topic_by_name(self.sess.db, 't1')

        t2 = self.sess.create_topic('t2', 'same level as t1')
        if t2 is None:
            t2 = ikcore.get_topic_by_name(self.sess.db, 't2')

        t3 = self.sess.create_topic('t3', 'child of t1 and t2')
        if t3 is None:
            t3 = ikcore.get_topic_by_name(self.sess.db, 't3')

        t4 = self.sess.create_topic('t4', 'child of t3 and t5')
        if t4 is None:
            t4 = ikcore.get_topic_by_name(self.sess.db, 't4')

        t5 = self.sess.create_topic('t5', 'minimal element')
        if t5 is None:
            t5 = ikcore.get_topic_by_name(self.sess.db, 't5')

        # whole two_valid block might be redundant
        def two_valid(a, b):
            return (a is not None) and (b is not None)

        if two_valid(t1, t3):
            self.sess.set_subtopic(t1, t3)
        if two_valid(t2, t3):
            self.sess.set_subtopic(t2, t3)
        if two_valid(t3, t4):
            self.sess.set_subtopic(t3, t4)
        if two_valid(t4, t5):
            self.sess.set_subtopic(t5, t4)

        # assert statements
        self.assertTrue(self.sess.has_as_descendent(t1, t3))
        self.assertTrue(self.sess.has_as_descendent(t2, t3))
        self.assertTrue(self.sess.has_as_descendent(t3, t4))
        self.assertTrue(self.sess.has_as_descendent(t5, t4))

        self.assertTrue(self.sess.has_as_descendent(t2, t4))
        self.assertTrue(self.sess.has_as_descendent(t1, t4))

        self.assertFalse(self.sess.has_as_descendent(t3, t1))
        self.assertFalse(self.sess.has_as_descendent(t3, t2))
        self.assertFalse(self.sess.has_as_descendent(t4, t1))
        self.assertFalse(self.sess.has_as_descendent(t4, t5))

        self.assertFalse(self.sess.has_as_descendent(t2, t5))
        self.assertFalse(self.sess.has_as_descendent(t5, t2))


class TestTopicFieldValidation(unittest.TestCase):
    def setUp(self):
        self.sess = ikcore.UserInterface(conn_opts='test_db')

    def tearDown(self):
        del self.sess

    def test_topic_name(self):
        """
        name is empty string
        # todo: the remainder of this docstring
        name too long
        name not a string
        name contains space or tabs
        """
        self.assertRaises(InvalidDocument, self.sess.create_topic, '', 'descr')


if __name__ == '__main__':
    unittest.main()

