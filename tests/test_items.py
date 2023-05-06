import unittest
from indiek.core.search import list_all_items
from indiek.core.items import Item
from indiek.mockdb.items import Item as DBitem
from indiek import mockdb


class TestItemAttr(unittest.TestCase):
    def test_instantiation(self):
        item = Item()
        expected_attr = [
            'name',
            'content',
            '_to_db',
            '_ikid',
            'save'
        ]
        for attr_name in expected_attr:
            self.assertTrue(hasattr(item, attr_name))


class TestItemIO(unittest.TestCase):
    db_driver = mockdb.items

    def test_to_db(self):
        pure_item = Item(driver=self.db_driver)
        db_item = pure_item._to_db()
        self.assertIsInstance(db_item, DBitem)        

    def test_item_io(self):
        pure_item = Item(name='someuniquename', driver=self.db_driver)
        pure_item.save()
        existing = list_all_items()
        # breakpoint()
        self.assertIn(pure_item, existing)


class TestComparison(unittest.TestCase):
    def test_core_vs_db(self):
        core = Item()
        db = core._to_db()
        self.assertFalse(core == db)

if __name__ == '__main__':
    unittest.main()
