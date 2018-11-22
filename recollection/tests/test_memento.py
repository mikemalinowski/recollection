from recollection.tests.classes import (
    EmptyTestClass,
    SetterTestClass,
    EventExceptingClass,
    EventCalledException,
)

import recollection
import unittest


# ------------------------------------------------------------------------------
class TestMemento(unittest.TestCase):
    """
    This suite of tests aims to give full coverage over memento.core by
    testing all the functionality within the object.
    """

    # --------------------------------------------------------------------------
    def test_can_instance_memento(self):
        """
        Ensures the memento object can be instanced
        :return:
        """
        test_class = EmptyTestClass()
        recollection.Memento(test_class)

    # --------------------------------------------------------------------------
    def test_can_store(self):
        """
        Ensures that we can store data, and that data is held in
        the memento object

        :return:
        """
        # -- Create a class and define a property
        test_class = EmptyTestClass()
        test_class.foo = 1

        # -- Create the memento object
        stack = recollection.Memento(test_class)
        stack.register('foo')

        # -- Set the value and store the result
        test_class.foo = 2
        stack.store()

        # -- Check that we stored 2
        self.assertEqual(
            2,
            stack._states[0]['foo'],
        )

    # --------------------------------------------------------------------------
    def test_can_restore(self):
        """
        Ensures that we can restore data from a memento state

        :return:
        """
        # -- Create a class and define a property
        test_class = EmptyTestClass()
        test_class.foo = 1

        # -- Create the memento object
        stack = recollection.Memento(test_class)
        stack.register('foo')

        # -- Store the current state
        stack.store()

        # -- Set the value and store the result
        test_class.foo = 2

        # -- Restore the last state
        stack.restore()

        # -- Check that we stored 2
        self.assertEqual(
            1,
            test_class.foo,
        )

    # --------------------------------------------------------------------------
    def test_can_restore_historically(self):
        """
        Ensures we can rollback to an older version of data

        :return:
        """
        # -- Create a class and define a property
        test_class = EmptyTestClass()
        test_class.foo = 1

        # -- Create the memento object
        stack = recollection.Memento(test_class)
        stack.register('foo')

        for i in range(11):
            test_class.foo = i

            # -- Store the current state
            stack.store()

        # -- Test that the latest value is indeed 10
        self.assertEqual(
            10,
            test_class.foo
        )

        # -- Restore 5 versions back
        stack.restore(index=5)

        self.assertEqual(
            5,
            test_class.foo,
        )

    # --------------------------------------------------------------------------
    def test_lock_step(self):
        """
        Ensures that the lock-step mechanism is working correctly

        :return:
        """
        # -- Create a class and define a property
        test_class_a = EmptyTestClass()
        test_class_b = EmptyTestClass()
        test_class_a.foo = 1
        test_class_b.foo = 1

        # -- Create the memento object
        stack_a = recollection.Memento(test_class_a)
        stack_b = recollection.Memento(test_class_b)

        stack_a.register('foo')
        stack_b.register('foo')

        # -- Group the stacks
        stack_a.group(stack_b)

        for i in range(11):
            test_class_a.foo = i
            test_class_b.foo = i

            # -- Store once
            stack_a.store()

        # -- Rollback
        stack_a.restore(5)

        self.assertEqual(
            5,
            test_class_a.foo,
        )

        self.assertEqual(
            5,
            test_class_b.foo,
        )

    # --------------------------------------------------------------------------
    def test_adding_to_group_multiple_times(self):
        """
        Groups allow lock-stepping. This test ensures all the logic which
        ensures instances do not exist multiple times in a group

        :return:
        """
        # -- Create a class and define a property
        test_class_a = EmptyTestClass()
        test_class_b = EmptyTestClass()
        test_class_c = EmptyTestClass()

        # -- Create the memento object
        stack_a = recollection.Memento(test_class_a)
        stack_b = recollection.Memento(test_class_b)
        stack_c = recollection.Memento(test_class_c)

        # -- Group the stacks
        stack_a.group(stack_b)
        stack_a.group(stack_b)
        stack_a.group(stack_b)
        stack_a.group(stack_b)

        stack_b.group(stack_a)
        stack_b.group(stack_a)
        stack_b.group(stack_a)
        stack_b.group(stack_a)

        # -- Side test to check when group a is in a group already
        # -- and group c is not
        stack_a.group(stack_c)

        self.assertEqual(
            3,
            len(stack_a.sync_group())
        )

    # --------------------------------------------------------------------------
    def test_can_unregister(self):
        """
        Checks that when we unregister something, we no longer look for
        it or utilise it

        :return:
        """
        # -- Create a class and define a property
        test_class = EmptyTestClass()
        test_class.foo = 1

        # -- Create the memento object
        stack = recollection.Memento(test_class)
        stack.register('foo')

        # -- Set the value and store the result
        test_class.foo = 2
        stack.store()

        # -- Check that we stored 2
        self.assertEqual(
            2,
            stack._states[0]['foo'],
        )

        # -- Now unregister foo
        stack.unregister('foo')
        stack.store()

        self.assertNotIn(
            'foo',
            stack._states[0],
        )

    # --------------------------------------------------------------------------
    def test_setter_methods(self):
        """
        Checks to see that the explicit declaration of setters is working

        :return:
        """
        # -- Create our test class
        test_class = SetterTestClass()

        # -- Instance a stack
        stack = recollection.Memento(test_class)

        # -- Register an attribute using getters and setters
        stack.register(
            label='target',
            getter=test_class.getTarget,
            setter=test_class.setTarget,
        )

        # -- Set the target
        test_class.setTarget(42)
        stack.store()

        # -- Set the target again
        self.assertEqual(
            42,
            stack._states[0]['target'],
        )

    # --------------------------------------------------------------------------
    def test_object_copying(self):
        """
        When we store state we have the option of specifically copying objects
        or just referencing them.

        In most cases we want to copy, as state is dependent on it - but not
        always. Therefore this is optional and this tests specifically that
        we get new objects when copying.

        :return:
        """
        # -- Create an object
        generic_object = EmptyTestClass()

        # -- Create our test class
        test_class = SetterTestClass()

        # -- Instance the memento stack
        stack = recollection.Memento(test_class)

        # -- Register an object to store
        stack.register(
            label='target',
            getter=test_class.getTarget,
            setter=test_class.setTarget,
            copy_value=True
        )

        # -- Set the attribute to our object - which should
        # -- create a copy each time
        for i in range(11):
            test_class.setTarget(generic_object)
            stack.store()

        # -- Fail if they are the same
        self.assertNotEqual(
            generic_object,
            stack._states[0]['target'],
        )

    # --------------------------------------------------------------------------
    def test_object_not_copying(self):
        """
        When we store state we have the option of specifically copying objects
        or just referencing them.

        In most cases we want to copy, as state is dependent on it - but not
        always. Therefore this is optional and this tests specifically that
        we get the same objects when not copying.

        :return:
        """
        # -- Create the object which we will ultimately test against
        generic_object = EmptyTestClass()

        # -- Create our test class
        test_class = SetterTestClass()

        # -- Instance a memento stack
        stack = recollection.Memento(test_class)

        # -- Regiser the attribute
        stack.register(
            label='target',
            getter=test_class.getTarget,
            setter=test_class.setTarget,
            copy_value=False
        )

        # -- Call the store a few times - this time we're expecting
        # -- the object to be referenced
        for i in range(11):
            test_class.setTarget(generic_object)
            stack.store()

        # -- Fail if the objects are not the same
        self.assertEqual(
            generic_object,
            stack._states[0]['target'],
        )

    # --------------------------------------------------------------------------
    def test_simple_list_registration(self):
        """
        Memento allows us to specify a list of attributes by string name, this
        test ensures that mechanism works.

        :return:
        """
        # -- Define our list of properties
        properties = [
            'a',
            'b',
            'c',
        ]

        # -- Create a class and define a property
        test_class = EmptyTestClass()

        # -- Set values on each property
        for prop in properties:
            setattr(
                test_class,
                prop,
                1,
            )

        # -- Create the memento object
        stack = recollection.Memento(test_class)
        stack.register(properties)
        stack.store()

        # -- Ensure that each property is in the stack
        for prop in properties:
            self.assertIn(
                prop,
                stack._states[0],
            )

    # --------------------------------------------------------------------------
    def test_complex_list_registration(self):
        """
        As well as giving a list of strings we can also give a list containing
        lists of index-ordered parameters. This ensures that mechanism works
        as expected.

        :return:
        """
        # -- Create a class and define a property
        test_class = SetterTestClass()

        # -- Create the memento object
        stack = recollection.Memento(test_class)

        # -- Register the two getters and setters in one go
        stack.register(
            [
                [
                    test_class.getTarget,
                    test_class.setTarget,
                    'target',
                    True,
                ],
                [
                    test_class.getDistance,
                    test_class.setDistance,
                    'distance',
                    True,
                ],
            ]
        )
        stack.store()

        # -- Ensure the target was stored
        self.assertIn(
            'target',
            stack._states[0],
        )

        # -- Ensure the distance was stored
        self.assertIn(
            'distance',
            stack._states[0],
        )

    # --------------------------------------------------------------------------
    def test_assert_on_label_duplication(self):
        """
        This is a negative test to ensure we get an assertion when we
        try to register the same label twice.

        :return:
        """
        # -- Create a class and define a property
        test_class = EmptyTestClass()
        test_class.foo = 1

        # -- Create the memento object
        stack = recollection.Memento(test_class)

        # -- Register a label
        stack.register('foo')

        # -- Try to register the same label again
        try:
            stack.register('foo')

            self.assertTrue(
                False,
                msg='Did not fail on registering the same label twice',
            )

        except recollection.RegistrationError:
            pass

    # --------------------------------------------------------------------------
    def test_out_of_scope_assert(self):
        """
        This will test teh assertion when our target object we're looking
        at is garbage collected.

        :return:
        """
        # -- Create a class and define a property
        test_class = EmptyTestClass()
        test_class.foo = 1

        # -- Create the memento object
        stack = recollection.Memento(test_class)
        stack.register('foo')

        # -- Delete the object
        # noinspection PyRedundantParentheses
        del(test_class)

        # -- Attempt to store using the stack
        try:
            stack.store()

            self.assertTrue(
                False,
                msg='Did not fail on storing a deleted object reference',
            )

        except recollection.StorageError:
            pass

    # --------------------------------------------------------------------------
    def test_type_error_on_invalid_label(self):
        """
        This ensures that we get a type error if giving an invalid
        label type.

        :return:
        """
        # -- Create a class and define a property
        test_class = EmptyTestClass()
        test_class.foo = 1

        # -- Create the memento object
        stack = recollection.Memento(test_class)

        try:
            # noinspection PyTypeChecker
            stack.register(
                label=123,
                getter='foo',
            )
            self.assertTrue(
                False,
                msg='Did not fail when giving an invalid label type',
            )

        except TypeError:
            pass

    # --------------------------------------------------------------------------
    def test_max_states_are_popped(self):
        """
        We can define the max states to store on a stack. This checks that
        the behaviour when exceeding that value is to have the stack constantly
        popping.

        :return:
        """
        # -- Create a class and define a property
        test_class = EmptyTestClass()
        test_class.foo = 1

        # -- Create the memento object
        stack = recollection.Memento(test_class, max_states=5)
        stack.register('foo')

        for i in range(100):
            test_class.foo = i
            stack.store()

        self.assertEqual(
            stack.count(),
            5,
        )

    # --------------------------------------------------------------------------
    def test_assert_registering_invalid_serialiser(self):
        """
        This will ensure that we get teh correct assert when giving a
        serialiser which does not base off our SerialiserBase

        :return:
        """
        # -- Create a class and define a property
        test_class = EmptyTestClass()
        test_class.foo = 1

        # -- Create the memento object
        stack = recollection.Memento(test_class, max_states=5)
        stack.register('foo')

        try:
            stack.register_serialiser(
                serialiser=EmptyTestClass(),
                identifier='',
            )

            self.assertTrue(
                False,
                msg='Did not fail when registering invalid serialiser',
            )

        except TypeError:
            pass

    # --------------------------------------------------------------------------
    def test_serialising_with_no_serialiser(self):
        """
        Tests that we get an assert when trying to serialise with no
        serialiser registered.

        :return:
        """
        # -- Create a class and define a property
        test_class = EmptyTestClass()

        # -- Create the memento object
        stack = recollection.Memento(test_class, max_states=5)

        # noinspection PyBroadException
        try:
            stack.serialise()

            self.assertTrue(
                False,
                msg='Did not fail when serialising with no serialiser',
            )

        except Exception:
            pass

    # --------------------------------------------------------------------------
    def test_deserialising_with_no_serialiser(self):
        """
        Tests that we get an assert when trying to deserialise with no
        serialiser registered.

        :return:
        """
        # -- Create a class and define a property
        test_class = EmptyTestClass()

        # -- Create the memento object
        stack = recollection.Memento(test_class, max_states=5)

        # noinspection PyBroadException
        try:
            stack.deserialise()

            self.assertTrue(
                False,
                msg='Did not fail when serialising with no serialiser',
            )

        except Exception:
            pass

    # --------------------------------------------------------------------------
    def test_registration_event_triggering(self):
        """
        Tests that we get an assert when trying to deserialise with no
        serialiser registered.

        :return:
        """
        # -- Create a class and define a property
        test_class = EventExceptingClass()
        test_class.foo = 0

        # -- Create the memento object
        stack = recollection.Memento(test_class, max_states=5)

        # -- Hook up the event
        stack.registered.connect(test_class.raise_exception)

        # noinspection PyBroadException
        try:
            stack.register('foo')

            self.assertTrue(
                False,
                msg='Event not triggered during exception',
            )

        except EventCalledException:
            pass

    # --------------------------------------------------------------------------
    def test_unregister_event_triggering(self):
        """
        Tests that we get an assert when trying to deserialise with no
        serialiser registered.

        :return:
        """
        # -- Create a class and define a property
        test_class = EventExceptingClass()
        test_class.foo = 0

        # -- Create the memento object
        stack = recollection.Memento(test_class, max_states=5)

        # -- Hook up the event
        stack.unregistered.connect(test_class.raise_exception)
        stack.register('foo')

        # noinspection PyBroadException
        try:
            stack.unregister('foo')

            self.assertTrue(
                False,
                msg='Event not triggered during exception',
            )

        except EventCalledException:
            pass

    # --------------------------------------------------------------------------
    def test_store_event_triggering(self):
        """
        Tests that we get an assert when trying to deserialise with no
        serialiser registered.

        :return:
        """
        # -- Create a class and define a property
        test_class = EventExceptingClass()
        test_class.foo = 0

        # -- Create the memento object
        stack = recollection.Memento(test_class, max_states=5)
        stack.register('foo')

        # -- Hook up the event
        stack.stored.connect(test_class.raise_exception)

        # noinspection PyBroadException
        try:
            stack.store()

            self.assertTrue(
                False,
                msg='Event not triggered during exception',
            )

        except EventCalledException:
            pass

    # --------------------------------------------------------------------------
    def test_restore_event_triggering(self):
        """
        Tests that we get an assert when trying to deserialise with no
        serialiser registered.

        :return:
        """
        # -- Create a class and define a property
        test_class = EventExceptingClass()
        test_class.foo = 0

        # -- Create the memento object
        stack = recollection.Memento(test_class, max_states=5)
        stack.register('foo')
        stack.store()
        stack.store()

        # -- Hook up the event
        stack.restored.connect(test_class.raise_exception)

        # noinspection PyBroadException
        try:
            stack.restore()

            self.assertTrue(
                False,
                msg='Event not triggered during exception',
            )

        except EventCalledException:
            pass

    # --------------------------------------------------------------------------
    def test_unregister_event_triggering(self):
        """
        Tests that we get an assert when trying to deserialise with no
        serialiser registered.

        :return:
        """
        # -- Create a class and define a property
        test_class = EventExceptingClass()
        test_class.foo = 0

        # -- Create the memento object
        stack = recollection.Memento(test_class, max_states=5)

        # -- Hook up the event
        stack.registered.connect(test_class.raise_exception)
        stack.registered.disconnect(test_class.raise_exception)

        # noinspection PyBroadException
        try:
            stack.register('foo')

        except EventCalledException:
            self.assertTrue(
                False,
                msg='Called event after it was disconnected',
            )
