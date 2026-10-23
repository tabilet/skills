import unittest
from slug import slugify


class SlugTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify('Hello, World!'), 'hello-world')
        self.assertEqual(slugify('  A   b  '), 'a-b')
