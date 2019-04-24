"""
module indiek
v0.2.0 (Alpha)

Right now, the goal is mainly to find the right architecture for IndieK
In this module, 'ik' stands for the application IndieK
"""

__author__ = "Adrian Ernesto Radillo"

from collections import namedtuple

AllowedUIs = namedtuple('AllowedUIs', ['PYTHON_CONSOLE', 'SHELL'])
ALLOWED_UI_MODES = AllowedUIs(PYTHON_CONSOLE='pythonConsole')  # the point here is to have an 'immutable' dictionary

AllowedDBs = namedtuple('AllowedDBs', ['DUMMY_DATABASE'])
ALLOWED_DATABASES = AllowedDBs(DUMMY_DATABASE='DummyDB')

ITEM_TYPES = (
    'webpage',
    'post',
    'conversation',
    'video',
    'document',
    'image',
    'file',
    'unclassified'
)


class UserInterfaceSession:
    def __enter__(self):

        ui_mode = input('Starting IndieK session\nenter ui mode:')

        if ui_mode not in ALLOWED_UI_MODES:
            raise ValueError(f"ui_mode provided not allowed. Allowed types are {ALLOWED_UI_MODES}")

        if ui_mode == ALLOWED_UI_MODES.PYTHON_CONSOLE:
            self.user = input('enter your username: ')

            db_options = {}

            for i, j in enumerate(ALLOWED_DATABASES):
                db_options[i] = j

            db_choice = input(f'enter the number corresponding to the '
                              f'database you would like to use in this session.\n'
                              f'available databases are {db_options}: ')

            if db_options[int(db_choice)] == ALLOWED_DATABASES.DUMMY_DATABASE:
                self.db = DummyDB(self.user)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('enter __exit__')
        del self.db
        print('exiting IndieK session')

    def run(self):
        while True:










class DummyDB:
    """
    class to simulate a database for IndieK. This allows me to bypass real DB during the development of ik.
    """
    def __init__(self, user, max_items = 10):
        """
        dummy DB to test ik
        :param user: string for username
        :param max_items: max number of items allowed
        """

        # check user argument meets requirements
        if isinstance(user, str):
            self.user = user
        else:
            raise TypeError(f"user should be of type str, currently of type {type(user)}")

        self.items = set([])  # set containing all DummyDBItem from current DummyDB instance
        self.max_items = max_items

    def save_item(self, item):
        """
        adds item to DummyDB instance after converting Item to DummyDBItem
        :param item: instance of class Item
        :return: item.db_id
        """

    def _add_item(self, item):
        """
        adds item to DummyDB instance after converting Item to DummyDBItem
        :param item: instance of class Item
        :return: item.db_id
        """
        if isinstance(item, Item):
            if item.db_id in {i.item_id for i in self.items}:
                raise ValueError(f"item with Item.db_id {item.db_id} already in {self.__class__}")
            item_id = self._generate_item_id()
            self.items.add(item)
        return None

    @staticmethod
    def _generate_item_id(self):
        i = 1
        while True:
            yield DummyDBID(i)
            i += 1

    # do I need the following?
    def is_in_db(self, item):
        return item in self.items


class DummyDBID(str):
    """
    ID type for DummyDB class
    """
    pass


class DummyDBContent(str):
    """
    item Content type for DummyDB class
    """
    pass


class DummyDBItem:
    """
    Item class within the DB. This is my way of defining a schema within the DummyDB
    Since my DummyDB should only be manipulated through the BLL, a DummyDBItem must
    be initialized with a (BLL) Item.
    """
    def __init__(self, item):
        """
        initialize item in DummyDB by converting an item of type Item
        :param item: should be an instance of class Item
        """
        self._item_id = None
        self._content = None

    @property
    def item_id(self):
        return self._item_id

    @item_id.setter
    def item_id(self, item_id):
        if isinstance(item_id, DummyDBID):
            self._item_id = item_id
        else:
            raise TypeError(f"Cannot set item ID of type {type(item_id)} in {self.__class__}. "
                            "Type should be {type(DummyDBID)}")

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, content):
        if isinstance(content, DummyDBContent):
            self._content = content
        else:
            raise TypeError(f"Cannot set item content of type {type(content)} in {self.__class__}. "
                            "Type should be {type(DummyDBContent)}")


class Workspace:
    def __init__(self, ui_session):
        """
        :param db: database to use with this workspace
        """
        self.objects = set([])

    def create_item(self):
        item = Item(self.interaction_mode)
        self._add_object(item)

    # def _add_object(self):


class Item:
    """
    In ik v0.2.0, items are mainly URLs.
    Note: for now, I only allow for 1 DB to be used at a time, in an ik session
    """
    def __init__(self, item_creation_mode, db=None, item_db_id=None):
        """
        Item creation
        :param item_creation_mode: 'interactiveConsole'
        """
        self.allowed_creation_modes = {'pythonConsole', 'databaseLoad'}
        if item_creation_mode not in self.allowed_creation_modes:
            raise ValueError("item creation mode '{}' not recognized".format(item_creation_mode))

        self.db = db
        self.db_id = None  # attribute set by self.save_to_db()
        self.content = None  # attribute set by self.create_item()
        self.create_item(item_creation_mode)

    def create_item(self, item_creation_mode):
        """
        for now, it is understood that item creation occurs within a Workspace
        :param item_creation_mode:
        :return:
        """
        if item_creation_mode == "interactiveConsole":
            content = input('please enter item Content: ')
            # todo: instead of the conditional below, use property such as DummyDBItem.content
            if self.check_content_input(content):
                self.content = content
        elif item_creation_mode == "databaseLoad":
            self.load_from_db()

    def check_content_input(self, content):
        """
        todo: write this function
        :param content: item content
        :return: boolean
        """
        return True

    # def save_to_db(self, db):

