from indiek import *


def pretty_test(test_num):
    """
    parameterized decorator for tests
    :param test_num: test number (positive integer)
    :return: a standard decorator
    """
    def _pretty_test(test_fun):
        """
        decorator for test functions
        :param test_fun: test function to decorate
        :return:
        """
        def __pretty_test():
            """
            wrapper for pretty-printing tests
            :return: test_result
            """
            pretty_string_1 = '\n>>>'
            pretty_string_2 = '<<<'

            print('{0} entering test {1} ...\n'.format(pretty_string_1, test_num))

            test_result = test_fun()

            print('{0} exiting test {1} with result **{2}**'.format(pretty_string_2,
                                                                    test_num, test_result))
            return test_result
        return __pretty_test
    return _pretty_test


@pretty_test(1)
def test_1():
    """
    tests that a ValueError is raised if wrong item creation mode is passed
    :return: boolean
    """
    try:
        i1 = Item('blablabla')
    except ValueError as err:
        print(err)
        return True
    else:
        return False


@pretty_test(2)
def test_2():
    """
    checks that an Item may be created with creation mode "interactiveConsole"
    :return:
    """
    try:
        i2 = Item('pythonConsole')
    except Exception as err:
        print(err)
        return False
    else:
        return True


if __name__ == '__main__':
    # import sys
    # sys.path.extend(['/home/adrian/Git/GitHub/IndieK/python_scripts'])

    # create item with unknown item creation mode
    #test_1()
    # create item with known item creation mode
    #test_2()

    db = DummyDB('adrian', max_items=10)
    workspace = Workspace(db)
