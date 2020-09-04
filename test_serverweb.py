from unittest import TestCase

from serverweb import RefreshableCache


class TestRefreshableCache(TestCase):

    def setUp(self) -> None:
        self.counter = 0

    def inc_counter(self):
        self.counter += 1
        return self.counter

    def test_should_return_value_from_provider(self):
        target = RefreshableCache(lambda: 'foo')
        self.assertEqual('foo', target())

    def test_should_call_provider_only_once(self):
        target = RefreshableCache(self.inc_counter)

        self.assertEqual(1, target())
        self.assertEqual(1, target())

    def test_refresh__should_call_provider_again_and_return_same_value(self):
        target = RefreshableCache(self.inc_counter)
        target.refresh()
        self.assertEqual(2, self.counter)
        self.assertEqual(2, target())
