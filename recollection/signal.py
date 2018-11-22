import weakref
import inspect

try:
    from weakref import WeakMethod

except ImportError:
    from .compat import WeakMethod


# ------------------------------------------------------------------------------
class Signal(object):

    # --------------------------------------------------------------------------
    def __init__(self):
        self._slots = list()

    # --------------------------------------------------------------------------
    def connect(self, slot):
        """
        Connects the given callable to the signal such that when the signal
        is emitted, any connecting slots will be called.

        Each connected slot will be called with any arguments that are passed
        through on the emit.

        :param slot: callable
        :return: True on successful connection
        """
        if not callable(slot):
            return False

        # -- Store the slot as a weak reference to ensure
        # -- this class does not go out of scope
        if inspect.ismethod(slot):
            self._slots.append(WeakMethod(slot))
        else:
            self._slots.append(weakref.ref(slot))

    # --------------------------------------------------------------------------
    def disconnect(self, slot):
        """
        Removes the given slot from the slot list meaning it will never be
        called when the signal is emitted.

        :param slot: callable to remove

        :return: True on successful removal
        """
        callables_to_remove = [
            possibility
            for possibility in self._slots
            if possibility() and possibility() == slot
        ]

        if not callables_to_remove:
            return False

        while callables_to_remove:
            self._slots.remove(callables_to_remove.pop())

        return True

    # --------------------------------------------------------------------------
    def emit(self, *args, **kwargs):
        """
        Triggers a call of all the connected slots passing through any
        arguments you give down to each slot.

        :param args: Args to be passed to each slot
        :param kwargs: Kwargs to be passed to each slot

        :return: None
        """
        for slot in self._slots:
            if slot():
                slot()(
                    *args,
                    **kwargs
                )
