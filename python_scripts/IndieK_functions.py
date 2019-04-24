# requires the following imports
from pyArango.connection import *
from pyArango.document import Document
from pyArango.collection import Collection, Field
from pyArango.graph import Graph, EdgeDefinition
import uuid

# type following lines in console to use classes from this script
# from IndieK_functions import *
# connection = Connection(username="root", password="l,.7)OCR")


class Workspace:
    """
    Main user interface. Items, topics and graphs are loaded from and saved to the db from this class

    GENERAL NOTES ABOUT THE WORKSPACE CLASS
    A Workspace instance contains its objects into its self.objects dict.
    As of now, this dict has only three keys: 'items', 'topics' and 'graphs'.
    To access an Item object from the workspace, use self.objects['items'][<wid>]
    where wid is a String (wid stands for Workspace ID).
    All the wid's must be distinct, even across object types.
    That is, if an Item and a Topic are both contained in self.objects, then they
    cannot have same wid.
    """
    # todo: check method add_item(); especially if item is taken from another workspace
    # todo: consider making all the methods private with prefix _
    def __init__(self, connection, dbname="test", interactive=True):
        # todo: think of how an objects dict may be passed to this method
        self.conn = connection
        # opens DB
        self.db = self.conn[dbname]

        # instantiate collections
        # todo: all these collections should be defined (have their own class) in IndieK's BLL
        self.items_collection = self.db["items"]
        self.topics_collection = self.db["topics"]
        # Collections for relations
        # self.topics_elements_relation_collection = self.db["topics_elements_relation"]
        # self.items_relation_1_collection = self.db["items_relation_1"]
        # self.subtopics_relation_collection = self.db["subtopics_relation"]

        # instantiate graphs
        self.graph_topics_elements = self.db.graphs["topics_elements"]
        self.graph_items_1 = self.db.graphs['items_graph']  # edges = items_relation_1
        self.graph_topics_1 = self.db.graphs['topics_graph']  # edges = subtopics_relation

        # NOTE: the keys for the dict objects below should match the .type attribute of the BLL objects
        self.objects = {'items': {}, 'topics': {}, 'graphs': {}}
        self.interactive = interactive
        self.types = ('items', 'topics', 'graphs')

    def get_type_from_wid(self, wid):
        """returns the BLL type of an object from the workspace, given its wid"""
        # todo: Can I simplify this method using self.is_in_workspace()?
        if wid in self.objects['items'].keys():
            return 'items'
        elif wid in self.objects['topics'].keys():
            return 'topics'
        elif wid in self.objects['graphs'].keys():
            return 'graphs'
        else:
            print('wid not in workspace')
            return None

    def create_all_obj_dict(self):
        # todo: check whether following line is best practice
        return {**self.objects['items'], **self.objects['topics'], **self.objects['graphs']}

    def summary(self):
        print('workspace contains:')
        print('%i graphs' % len(self.objects['graphs']))
        print('%i topics' % len(self.objects['topics']))
        print('%i items' % len(self.objects['items']), end='\n\n')

    def diagnostic(self):
        self.summary()
        self.list_topics()
        self.list_items(content=True)

    def is_in_workspace(self, **kwargs):
        """
        checks whether object obj is already in workspace using either object, _id or wid
        :param kwargs: arg name must be one of 'obj', '_id', 'wid'
        :return: True or False
        """
        # todo: is this structure with **kwargs really necessary?
        if len(kwargs) != 1:
            print('Single keyword parameter expected')
            return
        # create list of object _id's in workspace
        all_obj_dict = self.create_all_obj_dict()
        all_obj_ids = [o["_id"] for o in all_obj_dict.values()]
        if 'obj' in kwargs.keys():
            return kwargs['obj']["_id"] in all_obj_ids
        elif '_id' in kwargs.keys():
            return kwargs['_id'] in all_obj_ids
        elif 'wid' in kwargs.keys():
            return kwargs['wid'] in all_obj_dict.keys()

    def generate_workspace_id(self):
        """generates a new unique workspace id (wid)"""
        workspace_id = str(uuid.uuid4())[0:6]
        all_obj_dict = self.create_all_obj_dict()
        while workspace_id in all_obj_dict.keys():
            workspace_id = str(uuid.uuid4())[0:6]
        return workspace_id

    def remove_object(self, obj_wid, delete_from_db=False):
        """
        remove object from workspace, and deletes it from db if requested

        WARNING: This method heavily uses the following two facts:
        1. all objects from Workspace should have a method delete_from_db()
        2. equality operator for such objects is identity (not copy)
        """
        all_obj_dict = self.create_all_obj_dict()
        if obj_wid in all_obj_dict.keys():
            if delete_from_db:
                all_obj_dict[obj_wid].delete_from_db()
            obj_type = self.get_type_from_wid(obj_wid)
            del self.objects[obj_type][obj_wid]
        else:
            print('item not in workspace. Nothing done')

    def add_object(self, obj):
        """
        adds an existing object to the self.objects[object.type] dict
        :param obj: an object from IndieK's BLL
        :return: changes the self.objects dict + stdout
        """
        # check that object is not already in workspace
        # todo: think whether we might want to duplicate items within workspace
        if self.is_in_workspace(obj=obj):
            print('WARNING: object with _id ' + obj['_id'] + ' already in workspace. Nothing done.')
        else:
            # check obj.type is acceptable
            try:
                if obj.type in self.types:
                    # check wid is not already used
                    if obj.wid in self.objects[obj.type].keys():
                        obj.wid = self.generate_workspace_id()
                    # add object to workspace
                    self.objects[obj.type][obj.wid] = obj
                else:
                    raise ValueError("the provided object's type is not supported by this method")
            except AttributeError as err:
                print(err.args)

    def fetch_object(self, key, obj_type, rawResults=False, rev=None):
        """
        function based on pyArango.collection.Collection.fetchDocument()
        fetches object from db and tries to insert it into workspace.
        returns string to stdout if object already in workspace

        NOTE: this method currently only instantiates objects of type Item or Topic

        :param key: _key field from ArangoDB
        :param obj_type: a type from the BLL
        """
        if obj_type == 'items':
            collection = self.items_collection
        elif obj_type == 'topics':
            collection = self.topics_collection
        else:
            print('sorry the provided object type is not recognized by this method yet')
            return

        # todo: figure out what we want to do if object is already loaded in workspace (duplicate it + warning?)
        url = "%s/%s/%s" % (collection.documentsURL, collection.name, key)
        if rev is not None:
            r = collection.connection.session.get(url, params={'rev': rev})
        else:
            r = collection.connection.session.get(url)
        if (r.status_code - 400) < 0:
            if rawResults:
                return r.json()
            wid = self.generate_workspace_id()
            if obj_type == 'items':
                obj = Item(wid, collection, r.json())
                obj.as_in_db = True
                print('item fetched:')
                obj.display_info()
            elif obj_type == 'topics':
                obj = Topic(wid, collection, r.json())
                obj.as_in_db = True
                print('topic fetched')
                obj.display_info()
            self.add_object(obj)
        else:
            raise KeyError("Unable to find object with _key: %s" % key, r.json())

    def save_to_db(self, obj_wid):
        """saves object from workspace to db using method from the relevant object's class"""
        all_objects = self.create_all_obj_dict()
        if obj_wid in all_objects.keys():
            all_objects[obj_wid].save_to_db()
        else:
            print('object not in workspace. Nothing done')

    """METHODS RELATED TO ITEMS MANIPULATION"""

    def list_items(self, content=False):
        print('List of workspace items:')
        for item in self.objects['items'].values():
            # todo: find out why PyCharm produces a warning at the next line
            item.display_info(display_content=content)

    def create_new_item(self, item_content=None, save_to_db=False):
        """
        Creates new item and saves it to db if save_to_db=True.
        :return: save to db + stdout
        """
        # todo: add automatic timestamp fields for creation and last modification dates

        # 1. get item content from user
        # the following is a chunk copied from this link in order to get multiline text input
        # https://stackoverflow.com/a/11664675/8787400
        if self.interactive:
            print('Enter content of new item: ')
            sentinel = ''  # ends when the empty string is seen
            new_item_string = '\n'.join(iter(input, sentinel))
            # to check what has been inputted:
            # for x in new_item_string.split('\n'):
            #    print(x)
        else:
            new_item_string = item_content

        # 2. generate workspace id
        wid = self.generate_workspace_id()

        # 3. create item according to collection's method
        new_item = Item(wid, self.items_collection, {"content": new_item_string})
        print('newly created item with workspace id: ' + new_item.wid)

        # 4. update workspace
        self.objects['items'][wid] = new_item

        # 5. save to db if requested
        if save_to_db:
            self.objects['items'][wid].save_to_db()

    """ Methods below are all based on methods with same name in Item class"""
    # todo: check whether this is a good class architecture

    def display_item_info(self, item_wid, display_content=False):
        """displays on stdout item's main info"""
        if item_wid in self.objects['items'].keys():
            self.objects['items'][item_wid].display_info(display_content=display_content)
        else:
            print('item not in workspace. Nothing done')

    def display_item_content(self, item_wid):
        """displays to stdout item content from workspace using method from Item class"""
        if item_wid in self.objects['items'].keys():
            self.objects['items'][item_wid].display_item_content()
        else:
            print('item not in workspace. Nothing done')

    def edit_item(self, item_wid, item_content=None, save_to_db=False, interactive=True):
        # todo: produce a warning or maybe abort if item_content is not None and interactive=True
        """ 'imported' method from Item class"""
        if item_wid in self.objects['items'].keys():
            self.objects['items'][item_wid].edit_item(item_content, save_to_db, interactive)
        else:
            print('item not in workspace. Nothing done')

    """METHODS RELATED TO TOPICS MANIPULATION"""

    def list_topics(self):
        print('List of workspace topics:')
        for topic in self.objects['topics'].values():
            topic.display_info()

    def create_new_topic(self, save_to_db=False):
        """
        Creates new topic and saves it to db if save_to_db=True.
        :return: save to db + stdout
        """
        # todo: add automatic timestamp fields for creation and last modification dates
        # todo: think of what constraints should be enforced on topic name and description and implement checks

        if self.interactive:
            # 1. get topic name from user
            print('Enter name of new topic: (30 chars max)')
            sentinel = ''  # ends when the empty string is seen
            new_topic_name = '\n'.join(iter(input, sentinel))
            # 2. get topic description from user
            print('Enter description of new topic (1 line): ')
            sentinel = ''  # ends when the empty string is seen
            new_topic_descr = '\n'.join(iter(input, sentinel))
        else:
            print("this method can't be used in non-interactive mode yet")
            return None

        # 2. generate workspace id
        wid = self.generate_workspace_id()

        # 3. create topic according to collection's method
        new_topic = Topic(wid, self.topics_collection,
                          dict(name=new_topic_name, description=new_topic_descr))
        print('newly created topic with workspace id: ' + new_topic.wid)

        # 4. update workspace
        self.objects['topics'][wid] = new_topic

        # 5. save to db if requested
        if save_to_db:
            self.objects['topics'][wid].save_to_db()

    """METHODS RELATED TO LINK MANIPULATION"""

    def link_items(self, wid_from, wid_to, save_to_db=False):
        """
        Creates a link between two items in the workspace
        :param wid_from: wid of the source item
        :param wid_to: wid of the target item
        :param save_to_db: saves link to db if True
        :return:
        """
        # what happens if wid's provided don't correspond to objects in WS?
        # check that both objects are items
        if self.get_type_from_wid(wid_from) != 'items' or self.get_type_from_wid(wid_to) != 'items':
            print('At least one of the wid provided is not an Item')
            return
        parent = self.objects['items'][wid_from]
        child = self.objects['items'][wid_to]
        # test whether link already exists
        if link_exists:
            print('link already exists')
        else:
            if save_to_db:
                self.graph_items_1.link('items_relation_1', parent, child, {})
            # parent.children += [wid_to]
            # child.parents += [wid_from]


