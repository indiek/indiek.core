"""Search API for IndieK"""
from typing import List
from indiek.core.items import Item
from indiek.mockdb.items import Item as DBItem


def list_all_items() -> List[Item]:
    """Wrapper around backend DBItem.list_all"""
    return [Item.from_db(dbi) for dbi in DBItem.list_all()]