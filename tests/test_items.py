import unittest
from indiek.core.items import Item
from indiek.mockdb.items import Item as DBitem
from indiek import mockdb


class TestItemAttr(unittest.TestCase):
    def test_instantiation(self):
        item = Item()
        expected_attr = [
            'name',
            'content',
            'to_db'
        ]
        for attr_name in expected_attr:
            self.assertTrue(hasattr(item, attr_name))


class TestItemIO(unittest.TestCase):
    db_driver = mockdb.items

    def test_item_io(self):
        pure_item = Item(driver=self.db_driver)
        db_item = pure_item.to_db()
        self.assertIsInstance(db_item, DBitem)


if __name__ == '__main__':
    unittest.main()
