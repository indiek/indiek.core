from __future__ import annotations
from typing import Any, Optional, Self
from indiek.mockdb import items as default_driver


IKID = 'iKiD'

class NestedNoteLoop(Exception): pass
class AddContentToPointerNote(Exception): pass
class DeadPointerNoteSave(Exception): pass

class Nucleus:
    """Nuclear item."""

    def __init__(self, _ikid: Optional[int] = None, driver: Any = default_driver):
        self._ikid = _ikid
        self.backend = driver

    @property 
    def ikid(self):
        return self._ikid

    @property
    def exists_in_db(self):
        """Check whether item was ever saved. Doesn't query the DB at all. """
        return self._ikid is not None
    
    def save(self) -> int:
        """Save to backend.
        
        This method delegates the save operation to the backend.
        If _ikid is None in self, it will get set to new value
        generated by backend.
        """
        self._ikid = self._to_db().save()
        return self._ikid
    
    def delete(self) -> None:
        self._to_db().delete()
        self._ikid = None


def str2note(string_or_note: str | Note) -> Note:
    if isinstance(string_or_note, Note):
        return string_or_note
    note = Note()
    note.add_content(string_or_note)
    return note


class Item(Nucleus):
    """Generic Item in IndieK core.

    A note on unique id _ikid. The assignments and checks for uniqueness are 
    usually handled by the backend driver. Therefore, usual flow for new Item
    creation is the following:
    1. Item instance is created in indiek-core without _ikid attr set to None.
    2. When the `save` method is called, the backend generates a unique _ikid and
       it gets saved as attr to current indiek-core Item instance.
    3. If `save` is called while `_ikid` is already set, then the backend will 
       take that value as is, potentially overriding any pre-existing items in DB. 

    Attributes:
        _ikid (int): a unique identifier.
        name (str): a human-friendly short identifier.
        content (str): some string with data the Item is meant to hold or reference.
        backend (Any): backend port for I/O operations with DB
    """

    _attr_defs = ['_ikid', 'content', 'name']
    
    def __init__(self, *, name: str | Note = '', content: str | Note = '', _ikid: Optional[int] = None, driver: Any = default_driver):
        super().__init__(_ikid, driver)
        self.name = str2note(name)
        self.content = str2note(content)

    def __repr__(self):
        _ikid = self._ikid
        name = self.name
        content_hash = hash(self.content)
        driver = self.backend
        return f"module: {__name__}; class:{self.__class__.__name__}; {_ikid=}; {name=}; {content_hash=}; {driver=}"
    
    def __hash__(self):
        # TODO: not sure this __hash__ method follows best practices
        return hash((self._ikid, self.name, self.content, self.__class__.__name__))

    def __str__(self):
        return f"Core {self.__class__.__name__} with ID {self.ikid} and name {self.name}"

    def __eq__(self, other) -> bool:
        return (self._ikid == other._ikid
                and self.name == other.name
                and self.content == other.content
                and type(other) == type(self))

    def _to_db(self) -> default_driver.Item:
        """Export core Item to DB Item instance."""
        as_dict = self.to_dict()
        try:
            return self.BACKEND_CLS(**as_dict)
        except AttributeError:
            return self.backend.Item(**as_dict)

    @classmethod
    def load(cls, ikid) -> Item:
        """Create Core Item from backend using ikid."""
        return cls.from_db(cls.BACKEND_CLS.load(ikid))

    @classmethod
    def from_db(cls, db_item: default_driver.Item) -> Item:
        """Instantiate core Item off of backend Item."""
        return cls(**db_item.to_dict())
    
    def to_dict(self):
        """Export core Item content to dict."""
        return {a: getattr(self, a) for a in self._attr_defs}
    

# TODO: automate class creation below
class Definition(Item):
    BACKEND_CLS = default_driver.Definition
class Theorem(Item):
    BACKEND_CLS = default_driver.Theorem
class Proof(Item):
    BACKEND_CLS = default_driver.Proof
class Question(Item):
    BACKEND_CLS = default_driver.Question
CORE_ITEM_TYPES = [Definition, Theorem, Proof, Question]

        
class Note(Nucleus):
    """Generic note.

    A note contains a sequence of entries, each entry
    being either a string literal or a Note itself.

    Notes are meant to act as Wikis in IndieK.
    """

    def __init__(self, *, _ikid: Optional[int] = None, driver: Any = default_driver):
        super().__init__(_ikid, driver)
        self.content = []
        self.mentions = set()
        # TODO: add a content_type attr?
    
    def add_content(self, content: Self | str) -> None:
        if not isinstance(content, str):
            self.update_mentions(content)
        self.content.append(content)

    def __hash__(self):
        return hash(tuple(map(hash, self.content)))

    def __str__(self) -> str:
        """Resolves content into str.

        Returns:
            str: string representation.

        Raises:
            RecursionError: if loops are present (a contains b contains a)
        """
        # TODO: store the start-end chars positions of each content entry
        return ' '.join(map(str, self.content))

    def update_mentions(self, content):
        self.mentions.update(content.mentions)


class PointerNote(Note):
    """Note designed to solely refer to an IndieK item or to another note.

    This kind of notes doesn't allow for content addition.

    Args:
        Note (_type_): _description_
    """

    def __init__(self, reference: Nucleus):
        assert reference.exists_in_db, "Cannot reference unsaved item or note."
        super().__init__()
        self.content = [IKID + str(reference.ikid)]
        self.mentions = {reference}

    def add_content(self) -> None:
        raise NotImplementedError(f"{self.__class__} doesn't allow content addition.")
    
