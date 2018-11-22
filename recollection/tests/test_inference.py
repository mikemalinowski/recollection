import recollection
import unittest


# ------------------------------------------------------------------------------
class SimpleTestClass(recollection.Inference):

    def __init__(self):
        super(SimpleTestClass, self).__init__()
        self._letter = 1
        self.number = 10
        self.memento.register('number')

    @recollection.infer.get('letter')
    def letter(self):
        return self._letter

    @ recollection.infer.store('letter')
    def set_letter(self, value):
        self._letter = value


# ------------------------------------------------------------------------------
class InvalidTestClass(recollection.Inference):

    def __init__(self):
        super(InvalidTestClass, self).__init__()
        self._letter = 1

    @ recollection.infer.store('letter')
    def set_letter(self, value):
        self._letter = value


# ------------------------------------------------------------------------------
class TestInference(unittest.TestCase):

    # --------------------------------------------------------------------------
    def test_can_instance_an_inference_class(self):
        """
        Simply checks that an inference class can be instanced

        :return:
        """
        SimpleTestClass()

    # --------------------------------------------------------------------------
    def test_properties_are_stored_automatically(self):
        """
        Ensures that property changes are automatically stored

        :return:
        """
        test_class = SimpleTestClass()

        test_class.number = 99
        test_class.number = 42

        test_class.memento.restore(1)

        self.assertEqual(
            99,
            test_class.number,
        )

    # --------------------------------------------------------------------------
    def test_setters_are_triggered(self):
        """
        Ensures storing is triggered when decorated with the infer.store

        :return:
        """
        test_class = SimpleTestClass()

        test_class.set_letter('z')
        test_class.set_letter('x')
        test_class.memento.restore(1)

        self.assertEqual(
            'z',
            test_class.letter(),
        )

    # --------------------------------------------------------------------------
    def test_register_only_double_decorators(self):
        """
        Ensures that if you have incorrectly decorated a class an exception
        will be triggered.

        :return:
        """
        test_class = InvalidTestClass()

        self.assertEqual(
            [],
            test_class.memento.labels(),
        )

    # --------------------------------------------------------------------------
    def test_defer_changes(self):
        """
        Ensures that we do not get state changes during a deferred step

        :return:
        """
        # -- Create a class and define a property
        test_class = SimpleTestClass()

        with test_class.memento.defer():
            for i in range(10):
                test_class.number = i

        self.assertEqual(
            1,
            len(test_class.memento._states)
        )

    # --------------------------------------------------------------------------
    def test_omit_changes(self):
        """
        Ensures that we do not get state changes during a deferred step

        :return:
        """
        # -- Create a class and define a property
        test_class = SimpleTestClass()

        with test_class.memento.omit():
            for i in range(10):
                test_class.number = i

        self.assertEqual(
            0,
            len(test_class.memento._states)
        )
