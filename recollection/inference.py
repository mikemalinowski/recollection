from .core import Memento
from .exceptions import StorageError


# ------------------------------------------------------------------------------
class Inference(object):
    """
    This class is specifically designed to allow you to inherit from
    it. In doing so the class will infer storage and serialisation behaviour
    for you through declared decorators.
    
    The other additional benefit of using this mechanism is that it can 
    monitor and store changes automatically whenever registered properties
    are changed.
    
    Due to inference testing during calls this approach is not as performant
    as creating a standard Memento object and explicitely calling the store
    methods where required. However, if performance is not the key concern 
    this class can make the code implementation significantly lighter and
    easier to manage.
    
    This example shows how to mark public attributes for automatic storage
    as well as defining setters and getters:
    
    ..code-block:: python
        
        >>> import recollection
        >>> 
        >>> class Foo(recollection.Inference):
        ... 
        ...     def __init__(self):
        ...         super(Foo, self).__init__()
        ... 
        ...         # -- Demonstrate a private attribute with getter
        ...         # -- and setter methods
        ...         self._letter = 1
        ... 
        ...         # -- Demonstrate public attributes which should be
        ...         # -- stored whenever they are changed
        ...         self.number = 10
        ... 
        ...         # -- Because we're inheriting from the Inference class, any
        ...         # -- registered properties will automatically trigger a
        ...         # -- state store whenever they are changed.
        ...         self.memento.register('number')
        ... 
        ...     # -- Declare that this is a memento getter
        ...     @recollection.infer.get('foobar')
        ...     def letter(self):
        ...         return self._letter
        ... 
        ...     # -- Declare this as a memento setter, using the same
        ...     # -- label as the getter. Whenever setHeight is called
        ...     # -- it will automatically store the state change.
        ...     @recollection.infer.store('foobar')
        ...     def setLetter(self, value):
        ...         self._letter = value
        >>> 
        >>> # -- Instance our object
        >>> foo = Foo()
        >>> 
        >>> # -- Update our variable using our accessor - which will automatically
        >>> # -- incur a state store
        >>> for letter in ['a', 'b', 'c', 'd', 'e']:
        ...     foo.setLetter(letter)
        >>> 
        >>> # -- Demonstrate that the current state is 'e'
        >>> print(foo.letter())  # -- Prints 'e'
        >>> 
        >>> # -- Roll back one setp and demonstrate that the property
        >>> # -- now evaluates to 'd'
        >>> foo.memento.restore(1)
        >>> print(foo.letter())  # -- Prints 'd'
        >>> 
        >>> # -- Here we demonstrate directly changing properties
        >>> # -- which are registered
        >>> foo.number = 5
        >>> foo.number = 99
        >>> print(foo.number == 99)
        >>> 
        >>> # -- Now restore back one step
        >>> foo.memento.restore(1)
        >>> print(foo.number == 5)
    """

    # ----------------------------------------------------------------------
    def __init__(self):

        # -- Define the memento object we will use for
        # -- state storage
        self.memento = Memento(self)

        self._initialise_decorator_registration()

    # --------------------------------------------------------------------------
    def __getattribute__(self, item):
        return object.__getattribute__(self, item)

    # --------------------------------------------------------------------------
    def __setattr__(self, name, value):
        """
        We re-implement the setattr to allow us to perform a check as to
        whether the name we're trying to set is registered in the list of
        watch items in the Memento object.
        
        :param name: 
        :param value: 
        :return: 
        """
        self.__dict__[name] = value

        try:
            if name in self.memento.labels():
                self.memento.store()

        except (AttributeError, StorageError):
            pass

    # --------------------------------------------------------------------------
    def _initialise_decorator_registration(self):
        """
        This will perform an intial registration based on the decorators
        wrapping any methods of this class.

        :return: 
        """
        # -- We need to
        found_getters = dict()
        found_setters = dict()

        # -- Cycle over all the elements making up the class
        # -- and inspect them for decorators
        for item in dir(self):

            # -- Get the item as its object
            item = getattr(
                self,
                item,
            )

            # -- Ask for forgiveness rather than permission - if the attributes
            # -- dont exist we just skip over to the next time.
            try:
                if item.is_memento_getter:
                    found_getters[item.label] = item

                elif item.is_memento_setter:
                    found_setters[item.label] = item

            except AttributeError:
                pass

        # -- For each found label, register it in the memento
        # -- object unless it is already registered
        for label in found_getters:

            # -- We only allow matching getters and setters
            if label not in found_setters:
                continue

            # -- If this is already registered then we do not
            # - need to register it again
            if label in self.memento.labels():
                continue

            # -- Do the final registration
            self.memento.register(
                label=label,
                getter=found_getters[label],
                setter=found_setters[label],
                copy_value=False
            )