class Item(Document):
    """
    item object in IndieK's BLL
    """
    def __init__(self, wid, collection, jsonFieldInit={}):
        # todo: is the empty dict default argument best practice here?
        # todo: I don't know if this use of super() is best practice
        super().__init__(collection, jsonFieldInit)
        # todo: think whether attr wid is good given that it might be used outside of worksp (e.g. DbExploration?)
        self.wid = wid
        self.as_in_db = False
        self.type = 'items'  # todo: check whether it makes more sense to overwrite the typeName attribute
        # lists of _id's and wid's
        # todo: figure out how to initialize the lists below?
        self.parents = []
        self.children = []
        self.topics = []

    def display_info(self, display_content=False):
        """displays on stdout item's main info"""
        print("_id: %s" % self['_id'])
        print("_key: %s" % self["_key"])
        print("_rev: %s" % self["_rev"])
        print("wid: %s" % self.wid)
        print('as in db: %s' % self.as_in_db, end='\n\n')
        if display_content:
            self.display_content()

    def display_content(self):
        """
        fetches and displays content field from the item specified by the arguments
        :return: stdout
        """
        content_separator = '-------'
        print("content:\n%s\n%s\n%s\n" % (content_separator,
                                          self['content'],
                                          content_separator))

    def delete_from_db(self):
        """
        removes item specified by arguments from ArangoDB
        :return: delete from db + stdout

        WARNING: if item was obtained from a workspace with the equality operator,
        i.e. if item is obtained via the command: item=Workspace.items[wid]
        then this method directly affects the item from the workspace.
        """
        # todo: Is the warning above a problem or a desired feature?
        # todo: check behavior when same item is in both workspaces. Do we have indep?
        # todo: amend this method once relations with item nodes exist
        key = self['_key']
        self.delete()
        self.as_in_db = False
        print('item ' + key + ' has been deleted from db %s' % self.collection.database)

    def save_to_db(self):
        """
        save item to db

        WARNING: if item was obtained from a workspace with the equality operator,
        i.e. if item is obtained via the command: item=Workspace.items[wid]
        then this method directly affects the item from the workspace.
        """
        if self["_id"] is None:
            self.save()
            self.as_in_db = True
            print('item with workspace id %s got assigned _key %s: ' % (self.wid, self["_key"]))
        else:
            self.patch()
            self.as_in_db = True
            print('new item content was saved to db')

    def edit_item(self, item_content=None, save_to_db=False, interactive=True):
        # todo: run some validation on item_content
        # todo: think of an interactive way of editing existing content
        if interactive:
            print('Enter new content for item: ')
            sentinel = ''  # ends when the empty string is seen
            item_content = '\n'.join(iter(input, sentinel))
        if item_content is not None:
            self['content'] = item_content
            self.as_in_db = False
        else:
            print('no content was provided, item left unchanged')
        if save_to_db:
            self.save_to_db()


