import unittest
from indiek.core.items import Item
from indiek.core.search import list_all_items


class TestSearch(unittest.TestCase):
    def setUp(self) -> None:
        """Make sure DB has at least 1 Item"""
        dummy =  Item()
        dummy.save()

    def test_list_all_items(self):
        num = len(list_all_items())
        self.assertGreaterEqual(num, 1)

if __name__ == '__main__':
    unittest.main()