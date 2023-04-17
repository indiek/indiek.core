Library that stores the core logic for the IndieK software suite.

============
Installation
============

To install from PyPI: ``pip install indiek-core``

To develop, use the [dev] dependency specification, e.g.:
``pip install indiek-core[dev]``

Or from the cloned repo's top-level in editable mode:
``pip install -e .[dev]``

==========
Quickstart
==========

..  code-block:: python
    
    from indiek.core.items import Item
    from indiek.mockdb.items import Item as DBitem
    
    item1 = Item(name='item1', content='example item 1').to_db()
    item1.save()
    
    item2 = DBitem.load(item1.ikid)
    print(item2.name, item2.content)

=====
Tests
=====
To run the full test suite, type the following from the top level of this repo:
``pytest``