class Topic(Document):
    """
    Topic object in IndieK's BLL
    """
    def __init__(self, wid, collection, jsonFieldInit={}):
        super().__init__(collection, jsonFieldInit)
        self.wid = wid
        self.as_in_db = False
        self.type = 'topics'

    def display_info(self):
        """displays on stdout item's main info"""
        print("_id: %s" % self['_id'])
        print("_key: %s" % self["_key"])
        print("_rev: %s" % self["_rev"])
        print("wid: %s" % self.wid)
        print('as in db: %s' % self.as_in_db)
        print('topic name: %s' % self["name"])
        print('topic descr: %s' % self['description'], end='\n\n')

    # todo: write the method list_items_info below
    # def list_items_info(self):
    #     """
    #     list the info from topic's items
    #     :return: stdout
    #     """
    #     return list_of_items

    def delete_from_db(self):
        """
        removes topic specified by arguments from ArangoDB
        :return: delete from db + stdout
        """
        # todo: amend this method once relations with topic nodes exist
        key = self['_key']
        self.delete()
        self.as_in_db = False
        print('topic ' + key + ' has been deleted from db %s' % self.collection.database)

    def save_to_db(self):
        """
        save topic to db
        """
        if self["_id"] is None:
            self.save()
            self.as_in_db = True
            print('topic with workspace id %s got assigned _key %s: ' % (self.wid, self["_key"]))
        else:
            self.patch()
            self.as_in_db = True
            print('new topic fields were saved to db')


