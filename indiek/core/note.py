from typing import Self
from indiek.core.items import Item


IKID = 'iKiD'


class Note:
    """Generic note.

    A note contains a sequence of entries, each entry
    being either a string literal or a Note itself.

    Notes are meant to act as Wikis in IndieK.
    """

    def __init__(self):
        self.content = []
        self.mentions = set()
        # TODO: add a content_type attr?
    
    def add_content(self, content: Self | str) -> None:
        if not isinstance(content, str):
            self.update_mentions(content)
        self.content.append(content)

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

    def __init__(self, reference: Note | Item):
        assert reference.exists_in_db, "Cannot reference unsaved item or note."
        super().__init__()
        self.content = [IKID + str(reference.ikid)]
        self.mentions = {reference}

    def add_content(self) -> None:
        raise NotImplementedError(f"{self.__class__} doesn't allow content addition.")