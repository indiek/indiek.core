import unittest
import re
from indiek.core.items import  Proof, Theorem, Definition
from indiek.core.search import list_all_items, search_and_cast, build_search_query, filter_str


CORE_ITEM_TYPES = [Proof, Theorem, Definition]


class TestSearch(unittest.TestCase):
    def setUp(self) -> None:
        """Make sure DB has at least 1 Item of each type."""
        self.ids = {cls: cls(name=str(cls)).save() for cls in CORE_ITEM_TYPES}

    def test_list_all_items(self):
        # all written items have 'class' in their name
        class_in_name = filter_str("class")
            
        for written_cls in self.ids.keys():
            loaded_item = written_cls.load(self.ids[written_cls])
            self.assertIn(loaded_item, class_in_name[written_cls])
        
        # only Theorem and Proof items have 'theorem' or 'proof' word
        thm_prf = filter_str('theorem proof')
        
        # check type-specific results contain expected ids from setUp
        for core_type, core_items in thm_prf.items():
            if core_type in {Theorem, Proof}:
                self.assertTrue(core_items)
            elif core_type == Definition:
                self.assertFalse(core_items)

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

    def test_search_and_cast(self):
        thm_query = re.compile('Theorem')
        thm_result = search_and_cast(thm_query, Theorem)

        written_thm = Theorem.load(self.ids[Theorem])
        self.assertIn(written_thm, thm_result)

        written_proof = Proof.load(self.ids[Proof])
        proof_result = search_and_cast(thm_query, Proof)
        self.assertNotIn(written_proof, proof_result)

    def test_build_search_query(self):
        raw_str = r'user typed This'
        query = build_search_query(raw_str)
        base_str = '('
        base_str += '|'.join(raw_str.split())
        base_str += ')'
        correct_query = re.compile(base_str, flags=re.IGNORECASE)
        self.assertEqual(correct_query, query)

if __name__ == '__main__':
    unittest.main()