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

