import unittest


class TestBuilder(unittest.TestCase):

    def test_basic(self):

        from ambry import get_library
        l = get_library()


if __name__ == '__main__':
    unittest.main()
