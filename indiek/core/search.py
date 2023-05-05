"""Search API for IndieK"""
from indiek.core.items import Item
from indiek.mockdb.items import Item as DBItem


def list_all_items():
    return [Item.from_db(dbi) for dbi in DBItem.list_all()]