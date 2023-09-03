class TermStatus:
    """Has this term been deleted from the database?"""

    DELETED = 0
    NOT_DELETED = 1


class TestDirection:
    """When running a practice/test session, should you practice translating words
    from language 1 to language 2, or practice translating words from language 2
    to language 1?
    """

    _1to2 = 1
    _2to1 = 2


class TestMethod:
    """When running a practice/test session, should the words to be practiced be
    picked at random, or should the user select the words from a list?"""

    Random = 1
    List = 2
