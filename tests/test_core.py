import unittest
from pyArango.theExceptions import ConnectionError
# todo: clean up following imports
import sys
sys.path.append('../indiek/core/')
import indiek_core as ikcore
"""
List of things to test:
-    Connection
-        username
-        password
-        config file (ik should check validity of config file) 
-        port
-        database permissions
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


if __name__ == '__main__':
    unittest.main()

