from unittest import TestCase
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