class DbExplore:
    """
    This class should strictly be used to consult the database. Never to write to it.
    """
    def __init__(self, connection, dbname="test"):
        self.conn = connection
        # opens DB test
        self.db = self.conn[dbname]  # database object from PyArango driver
        # instantiate collections
        self.items_collection = self.db["items"]
        self.topics_collection = self.db["topics"]
        self.topics_elements_relation_collection = self.db["topics_elements_relation"]
        self.items_relation_1_collection = self.db["items_relation_1"]
        self.subtopics_relation_collection = self.db["subtopics_relation"]
        self.graph_topics_elements = self.db.graphs["topics_elements"]

    def list_all_items(self, content=False):
        """
        lists info from all items in db

        :param content: if True, displays item content on stdout
        """
        line_sep = '\n==============================\n'
        print(line_sep)
        for item in self.items_collection.fetchAll():
            print("_id: %s" % item['_id'])
            print("_key: %s" % item["_key"])
            print("_rev: %s" % item["_rev"])
            if content:
                print('content: %s' % item['content'])
            print(line_sep)

    def search_and_item_string(self, *args):
        """
        performs a full match of all the strings (not case sensitive). Uses AND connector.
        :param args: strings to match in content fields from items in db.
              !NOTE! beginning and end of each string must match beginning and end of words in field
        :return: stdout
        """
        words = ','.join(args)
        aql = 'FOR item IN FULLTEXT(items, "content", "' + words + '") ' \
              'RETURN {key: item._key, content: item.content}'
        query_result = self.db.AQLQuery(aql, rawResults=True, batchSize=100)
        for item in query_result:
            item.display_item_info(display_content=True)

    def search_or_item_string(self, *args):
        """
        performs a full match of all the strings (not case sensitive). Uses OR connector.
        :param args: strings to match in content fields from items in db.
              !NOTE! beginning and end of each string must match beginning and end of words in field
        :return: stdout
        """
        words = ',|'.join(args)
        aql = 'FOR item IN FULLTEXT(items, "content", "' + words + '") ' \
              'RETURN {key: item._key, content: item.content}'
        query_result = self.db.AQLQuery(aql, rawResults=True, batchSize=100)
        for item in query_result:
            item.display_item_info(display_content=True)

    def list_all_topics(self):
        """
        list topic names and descriptions that are stored in db
        :return: stdout
        """
        line_sep = '\n==============================\n'
        print(line_sep)
        for doc in self.topics_collection.fetchAll():
            print("_id: %s" % doc['_id'])
            print("_key: %s" % doc["_key"])
            print("_rev: %s" % doc["_rev"])
            print(doc['name'])
            print(doc['description'])
            print(line_sep)


