import unittest
from indiek.core.items import Item, Proof, Theorem, Definition
from indiek.core.search import list_all_items


CORE_ITEM_TYPES = [Proof, Theorem, Definition]


class TestSearch(unittest.TestCase):
    def setUp(self) -> None:
        """Make sure DB has at least 1 Item of each type."""
        self.ids = {cls: cls().save() for cls in CORE_ITEM_TYPES}

    def test_list_all_items(self):
        # at least written items from setUp should be present
        all_items = []
        for ilist in list_all_items().values():
            all_items += ilist
            
        all_item_ids = [i._ikid for i in all_items]
        for written in self.ids.values():
            self.assertIn(written, all_item_ids)
        
        # check count as well
        num = len(all_items)
        self.assertEqual(num, len(set(all_item_ids)))
        self.assertGreaterEqual(num, len(CORE_ITEM_TYPES))

        # check type-specific results are disjoint
        type_results = list_all_items(CORE_ITEM_TYPES)
        type_id_sets = {t: set([i._ikid for i in res]) for t, res in type_results.items()}
        sums = sum(len(id_set) for id_set in type_id_sets.values())
        self.assertEqual(len(set.union(*type_id_sets.values())), sums)
        
        # check type-specific results contain expected ids from setUp
        for core_type, ikid in self.ids.items():
            self.assertIn(ikid, type_id_sets[core_type])


if __name__ == '__main__':
    unittest.main()