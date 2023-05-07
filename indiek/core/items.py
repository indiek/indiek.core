from __future__ import annotations
from typing import Any, Optional
from indiek.mockdb import items as default_driver


class Item:
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

    BACKEND_CLS = default_driver.Item
    """Class from backend items module corresponding to present core API class."""

    def __init__(self, *, name: str = '', content: Any = '', _ikid: Optional[int] = None, driver: Any = default_driver):
        self._ikid = _ikid
        self.name = name
        self.content = content
        self.backend = driver

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
        return f"Core Item with ID {self._ikid} and name {self.name}"

    def __eq__(self, other) -> bool:
        return (self._ikid == other._ikid
                and self.name == other.name
                and self.content == other.content
                and type(other) == type(self))

    def _to_db(self) -> default_driver.Item:
        """Export core Item to DB Item instance."""
        return self.BACKEND_CLS.from_core(self)
    
    def save(self) -> int:
        """Save to backend.
        
        This method delegates the save operation to the backend.
        If _ikid is None in self, it will get set to new value
        generated by backend.
        """
        self._ikid = self._to_db().save()
        return self._ikid

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
        return {'name': self.name, 'content': self.content, '_ikid': self._ikid}
    

class Definition(Item):
    BACKEND_CLS = default_driver.Definition
    pass


class Theorem(Item):
    BACKEND_CLS = default_driver.Theorem
    pass


class Proof(Item):
    BACKEND_CLS = default_driver.Proof
    pass
