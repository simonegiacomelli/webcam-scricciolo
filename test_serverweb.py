from unittest import TestCase
from unittest.mock import Mock

from serverweb import RefreshableCache, Dispatch, MethodNotRegistered, WebApi


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

    def test_dispatch__should_not_call_late_added_method_AND_raise_exception(self):
        self.called = False

        def call_API_late():
            self.called = True

        class Endpoint:
            pass

        target = Dispatch().register(Endpoint, 'API_')
        instance = Endpoint()
        setattr(instance, 'API_late', lambda: call_API_late())

        self.assertRaises(MethodNotRegistered, lambda: target.dispatch(instance, 'late'))
        self.assertFalse(self.called)

    def test_dispatch__with_paramters(self):
        class Endpoint:
            def __init__(self):
                self.name = None

            def API_set_name(self, name):
                self.name = name

        target = Dispatch().register(Endpoint, 'API_')
        instance = Endpoint()

        target.dispatch(instance, 'set_name', {'name': 'john'})
        self.assertEqual('john', instance.name)


class TestWebApi(TestCase):

    def test_api_days(self):
        metadata = Mock()
        metadata.days.names = ['day1', 'day2']
        target = WebApi(metadata)
        self.assertEqual(({'name': 'day1'}, {'name': 'day2'}), target.API_days())
