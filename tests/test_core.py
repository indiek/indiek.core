import io
import unittest
import sys
from pyArango.theExceptions import ConnectionError, ValidationError, InvalidDocument

# todo: clean up following imports
sys.path.append('../indiek/core/')
import indiek_core as ikcore

IK_CONFIG = 'test_db'
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


class TestDBInfrastructure(unittest.TestCase):
    """
    when a connection to the db is started
    """
    def test_faulty_connexion(self):
        self.assertRaises(ConnectionError, ikcore.session, config='missing_user')
        self.assertRaises(ConnectionError, ikcore.session, config='wrong_pwd')
        self.assertRaises(LookupError, ikcore.session, config='missing_db')
        self.assertRaises(LookupError, ikcore.session, config='unauthorized_user')

    def test_db_setup(self):
        """
        connects to test_db
        verifies no collections exist
        uses ik functionalities to create them (and graphs)
        deletes them
        """
        with ikcore.session(config=IK_CONFIG, create_if_missing=True) as db:
            for coll in ikcore.DB_NAMES['collections'].values():
                self.assertTrue(db.hasCollection(coll))
            for gr in ikcore.DB_NAMES['graphs'].values():
                self.assertTrue(db.hasGraph(gr))
            db.dropAllCollections()
            for coll in ikcore.DB_NAMES['collections'].values():
                self.assertFalse(db.hasCollection(coll))
            for gr in ikcore.DB_NAMES['graphs'].values():
                self.assertFalse(db.hasGraph(gr))


class TestQueries(unittest.TestCase):
    def test_list_topics(self):
        """
        add a topic and check it is in the output
        """
        # the following block taken from there: https://stackoverflow.com/a/34738440
        captured_output = io.StringIO()  # Create StringIO object
        sys.stdout = captured_output     # and redirect stdout.

        topic_name = 'test_topic'
        topic_descr = 'descr of test topic'

        with ikcore.session(config=IK_CONFIG) as db:
            sess = ikcore.UserInterface(db)
            topic = sess.create_topic(topic_name, topic_descr)
            sess.list_topics()      # Call function to test
            sess.delete_topic(topic)

        sys.stdout = sys.__stdout__      # Reset redirect.

        self.assertIn(topic_name, captured_output.getvalue())
        self.assertIn(topic_descr, captured_output.getvalue())

    def test_has_as_descendent(self):
        with ikcore.session(config=IK_CONFIG) as db:
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

            sess.clear_topics()


class TestTopicFieldValidation(unittest.TestCase):
    def test_topic_name(self):
        """
        name is empty string
        # todo: the remainder of this docstring
        name too long
        name not a string
        name contains space or tabs
        """
        with ikcore.session(config=IK_CONFIG) as db:
            sess = ikcore.UserInterface(db)
            self.assertRaises(InvalidDocument, sess.create_topic, '', 'descr')
            self.assertRaises(InvalidDocument, sess.create_topic, 'A', 'too short')
            self.assertRaises(InvalidDocument, sess.create_topic, 'missing description', '')


if __name__ == '__main__':
    unittest.main()

