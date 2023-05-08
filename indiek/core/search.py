"""Search logic for the core IndieK API."""
import re
from typing import List, Union, Sequence, Dict
from indiek.core.items import Item, Definition, Theorem, Proof
from indiek.mockdb.items import (Item as DBItem,
                                 Definition as DBDefinition,
                                 Theorem as DBTheorem,
                                 Proof as DBProof)


BackendItem = Union[DBItem, DBDefinition, DBTheorem, DBProof]
ITEM_TYPES = Definition, Theorem, Proof


def build_search_query(string: str) -> re.Pattern:
    base_str = '('
    base_str += '|'.join(string.split())
    base_str += ')'
    return re.compile(base_str, flags=re.IGNORECASE)


def search_and_cast(query: re.Pattern, core_cls: Item) -> List[Item]:
    """Trigger query on backend, fetch and cast to core objects.

    Args:
        query (re.Pattern): compiled regex object.
        core_cls (Item): item class in core API to use for filtering.

    Returns:
        List[Item]: list of core items
    """
    db_cls = core_cls.BACKEND_CLS
    return [core_cls.from_db(dbi) for dbi in db_cls.str_filter(query)]


def fetch_and_cast(core_cls: Item) -> List[Item]:
    """Fetch all results from backend and cast to core objects.

    Args:
        core_cls (Item): item class in core API to use for filtering.

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
            two types (more precisely for their corresponding types in backend typing). Defaults to (Definition,
            Theorem, Proof) in which case all types are queried. Note that another way to query all items without filtering 
            on types is to set item_types to an empty container.

    Returns:
        Dict[Item, List[Item]]: segmented results. Returned dict has keys identical to item_types entries, with the
            exception of the case where item_types was an empty container; for that latter case, returned dict has
            the default keys (Definition, Theorem, Proof).
    """
    if len(item_types) == 0:
        item_types = ITEM_TYPES
    return {item_type: fetch_and_cast(item_type) for item_type in item_types}


def filter_str(search_str: str, item_types: Sequence[Item] = (Definition, Theorem, Proof)) -> Dict[Item, List[Item]]:
    """Search items from specified type which match search string.

    Backend items of type compatible with item_types are searched, retrieved and cast to Core type.
    The search_str is split on white spaces and regex are built and 'and-ed'. The resulting regex is
    applied on item name and content.
    
    Args:
        search_str (str): search string.
        item_types (Sequence[Item]): list-like of core item types (similar to `list_all_items` arg of same name).
    
    Returns:
        Dict[Item, List[Item]]: segmented results, only containing matching items.
    """
    if len(item_types) == 0:
        item_types = ITEM_TYPES
    query = build_search_query(search_str)
    return {item_type: search_and_cast(query, item_type) for item_type in item_types}