if __name__ == "__main__":
    # to run this script in interactive mode from Python's console,
    # type the following at the start of the console session
    #
# from IndieK_functions import *
# conn = Connection(username="root", password="l,.7)OCR")
# w = Workspace(conn)
# db = DbExplore(conn)
    #
    # from there, you are good to play with the methods of w and db

    # everything from here onwards is for batch mode
    conn = Connection(username="root", password="openSesame")
    # create workspace
    # w1 = Workspace(conn, interactive=False)
    #
    # # create new item
    # # new_item_content = 'hello\nyou world'
    # # w1.create_new_item(new_item_content)
    #
    # # fetch existing item from db
    # item_key = '174480'
    # w1.fetch_item(item_key)
    #
    # # save item to db
    # item_id = list(w1.items.keys())[0]
    # w1.items[item_id].save_item_to_db()
    # w1.list_items(content=True)
    # w1.diagnostic()
    # create new topic

    db = DbExplore(conn)

'''
Console example for success for edge creation (item in topic)
from IndieK_functions import *
conn = Connection(username="root", password="l,.7)OCR")
w = Workspace(conn)
db = DbExplore(conn)
w.fetch_object('438192','items')
    item fetched:
    _id: items/438192
    _key: 438192
    _rev: _WoRa1sK--_
    wid: 596325
    as in db: True
w.fetch_object('471606','topics')
    topic fetched
    _id: topics/471606
    _key: 471606
    _rev: _WoV9L2y--_
    wid: 92075a
    as in db: True
    topic name: et le marathon
    topic descr: et pour une fois que je gagne!
obj1 = w.objects['items']['596325']
obj2 = w.objects['topics']['92075a']
db.graph_topics_elements.link('topics_elements_relation', obj2, obj1, {})
    ArangoEdge '_id: topics_elements_relation/915654, _key: 915654, _rev: _WvEkrtG--_, _to: items/438192, _from: topics/471606': <store: {}>

PB: allows duplicate edges
'''