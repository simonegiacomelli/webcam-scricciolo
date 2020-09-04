from unittest import TestCase

from serverweb import Cached


class TestCached(TestCase):

    def test_should_return_value_from_provider(self):
        target = Cached(lambda: 'foo')
        self.assertEqual('foo', target())

    def test_should_call_provider_only_once(self):
        self.counter = 0

        def provider():
            self.counter += 1
            return self.counter

        target = Cached(provider)

        self.assertEqual(1, target())
        self.assertEqual(1, target())

    def test_refresh__should_call_provider_again_and_return_same_value(self):
        self.counter = 0

        def provider():
            self.counter += 1
            return self.counter

        target = Cached(provider)
        target.refresh()
        self.assertEqual(2, self.counter)
        self.assertEqual(2, target())
