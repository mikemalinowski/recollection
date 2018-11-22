from recollection.tests.classes import SetterTestClass

import os
import recollection
import unittest


# ------------------------------------------------------------------------------
class TestClass(object):
    # noinspection PyUnusedLocal
    def __init__(self):
        foo = 1
        bar = ''


# ------------------------------------------------------------------------------
class TestSerialiserAppData(unittest.TestCase):

    # --------------------------------------------------------------------------
    def test_serialise(self):
        """
        Checks to see that our serialisation kicks in and we have
        a persistent data artifact

        :return:
        """
        # -- Create out test stack
        test_class, stack = self._memento_test_data()

        # -- Define the data location
        identifier = 'memento/tests/json_appdata'
        data_path = recollection.JsonAppSerialiser.locator(identifier)

        # -- Remove any old data
        if os.path.exists(data_path):
            os.remove(data_path)

        # -- Register our serialiser
        stack.register_serialiser(
            serialiser=recollection.JsonAppSerialiser,
            identifier='memento/tests/json_appdata',
        )

        # -- Set some properties on the class
        test_class.setTarget(10)
        test_class.setDistance(20)

        # -- Store the data and serialise
        stack.store()
        stack.serialise()

        # -- Ensure the data exists
        self.assertTrue(
            os.path.exists(data_path)
        )

    # --------------------------------------------------------------------------
    def test_serialise_on_store(self):
        """
        Checks to see that our serialisation kicks in and we have
        a persistent data artifact when calling the shortcut of
        serelialise=True on the store method

        :return:
        """
        # -- Create out test stack
        test_class, stack = self._memento_test_data()

        # -- Define the data location
        identifier = 'memento/tests/json_appdata'
        data_path = recollection.JsonAppSerialiser.locator(identifier)

        # -- Remove any old data
        if os.path.exists(data_path):
            os.remove(data_path)

        # -- Register our serialiser
        stack.register_serialiser(
            serialiser=recollection.JsonAppSerialiser,
            identifier='memento/tests/json_appdata',
        )

        # -- Set some properties on the class
        test_class.setTarget(10)
        test_class.setDistance(20)

        # -- Store the data and serialise
        stack.store(serialise=True)

        # -- Ensure the data exists
        self.assertTrue(
            os.path.exists(data_path)
        )

    # --------------------------------------------------------------------------
    def test_deserialise(self):
        """
        Checks to see that our serialisation kicks in and we have
        a persistent data artifact when calling the shortcut of
        serelialise=True on the store method

        :return:
        """
        # -- Create out test stack
        test_class, stack = self._memento_test_data()

        # -- Define the data location
        identifier = 'memento/tests/json_appdata'
        data_path = recollection.JsonAppSerialiser.locator(identifier)

        # -- Remove any old data
        if os.path.exists(data_path):
            os.remove(data_path)

        # -- Register our serialiser
        stack.register_serialiser(
            serialiser=recollection.JsonAppSerialiser,
            identifier='memento/tests/json_appdata',
        )

        # -- Set some properties on the class
        test_class.setTarget(10)
        test_class.setDistance(20)

        # -- Store the data and serialise
        stack.store(serialise=True)

        # -- Create out test stack
        new_test_class, new_stack = self._memento_test_data()

        # -- Register our serialiser
        new_stack.register_serialiser(
            serialiser=recollection.JsonAppSerialiser,
            identifier='memento/tests/json_appdata',
        )
        new_stack.deserialise()

        # -- Ensure the data exists
        self.assertEqual(
            10,
            new_test_class.getTarget(),
        )

        self.assertEqual(
            20,
            test_class.getDistance(),
        )

    # --------------------------------------------------------------------------
    @classmethod
    def _memento_test_data(cls):

        test_class = SetterTestClass()

        stack = recollection.Memento(test_class)
        stack.register(
            label='target',
            getter=test_class.getTarget,
            setter=test_class.setTarget,
        )

        stack.register(
            label='distance',
            getter=test_class.getDistance,
            setter=test_class.setDistance,
        )

        return test_class, stack
