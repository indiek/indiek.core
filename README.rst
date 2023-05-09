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
    
    from indiek.core.items import Definition
    
    item1 = Definition(name='def1', content='example def 1')
    item1_id = item1.save()

    reloaded = Definition.load(item1_id)
    assert item1 == reloaded

=====
Tests
=====
To run the full test suite, type the following from the top level of this repo:
``pytest``
