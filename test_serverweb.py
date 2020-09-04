from unittest import TestCase

from serverweb import RefreshableCache, Dispatch


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


class TestDispatch(TestCase):
    def test_register__should_register_only_prefix(self):
        class Endpoint:
            def no_register(self):
                pass

            def PREFIX_foo(self):
                pass

        target = Dispatch().register(Endpoint, 'PREFIX_')
        self.assertEqual(['foo'], list(target.registered.keys()))

    def test_simple_procedure_dispatch(self):
        class Endpoint:
            def __init__(self):
                self.called = False

            def API_pippo(self):
                self.called = True

        target = Dispatch().register(Endpoint, 'API_')
        instance = Endpoint()
        target.dispatch(instance, 'pippo')
        self.assertTrue(instance.called)
