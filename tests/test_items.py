import unittest
from indiek.core.items import Item


class TestItemAttr(unittest.TestCase):
    def test_instantiation(self):
        item = Item()
        self.assertTrue(hasattr(item, 'name'))


if __name__ == '__main__':
    unittest.main()