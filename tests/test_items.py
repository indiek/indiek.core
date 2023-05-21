import unittest
from indiek.core.items import (Item, 
                               Definition, 
                               CORE_ITEM_TYPES, 
                               Note, 
                               PointerNote, 
                               NestedNoteLoop, 
                               AddContentToPointerNote)
from indiek.mockdb.items import Definition as DBDefinition
from indiek import mockdb


class TestItemAttr(unittest.TestCase):
    def test_instantiation(self):
        item = Item()
        expected_attr = [
            'name',
            'content',
            '_to_db',
            'ikid',
            'save'
        ]
        for attr_name in expected_attr:
            self.assertTrue(hasattr(item, attr_name))
    
    def test_notes_presence(self):
        item = Definition()
        self.assertIsInstance(item.name, Note)
        self.assertIsInstance(item.content, Note)


class TestItemIO(unittest.TestCase):
    db_driver = mockdb.items

    def test_to_db(self):
        pure_item = Definition(driver=self.db_driver)
        db_item = pure_item._to_db()
        self.assertIsInstance(db_item, DBDefinition)

        for core_cls in CORE_ITEM_TYPES:
            pure_item = core_cls(driver=self.db_driver)
            db_item = pure_item._to_db()
            self.assertIsInstance(db_item, getattr(pure_item.backend, core_cls.__name__))

    def test_item_io(self):
        """Each item type gets written and retrieved."""
        for item_type in CORE_ITEM_TYPES + [Note]:
            core_item = item_type(driver=self.db_driver)
            core_item.save()
            new_item = item_type.load(core_item.ikid)
            # breakpoint()
            self.assertEqual(core_item, new_item)

        # PointerNote needs a ref to instantiate, so out of for loop
        core_pointer_note = PointerNote(new_item, driver=self.db_driver)

        self.assertEqual(len(core_pointer_note.mentions), 1)

        core_pointer_note.save()

        self.assertEqual(len(core_pointer_note.mentions), 1)
        # breakpoint()
        reloaded = PointerNote.load(core_pointer_note.ikid)

        self.assertEqual(len(core_pointer_note.mentions), 1)
        # breakpoint()
        self.assertEqual(core_pointer_note, reloaded)


class TestComparison(unittest.TestCase):
    def test_core_vs_db(self):
        core = Item()
        db = core._to_db()
        self.assertNotEqual(core, db)


class TestNote(unittest.TestCase):
    """Tests for Note class

    Summary of tests to implement:
    - a note doesn't accept any arg for initialization
    - several notes may be nested and str representation concatenates
    - loops forbidden for nested notes
    - notes behave as Items when it comes to ikid, save and load (see test_item_io above)
    - updating the content of a nested note updates the parent note's str
    - upon nested note deletetion, parent notes drop that entry, child notes not deleted by default
    """

    def setUp(self) -> None:
        self.n1, self.n2, self.n3 = Note(), Note(), Note()
        self.n1.add_content('a')
        self.n2.add_content('b')
        self.n1.add_content(self.n2)
        self.n2.add_content(self.n3)
        self.n3.add_content('c')
        
    def test_depth(self):
        self.assertEqual(self.n1.depth, 3)
        self.assertEqual(self.n2.depth, 2)
        self.assertEqual(self.n3.depth, 1)

        # a slightly more advanced structure
        master_note = Note()  # depth 4
        child_1 = Note()  # depth 2
        child_1_1 = Note()  # depth 1
        child_1_2 = Note()  # depth 1
        child_2 = Note()  # depth 3
        child_3 = Note()  # depth 2
        child_4 = Note()  # depth 1
        child_3.add_content(child_4)
        child_2.add_content(child_3)
        master_note.add_content(child_1)
        master_note.add_content(child_2)
        child_1.add_content(child_1_1)
        child_1.add_content(child_1_2)
        notes = [
            master_note,
            child_1,
            child_1_1,
            child_1_2,
            child_2,
            child_3,
            child_4
        ]
        expected = [4, 2, 1, 1, 3, 2, 1]
        for n, d in zip(notes, expected):
            self.assertEqual(n.depth, d)

    def test_no_arg(self):
        self.assertRaises(TypeError, Note, '3')

    def test_str_concat(self):
        self.assertEqual(str(self.n1), 'a b c')

    def test_forbid_loop(self):
        self.assertRaises(NestedNoteLoop, self.n3.add_content, self.n1)

    def test_str_update(self):
        self.n3.add_content('d')
        self.assertEqual(str(self.n1), 'a b c d')
        self.n3.content[-1] = 'dollar'
        self.assertEqual(str(self.n1), 'a b c dollar')

    def test_nested_note_deletion(self):
        del self.n2
        self.assertEqual(str(self.n3), 'c')
        self.assertEqual(len(self.n1.content), 1)


class TestPointerNote(unittest.TestCase):
    """Tests for Note class

    Summary of tests to implement:
    - doesn't accept adding content
    - reference Item can be inspected as usual
    - str representation shows ikid of reference
    - upon item deletion, PointerNote gets deleted
    """
    
    def setUp(self) -> None:
        self.defin = Definition(name='blabla', content='roaster')
        self.defin.save()
        self.note = PointerNote(self.defin)

    def test_no_add(self):
        self.assertRaises(AddContentToPointerNote, self.note.add_content, '4')

    def test_inspect_ref(self):
        definition = next(iter(self.note.mentions))
        self.assertEqual(str(definition.content), 'roaster')

    def test_str_repr(self):
        self.assertIn(str(self.defin.ikid), str(self.note))

    def test_item_deletion(self):
        del self.defin
        self.assertTrue(not self.note.exists_in_db)
        self.assertEqual(self.note.mentions, set())
        self.assertRaises(DeadPointerNoteSave, self.note.save)


if __name__ == '__main__':
    unittest.main()
