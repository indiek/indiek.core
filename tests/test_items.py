import unittest
from indiek.core.items import Item, Definition, Theorem, Proof
from indiek.mockdb.items import Item as DBitem
from indiek import mockdb

CORE_ITEM_TYPES = [Definition, Theorem, Proof]

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

        for core_cls in CORE_ITEM_TYPES:
            pure_item = core_cls(driver=self.db_driver)
            db_item = pure_item._to_db()
            self.assertIsInstance(db_item, pure_item.BACKEND_CLS)

    def test_item_io(self):
        """Each item type gets written and retrieved."""
        for item_type in CORE_ITEM_TYPES:
            core_item = item_type(driver=self.db_driver)
            core_item.save()
            new_item = item_type.load(core_item._ikid)
            self.assertEqual(core_item, new_item)
            

class TestComparison(unittest.TestCase):
    def test_core_vs_db(self):
        core = Item()
        db = core._to_db()
        self.assertFalse(core == db)


if __name__ == '__main__':
    unittest.main()
