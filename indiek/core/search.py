"""Search logic for the core IndieK API."""
from typing import List, Union, Optional, Sequence, Dict
from indiek.core.items import Item, Definition, Theorem, Proof
from indiek.mockdb.items import (Item as DBItem,
                                 Definition as DBDefinition,
                                 Theorem as DBTheorem,
                                 Proof as DBProof)


BackendItem = Union[DBItem, DBDefinition, DBTheorem, DBProof]


def fetch_and_cast(core_cls: Item) -> List[Item]:
    """Fetch all results from backend and cast to core objects.

    Args:
        core_cls (Item): item class in core API

    Returns:
        List[Item]: list of core items
    """
    db_cls = core_cls.BACKEND_CLS
    return [core_cls.from_db(dbi) for dbi in db_cls.list_all()]



def list_all_items(item_types: Sequence[Item] = (Definition, Theorem, Proof)) -> Dict[Item, List[Item]]:
    """Fetch all items with optional type filter.

    Args:
        item_types (Sequence[Item], optional): list-like of core item types to use for segmented
            search. For example, if item_types is [Proof, Theorem], then backend will be queried only for these
            two types (more precisely for their corresponding types in backend typing). Defaults to None in which
            case all types are queried. Note that the way to query all items without filtering on types is to set 
            item_types to None (as opposed to setting it to [Item] which would throw a KeyError).

    Returns:
        Dict[Item, List[Item]]: segmented results. If item_types arg was None, then Item is the only key in the 
            dict. Otherwise, returned dict has keys identical to item_types entries.

    Raises:
        KeyError: When item_types contains entries that are not keys of CORE_TO_DB_MAPPING.
    """
    return {item_type: fetch_and_cast(item_type) for item_type in item_types}
