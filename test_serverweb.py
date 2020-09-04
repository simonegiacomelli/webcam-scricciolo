from unittest import TestCase

from serverweb import Cached


class TestCached(TestCase):

    def test_should_return_value_from_provider(self):
        target = Cached(lambda: 'foo')
        self.assertEqual('foo', target())

    def test_should_call_inner_only_once(self):
        self.counter = 0

        def provider():
            self.counter += 1
            return self.counter

        target = Cached(provider)

        self.assertEqual(1, target())
        self.assertEqual(1, target())
