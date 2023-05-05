from typing import Any
from indiek.mockdb import items as default_driver


class Item:
    def __init__(self, name: str = '', content: Any = '', driver: Any = default_driver):
        self.name = name
        self.content = content
        self.backend = driver

    def to_db(self):
        return self.backend.Item.from_core(self)
    
    @staticmethod
    def from_db(db_item: default_driver.Item):
        return Item(name=db_item['name'], content=db_item['content'])
    
    def to_dict(self):
        return {'name': self.name, 'content': self.content}